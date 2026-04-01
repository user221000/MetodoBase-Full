"""Rutas de pago — integración Stripe y MercadoPago.

Las claves de API se leen de variables de entorno:
  STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
  MERCADOPAGO_ACCESS_TOKEN

Ambos proveedores siguen el mismo flujo:
  1. Frontend solicita sesión/preferencia (requiere autenticación).
  2. Backend crea la sesión con redirect URLs.
  3. El webhook confirma el pago y activa la licencia.

Seguridad: Todos los endpoints de creación de sesión requieren
autenticación para asociar el pago al gym correcto.
"""
import logging
import os
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field

from config.constantes import PLANES_LICENCIA, ERR_PAGOS_NO_CONFIGURADOS
from config.settings import get_settings
from web.auth_deps import get_usuario_gym
from web.services.resilience import retry_with_backoff, mercadopago_circuit, stripe_circuit
from web.services.subscription_service import activate_subscription, complete_checkout, is_payment_processed

logger = logging.getLogger(__name__)


def _get_mp_sdk():
    """Obtiene SDK de MercadoPago con timeout configurado."""
    import mercadopago
    access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
    sdk = mercadopago.SDK(access_token)

    # Configurar timeouts (MercadoPago SDK usa requests)
    settings = get_settings()
    sdk.request_options.request_timeout = settings.MERCADOPAGO_TIMEOUT
    sdk.request_options.connection_timeout = settings.HTTP_CONNECT_TIMEOUT

    return sdk

router = APIRouter(tags=["Pagos"])

# ── Schemas ───────────────────────────────────────────────────────────────────

_PLANES_VALIDOS = set(PLANES_LICENCIA.keys())


class CrearSesionRequest(BaseModel):
    plan: str = Field(..., description="standard | gym_comercial | clinica")
    email: str = Field(..., min_length=5, max_length=120)
    success_url: str = Field("/checkout/success", max_length=500)
    cancel_url: str = Field("/checkout/cancel", max_length=500)


class SesionResponse(BaseModel):
    session_id: str
    redirect_url: str


# ── Almacén de sesiones persistente en DB ─────────────────────────────────────
# Las sesiones de checkout se persisten en CheckoutSession (web.database.models)
# para sobrevivir reinicios de pods.


# ── Stripe endpoints ─────────────────────────────────────────────────────────

@retry_with_backoff(max_retries=3, circuit=stripe_circuit)
def _stripe_create_session(stripe_key: str, **kwargs) -> dict:
    """Crea sesión de Stripe Checkout (protegida con retry + circuit breaker)."""
    import stripe
    
    settings = get_settings()
    stripe.api_key = stripe_key
    stripe.max_network_retries = 0  # Usamos nuestro circuit breaker
    stripe.default_http_client = stripe.http_client.RequestsClient(
        timeout=settings.STRIPE_TIMEOUT
    )
    
    session = stripe.checkout.Session.create(**kwargs)
    return {"id": session.id, "url": session.url}


@router.post("/pagos/stripe/session", response_model=SesionResponse)
async def crear_sesion_stripe(
    req: CrearSesionRequest,
    usuario: dict = Depends(get_usuario_gym),
):
    """
    Crea una sesión de Stripe Checkout.
    
    Requiere autenticación para asociar el pago al gym del usuario.
    """
    from web.database.engine import get_engine
    from web.database.models import CheckoutSession
    from sqlalchemy.orm import Session as SQLASession
    
    gym_id = usuario["id"]
    settings = get_settings()
    
    if req.plan not in _PLANES_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Plan inválido: {req.plan}")

    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail=ERR_PAGOS_NO_CONFIGURADOS)

    info = PLANES_LICENCIA[req.plan]
    stripe_key = settings.STRIPE_SECRET_KEY

    try:
        if info.get("stripe_price_id"):
            line_items = [{"price": info["stripe_price_id"], "quantity": 1}]
        else:
            line_items = [{
                "price_data": {
                    "currency": "mxn",
                    "unit_amount": int(info["precio_mxn"] * 100),
                    "recurring": {"interval": "month"},
                    "product_data": {
                        "name": f"Método Base — {req.plan.title()}",
                        "description": f"Hasta {info['max_clientes']} clientes",
                    },
                },
                "quantity": 1,
            }]

        session = _stripe_create_session(
            stripe_key,
            payment_method_types=["card"],
            mode="subscription",
            customer_email=req.email,
            line_items=line_items,
            success_url=req.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=req.cancel_url,
            metadata={"plan": req.plan},
        )

        # Persist to DB instead of in-memory dict
        engine = get_engine()
        with SQLASession(engine) as db:
            checkout = CheckoutSession(
                id=secrets.token_urlsafe(32),
                gym_id=gym_id,
                stripe_session_id=session["id"],
                plan=req.plan,
                email=req.email,
                status="pending",
            )
            db.add(checkout)
            db.commit()

        return SesionResponse(session_id=session["id"], redirect_url=session["url"])

    except ImportError:
        raise HTTPException(status_code=503, detail="Módulo stripe no instalado.")
    except Exception as e:
        logger.error("Stripe error: %s", e, exc_info=get_settings().DEBUG)
        raise HTTPException(status_code=502, detail="Error al crear sesión de pago.")


@router.post("/pagos/stripe/webhook", include_in_schema=False)
async def stripe_webhook(request: Request):
    """
    Recibe webhooks de Stripe para confirmar pagos.
    
    Delega a stripe_service.handle_webhook_event para:
    - Verificación de firma
    - Idempotencia (evita procesar eventos duplicados)
    - Handlers completos de todos los eventos
    """
    from sqlalchemy.orm import Session as SQLASession
    from web.database.engine import get_engine
    from web.services.stripe_service import verify_webhook, handle_webhook_event
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    
    # Verificar firma y construir evento
    event = verify_webhook(payload, sig_header)
    if not event:
        raise HTTPException(status_code=400, detail="Firma de webhook inválida.")
    
    # Procesar con idempotencia
    engine = get_engine()
    with SQLASession(engine) as db:
        result = handle_webhook_event(db, event)
        db.commit()
        logger.info("Webhook procesado: event_type=%s, result=%s", event["type"], result)
    
    return {"status": "ok", "result": result}


# ── MercadoPago endpoints ────────────────────────────────────────────────────

@retry_with_backoff(max_retries=2, circuit=mercadopago_circuit)
def _mp_create_preference(sdk, preference_data: dict) -> dict:
    """Crea preferencia de pago en MercadoPago (protegida con retry + circuit breaker)."""
    return sdk.preference().create(preference_data)


@router.post("/pagos/mp/preference", response_model=SesionResponse)
async def crear_preferencia_mp(
    req: CrearSesionRequest,
    usuario: dict = Depends(get_usuario_gym),
):
    """
    Crea una preferencia de pago en MercadoPago.
    
    Requiere autenticación para asociar el pago al gym del usuario.
    """
    gym_id = usuario["id"]
    
    if req.plan not in _PLANES_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Plan inválido: {req.plan}")

    info = PLANES_LICENCIA[req.plan]
    mp_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    if not mp_token:
        raise HTTPException(status_code=503, detail=ERR_PAGOS_NO_CONFIGURADOS)

    try:
        sdk = _get_mp_sdk()

        preference = _mp_create_preference(sdk, {
            "items": [{
                "title": f"Método Base — {req.plan.title()}",
                "quantity": 1,
                "unit_price": info["precio_mxn"],
                "currency_id": "MXN",
            }],
            "payer": {"email": req.email},
            "back_urls": {
                "success": req.success_url,
                "failure": req.cancel_url,
                "pending": req.cancel_url,
            },
            "auto_return": "approved",
            "metadata": {
                "plan": req.plan,
                "gym_id": gym_id,
            },
        })

        resp = preference["response"]
        pref_id = resp["id"]

        # Persist to DB
        from web.database.engine import get_engine
        from web.database.models import CheckoutSession
        from sqlalchemy.orm import Session as SQLASession
        
        engine = get_engine()
        with SQLASession(engine) as db:
            checkout = CheckoutSession(
                id=secrets.token_urlsafe(32),
                gym_id=gym_id,
                stripe_session_id=pref_id,  # MP preference ID
                plan=req.plan,
                email=req.email,
                status="pending",
            )
            db.add(checkout)
            db.commit()

        return SesionResponse(
            session_id=pref_id,
            redirect_url=resp["init_point"],
        )

    except ImportError:
        raise HTTPException(status_code=503, detail="Módulo mercadopago no instalado.")
    except Exception as e:
        logger.error("MercadoPago error: %s", e, exc_info=get_settings().DEBUG)
        raise HTTPException(status_code=502, detail="Error al crear preferencia de pago.")


@router.post("/pagos/mp/webhook", include_in_schema=False)
async def mp_webhook(request: Request):
    """Recibe notificaciones IPN de MercadoPago y activa licencia."""
    # Verify webhook signature — REQUIRED in production
    settings = get_settings()
    raw_body = await request.body()
    if not settings.MERCADOPAGO_WEBHOOK_SECRET:
        logger.error("MP webhook received but MERCADOPAGO_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=503, detail="Webhook signature verification not configured")
    
    import hmac, hashlib
    sig_header = request.headers.get("x-signature", "")
    # MercadoPago x-signature format: "ts=<ts>,v1=<hash>"
    parts = dict(p.split("=", 1) for p in sig_header.split(",") if "=" in p)
    ts = parts.get("ts", "")
    v1 = parts.get("v1", "")
    # Build signed payload: "id:<data.id>;request-id:<x-request-id>;ts:<ts>;"
    request_id = request.headers.get("x-request-id", "")
    try:
        body_json = __import__("json").loads(raw_body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    data_id = str(body_json.get("data", {}).get("id", ""))
    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    expected = hmac.new(
        settings.MERCADOPAGO_WEBHOOK_SECRET.encode(),
        manifest.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not ts or not v1 or not hmac.compare_digest(expected, v1):
        logger.warning("MP webhook signature mismatch or missing")
        raise HTTPException(status_code=401, detail="Invalid signature")

    body = body_json
    topic = body.get("type", "")

    if topic != "payment":
        return {"status": "ignored"}

    payment_id = body.get("data", {}).get("id")
    if not payment_id:
        logger.warning("MP webhook sin payment_id")
        return {"status": "no_payment_id"}

    logger.info("MercadoPago notificación payment_id=%s", payment_id)

    try:
        sdk = _get_mp_sdk()
        payment_response = sdk.payment().get(payment_id)

        if payment_response["status"] != 200:
            logger.error("MP: No se pudo obtener pago %s: status=%s",
                         payment_id, payment_response["status"])
            return {"status": "error"}

        payment_data = payment_response["response"]
        status = payment_data.get("status")

        if status != "approved":
            logger.info("MP pago %s no aprobado: status=%s", payment_id, status)
            return {"status": "not_approved"}

        # Extraer metadata del pago
        metadata = payment_data.get("metadata", {})
        plan = metadata.get("plan", "standard")
        gym_id = metadata.get("gym_id", "")
        email = payment_data.get("payer", {}).get("email", "")

        if not gym_id:
            logger.error("MP pago %s aprobado pero sin gym_id en metadata", payment_id)
            return {"status": "missing_gym_id"}

        # Idempotency: skip if already processed
        from web.database.engine import get_engine
        from sqlalchemy.orm import Session as SQLASession

        engine = get_engine()
        with SQLASession(engine) as db:
            if is_payment_processed(db, str(payment_id)):
                logger.info("MP pago %s ya procesado (idempotente)", payment_id)
                return {"status": "already_processed"}

            complete_checkout(db, gym_id, plan, email, str(payment_id))
            activate_subscription(db, gym_id, plan, provider="mercadopago")
            db.commit()

        logger.info("MP pago activado: payment_id=%s, plan=%s, gym=%s",
                    payment_id, plan, gym_id)
        return {"status": "activated"}

    except ImportError:
        logger.error("SDK de MercadoPago no instalado")
        return {"status": "sdk_missing"}
    except Exception as e:
        logger.error("Error procesando webhook MP: %s", e)
        return {"status": "error"}
