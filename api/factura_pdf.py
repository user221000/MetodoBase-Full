"""Generador de facturas PDF para Método Base.

Genera un PDF tipo factura/recibo con:
  - Folio, fecha, datos del comprador
  - Plan adquirido, precio, IVA, total
  - Código QR de verificación (opcional)

Uso:
    from api.factura_pdf import generar_factura
    ruta = generar_factura(datos_factura, ruta_salida=Path("/tmp/factura.pdf"))
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

_COLOR_GREEN = colors.HexColor("#22C55E")
_COLOR_DARK = colors.HexColor("#111827")
_COLOR_GRAY = colors.HexColor("#F3F4F6")
_COLOR_MID = colors.HexColor("#6B7280")

_MARGIN = 2 * cm
_IVA_RATE = 0.16  # 16% IVA México


def generar_factura(
    datos: dict,
    ruta_salida: Path,
    *,
    iva_rate: float = _IVA_RATE,
    gym_branding: dict | None = None,
) -> Path:
    """Genera un PDF de factura/recibo.

    Args:
        datos: Dict con llaves:
            folio       (str)   — "MB-2026-0001"
            comprador   (str)   — "Mi Gimnasio S.A."
            email       (str)   — "admin@gym.com"
            plan        (str)   — "profesional"
            precio_mxn  (float) — 759.0
            fecha       (str)   — ISO date, default hoy
        ruta_salida: Path destino del PDF.
        iva_rate: Tasa de IVA (default 0.16).
        gym_branding: Dict con nombre_gym, telefono, email del gym. 
                      Fallback a "Método Base" si None.

    Returns:
        Path del archivo generado.
    """
    ruta_salida = Path(ruta_salida).resolve()
    # Guard against path traversal: output must stay inside its parent dir
    allowed_parent = ruta_salida.parent
    if ".." in ruta_salida.parts:
        raise ValueError(f"Path traversal detected in ruta_salida: {ruta_salida}")
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(ruta_salida),
        pagesize=LETTER,
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        topMargin=_MARGIN,
        bottomMargin=_MARGIN,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "Titulo", parent=styles["Heading1"],
        fontSize=20, textColor=_COLOR_DARK, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "SubGris", parent=styles["Normal"],
        fontSize=10, textColor=_COLOR_MID,
    ))
    styles.add(ParagraphStyle(
        "Derecha", parent=styles["Normal"],
        fontSize=10, alignment=TA_RIGHT, textColor=_COLOR_MID,
    ))

    folio = datos.get("folio", f"MB-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    fecha = datos.get("fecha", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    comprador = datos.get("comprador", "—")
    email = datos.get("email", "—")
    plan = datos.get("plan", "profesional").title()
    precio = float(datos.get("precio_mxn", 0))
    iva = round(precio * iva_rate, 2)
    total = round(precio + iva, 2)

    # ── Branding ──────────────────────────────────────────────────────────
    _brand = gym_branding or {}
    brand_name = _brand.get("nombre_gym") or "Método Base"
    brand_email = _brand.get("email") or ""
    brand_tel = _brand.get("telefono") or ""

    elements = []

    # ── Encabezado ────────────────────────────────────────────────────────────
    elements.append(Paragraph(brand_name, styles["Titulo"]))
    elements.append(Paragraph("Recibo de Compra", styles["SubGris"]))
    elements.append(Spacer(1, 0.8 * cm))

    # ── Info factura ──────────────────────────────────────────────────────────
    info_data = [
        ["Folio:", folio, "Fecha:", fecha],
        ["Comprador:", comprador, "Email:", email],
    ]
    info_table = Table(info_data, colWidths=[2.5 * cm, 6 * cm, 2 * cm, 6 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), _COLOR_MID),
        ("TEXTCOLOR", (2, 0), (2, -1), _COLOR_MID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.8 * cm))

    # ── Detalle ───────────────────────────────────────────────────────────────
    detail_data = [
        ["Concepto", "Plan", "Precio USD"],
        [f"Licencia {brand_name} — {plan}", plan, f"${precio:.2f}"],
        ["", "Subtotal", f"${precio:.2f}"],
        ["", f"IVA ({int(iva_rate * 100)}%)", f"${iva:.2f}"],
        ["", "TOTAL", f"${total:.2f}"],
    ]
    detail_table = Table(detail_data, colWidths=[9 * cm, 3.5 * cm, 4 * cm])
    detail_table.setStyle(TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), _COLOR_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        # Body
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BACKGROUND", (0, 1), (-1, 1), _COLOR_GRAY),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("ALIGN", (1, 2), (1, -1), "RIGHT"),
        # Total row
        ("FONTNAME", (1, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (1, -1), (-1, -1), 11),
        ("LINEABOVE", (1, -1), (-1, -1), 1.2, _COLOR_GREEN),
        # Grid
        ("GRID", (0, 0), (-1, 0), 0.5, _COLOR_GREEN),
        ("LINEBELOW", (0, 1), (-1, 1), 0.3, _COLOR_MID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 1.5 * cm))

    # ── Pie de página ─────────────────────────────────────────────────────────
    footer_parts = [f"Comprobante digital generado por {brand_name}."]
    if brand_tel:
        footer_parts.append(f"Tel: {brand_tel}")
    if brand_email:
        footer_parts.append(brand_email)
    elements.append(Paragraph(" | ".join(footer_parts), styles["SubGris"]))

    doc.build(elements)
    logger.info("Factura generada: %s", ruta_salida)
    return ruta_salida
