"""
tests/test_generacion_pdf.py — Tests de calidad para PDFs de MetodoBase.

Validan que:
  - Los PDFs se generan correctamente (archivo válido)
  - El contenido incluye datos clave del cliente y macros
  - El tiempo de generación es aceptable
  - El nuevo PDFGenerator (api/pdf_generator.py) produce output correcto
  - El generador funciona con y sin logo, con y sin % grasa

Run:
    pytest tests/test_generacion_pdf.py -v
"""
from __future__ import annotations

import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

# ── Datos de prueba compartidos ───────────────────────────────────────────────

DATOS_PLAN_COMPLETO = {
    "cliente": {
        "nombre": "Ana Prueba PDF",
        "edad": 28,
        "sexo": "F",
        "peso_kg": 65.0,
        "estatura_cm": 162.0,
        "grasa_corporal_pct": 22.5,
        "nivel_actividad": "moderada",
        "objetivo": "deficit",
    },
    "macros": {
        "tmb": 1405.2,
        "get_total": 2177.6,
        "kcal_objetivo": 1851.0,
        "proteina_g": 130.5,
        "carbs_g": 209.7,
        "grasa_g": 55.3,
    },
    "plan": {
        "desayuno": {
            "kcal_real": 370.0,
            "alimentos": {
                "avena": 60,
                "leche_descremada": 200,
                "manzana": 120,
            },
        },
        "almuerzo": {
            "kcal_real": 420.0,
            "alimentos": {
                "pechuga_de_pollo": 150,
                "arroz": 80,
                "brocoli": 150,
            },
        },
        "comida": {
            "kcal_real": 680.0,
            "alimentos": {
                "carne_magra_res": 180,
                "frijoles": 100,
                "tortilla_maiz": 60,
                "espinaca": 100,
            },
        },
        "cena": {
            "kcal_real": 381.0,
            "alimentos": {
                "salmon": 130,
                "papa": 150,
                "ejotes": 100,
            },
        },
    },
    "fecha_generacion": datetime(2026, 3, 16, 10, 0, 0),
}


# ── Fixture para directorio temporal ─────────────────────────────────────────

@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


# ════════════════════════════════════════════════════════════════════════════════
# 1. PDFGenerator (api/pdf_generator.py) — Nuevo generador Platypus
# ════════════════════════════════════════════════════════════════════════════════

class TestPDFGenerator:
    """Tests del nuevo PDFGenerator con layout Platypus."""

    def test_pdf_genera_archivo(self, tmp_dir):
        """El archivo se crea y tiene tamaño mínimo."""
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator()
        ruta = gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "test.pdf")
        assert ruta.exists(), "El PDF no se creó"
        assert ruta.stat().st_size > 5_000, "PDF demasiado pequeño"

    def test_pdf_es_valido(self, tmp_dir):
        """pypdf puede leerlo sin errores."""
        import pypdf
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator()
        ruta = gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "valid.pdf")
        reader = pypdf.PdfReader(str(ruta))
        assert len(reader.pages) >= 1

    def test_pdf_contiene_nombre_cliente(self, tmp_dir):
        """El texto del PDF incluye el nombre del cliente."""
        import pypdf
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator()
        ruta = gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "nombre.pdf")
        texto = _extraer_texto(ruta)
        assert "Ana Prueba PDF" in texto or "Ana" in texto

    def test_pdf_contiene_macros(self, tmp_dir):
        """El PDF incluye valores de TMB, GET o kcal objetivo."""
        import pypdf
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator()
        ruta = gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "macros.pdf")
        texto = _extraer_texto(ruta)
        # Al menos uno de los valores clave debe aparecer en el texto
        valores_clave = ["1405", "2177", "1851", "130"]  # TMB, GET, kcal_obj, proteina
        assert any(v in texto for v in valores_clave), (
            f"Ningún valor de macros encontrado en el PDF. Texto: {texto[:300]}"
        )

    def test_pdf_contiene_comidas(self, tmp_dir):
        """El PDF incluye nombres de al menos dos tiempos de comida."""
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator()
        ruta = gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "comidas.pdf")
        texto = _extraer_texto(ruta).lower()
        comidas_esperadas = ["desayuno", "cena"]
        for comida in comidas_esperadas:
            assert comida in texto, f"Tiempo de comida '{comida}' no encontrado en PDF"

    def test_pdf_tiempo_generacion(self, tmp_dir):
        """El PDF se genera en menos de 5 segundos."""
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator()
        t0 = time.perf_counter()
        gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "perf.pdf")
        elapsed = time.perf_counter() - t0
        assert elapsed < 5.0, f"PDF tardó {elapsed:.2f}s (límite: 5s)"

    def test_pdf_con_config_personalizada(self, tmp_dir):
        """PDFGenerator acepta config de branding personalizada."""
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator(config={
            "gym_nombre": "GDL Fitness Club",
            "color_primario": "#00C853",
            "color_secundario": "#1A237E",
        })
        ruta = gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "custom.pdf")
        assert ruta.exists()
        texto = _extraer_texto(ruta)
        assert "GDL Fitness Club" in texto

    def test_pdf_sin_logo(self, tmp_dir):
        """PDFGenerator funciona sin logo (gym_logo=None)."""
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator(config={"gym_logo": None})
        ruta = gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "sinlogo.pdf")
        assert ruta.exists()

    def test_pdf_sin_grasa_corporal(self, tmp_dir):
        """Plan con grasa_corporal_pct=None no provoca crash."""
        from api.pdf_generator import PDFGenerator
        import copy
        datos = copy.deepcopy(DATOS_PLAN_COMPLETO)
        datos["cliente"]["grasa_corporal_pct"] = None
        gen = PDFGenerator()
        ruta = gen.generar_plan(datos, tmp_dir / "singrasa.pdf")
        assert ruta.exists()

    def test_pdf_metadata_fecha(self, tmp_dir):
        """La fecha de generación aparece en el PDF."""
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator()
        ruta = gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "fecha.pdf")
        texto = _extraer_texto(ruta)
        assert "16/03/2026" in texto or "2026" in texto


# ════════════════════════════════════════════════════════════════════════════════
# 2. Generador legacy (core/exportador_salida.py) — Smoke test de compatibilidad
# ════════════════════════════════════════════════════════════════════════════════

class TestGeneradorLegacy:
    """Valida que el generador existente sigue funcionando sin regresiones."""

    def _construir_cliente(self):
        from core.modelos import ClienteEvaluacion
        from api.dependencies import build_cliente_from_dict
        return build_cliente_from_dict({
            "nombre": "Legacy Test",
            "edad": 30,
            "peso_kg": 80.0,
            "estatura_cm": 175.0,
            "grasa_corporal_pct": 18.0,
            "nivel_actividad": "moderada",
            "objetivo": "mantenimiento",
        })

    def test_legacy_genera_pdf(self, tmp_dir):
        """GeneradorPDFProfesional produce un archivo válido."""
        import pypdf
        from core.exportador_salida import GeneradorPDFProfesional
        from core.generador_planes import ConstructorPlanNuevo
        import os
        from config.constantes import CARPETA_PLANES

        cliente = self._construir_cliente()
        os.makedirs(CARPETA_PLANES, exist_ok=True)
        plan = ConstructorPlanNuevo.construir(cliente, plan_numero=1, directorio_planes=CARPETA_PLANES)

        ruta = str(tmp_dir / "legacy.pdf")
        gen = GeneradorPDFProfesional(ruta)
        result = gen.generar(cliente, plan)

        pdf_path = Path(result)
        assert pdf_path.exists(), f"PDF legacy no encontrado en {pdf_path}"
        reader = pypdf.PdfReader(str(pdf_path))
        assert len(reader.pages) >= 1

    def test_legacy_tiempo_generacion(self, tmp_dir):
        """El generador legacy no debe tardar más de 15 segundos."""
        from core.exportador_salida import GeneradorPDFProfesional
        from core.generador_planes import ConstructorPlanNuevo
        import os
        from config.constantes import CARPETA_PLANES

        cliente = self._construir_cliente()
        os.makedirs(CARPETA_PLANES, exist_ok=True)
        ruta = str(tmp_dir / "legacy_perf.pdf")

        t0 = time.perf_counter()
        plan = ConstructorPlanNuevo.construir(cliente, plan_numero=2, directorio_planes=CARPETA_PLANES)
        gen = GeneradorPDFProfesional(ruta)
        gen.generar(cliente, plan)
        elapsed = time.perf_counter() - t0

        assert elapsed < 15.0, f"Generador legacy tardó {elapsed:.2f}s (límite: 15s)"
        print(f"\n  Tiempo generación legacy: {elapsed:.2f}s")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extraer_texto(ruta_pdf: Path) -> str:
    """Extrae texto de todas las páginas de un PDF con pypdf."""
    import pypdf
    reader = pypdf.PdfReader(str(ruta_pdf))
    return " ".join(page.extract_text() or "" for page in reader.pages)


# ════════════════════════════════════════════════════════════════════════════════
# 3. Ramas no cubiertas — logo real, gym contacto, macros/plan vacíos
# ════════════════════════════════════════════════════════════════════════════════

class TestPDFGeneratorRamasAdicionales:
    """
    Cubre las ramas de código aún no alcanzadas en api/pdf_generator.py:
      - Header con logo real (imagen PNG válida)
      - Header sin logo pero con gym_dir y gym_telefono
      - _build_macro_summary con macros vacío (guard clause)
      - _build_meal_plan con plan vacío (guard clause)
    """

    def _crear_logo_png(self, directorio: Path) -> Path:
        """Genera una imagen PNG de prueba de 100x50 píxeles."""
        logo = directorio / "logo_test.png"
        try:
            from PIL import Image as PILImage
            img = PILImage.new("RGB", (100, 50), color=(255, 107, 53))
            img.save(str(logo))
        except ImportError:
            # Fallback si Pillow no está disponible: crear PNG mínimo válido
            import struct, zlib

            def _chunk(name: bytes, data: bytes) -> bytes:
                c = zlib.crc32(name + data) & 0xFFFFFFFF
                return struct.pack(">I", len(data)) + name + data + struct.pack(">I", c)

            w, h = 10, 10
            raw = b"\x00" + b"\xFF\x60\x20" * w  # filtro 0, rojo-anaranjado
            compressed = zlib.compress(raw * h)
            ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
            png = (
                b"\x89PNG\r\n\x1a\n"
                + _chunk(b"IHDR", ihdr)
                + _chunk(b"IDAT", compressed)
                + _chunk(b"IEND", b"")
            )
            logo.write_bytes(png)
        return logo

    def test_pdf_con_logo_real(self, tmp_dir):
        """El header con logo real se genera sin errores."""
        logo_path = self._crear_logo_png(tmp_dir)
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator(config={
            "gym_logo": str(logo_path),
            "gym_nombre": "Gym Con Logo Test",
        })
        ruta = gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "logo_real.pdf")
        assert ruta.exists()
        assert ruta.stat().st_size > 5_000

    def test_pdf_con_logo_y_contacto(self, tmp_dir):
        """Header con logo + dirección + teléfono (sub-texto bajo el logo)."""
        logo_path = self._crear_logo_png(tmp_dir)
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator(config={
            "gym_logo": str(logo_path),
            "gym_nombre": "Gym Logo Contacto",
            "gym_telefono": "33-1234-5678",
            "gym_direccion": "Av. Patria 123, Zapopan",
        })
        ruta = gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "logo_contacto.pdf")
        assert ruta.exists()
        texto = _extraer_texto(ruta)
        assert "Gym Logo Contacto" in texto

    def test_pdf_sin_logo_con_contacto(self, tmp_dir):
        """Header sin logo pero con gym_dir y gym_telefono (sub-texto alternativo)."""
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator(config={
            "gym_logo": None,
            "gym_nombre": "Gym Sin Logo",
            "gym_telefono": "33-9876-5432",
            "gym_direccion": "Calle Falsa 123",
        })
        ruta = gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "sinlogo_contacto.pdf")
        assert ruta.exists()
        texto = _extraer_texto(ruta)
        assert "Gym Sin Logo" in texto

    def test_pdf_macros_vacios_no_crash(self, tmp_dir):
        """_build_macro_summary devuelve [] si macros está vacío."""
        import copy
        from api.pdf_generator import PDFGenerator
        datos = copy.deepcopy(DATOS_PLAN_COMPLETO)
        datos["macros"] = {}  # dispara la guard clause
        gen = PDFGenerator()
        ruta = gen.generar_plan(datos, tmp_dir / "macros_vacios.pdf")
        assert ruta.exists()

    def test_pdf_plan_vacio_no_crash(self, tmp_dir):
        """_build_meal_plan devuelve [] si plan está vacío."""
        import copy
        from api.pdf_generator import PDFGenerator
        datos = copy.deepcopy(DATOS_PLAN_COMPLETO)
        datos["plan"] = {}  # dispara la guard clause
        gen = PDFGenerator()
        ruta = gen.generar_plan(datos, tmp_dir / "plan_vacio.pdf")
        assert ruta.exists()

    def test_pdf_logo_ruta_invalida_usa_fallback(self, tmp_dir):
        """Si gym_logo apunta a un archivo inexistente, usa header sin logo."""
        from api.pdf_generator import PDFGenerator
        gen = PDFGenerator(config={
            "gym_logo": "/ruta/que/no/existe/logo.png",
            "gym_nombre": "Gym Fallback Logo",
        })
        ruta = gen.generar_plan(DATOS_PLAN_COMPLETO, tmp_dir / "logo_fallback.pdf")
        assert ruta.exists()
        texto = _extraer_texto(ruta)
        assert "Gym Fallback Logo" in texto
