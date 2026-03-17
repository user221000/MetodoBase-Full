"""
api/pdf_generator.py — Generador de PDFs profesionales con ReportLab Platypus.

Diferencias vs GeneradorPDFProfesional (core/exportador_salida.py):
  - Usa el motor de flujo *Platypus* (SimpleDocTemplate + Flowables)
    en lugar de canvas de bajo nivel.
  - Layout configurable por dict `config` — cada gym puede personalizar
    nombre, logo, colores y datos de contacto sin tocar el código.
  - Acepta `datos_plan` como dict puro (no depende de ClienteEvaluacion),
    lo que facilita el testing aislado.

Uso desde routes/services:
    from api.pdf_generator import PDFGenerator
    gen = PDFGenerator(config={"gym_nombre": "Fit Club GDL", ...})
    ruta = gen.generar_plan(datos_plan, ruta_salida=Path("/tmp/plan.pdf"))
"""
from __future__ import annotations

import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# ── Paleta de colores predeterminada ──────────────────────────────────────────
_COLOR_ORANGE = colors.HexColor("#FF6B35")
_COLOR_NAVY   = colors.HexColor("#004E89")
_COLOR_GRAY   = colors.HexColor("#F3F4F6")
_COLOR_DARK   = colors.HexColor("#111827")
_COLOR_MID    = colors.HexColor("#6B7280")
_COLOR_WHITE  = colors.white

_PAGE_W, _PAGE_H = LETTER
_MARGIN = 1.5 * cm


class PDFGenerator:
    """
    Generador de PDFs con branding personalizado por gimnasio.

    Args:
        config: Dict opcional con llaves:
            gym_nombre     (str)   — "Mi Gym"
            gym_logo       (Path)  — Ruta al archivo de logo (.png/.jpg)
            gym_telefono   (str)   — "33 1234 5678"
            gym_direccion  (str)   — "Calle Falsa 123"
            color_primario (str)   — Hex "#FF6B35"
            color_secundario(str)  — Hex "#004E89"
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = {**self._default_config(), **(config or {})}
        _c1 = self.config.get("color_primario", "#FF6B35")
        _c2 = self.config.get("color_secundario", "#004E89")
        self.C_PRIMARY   = colors.HexColor(_c1)
        self.C_SECONDARY = colors.HexColor(_c2)
        self.styles = getSampleStyleSheet()
        self._build_styles()

    # ── Public API ─────────────────────────────────────────────────────────────

    def generar_plan(self, datos_plan: dict, ruta_salida: Path) -> Path:
        """
        Genera un PDF del plan nutricional en `ruta_salida`.

        Args:
            datos_plan: {
                'cliente': {nombre, edad, sexo, peso_kg, estatura_cm,
                            grasa_corporal_pct, nivel_actividad, objetivo},
                'macros':  {tmb, get_total, kcal_objetivo, proteina_g,
                            carbs_g, grasa_g},
                'plan': {
                    'desayuno': {'kcal_real': float, 'alimentos': {str: float}},
                    'almuerzo': ..., 'comida': ..., 'cena': ...
                },
                'fecha_generacion': datetime   (opcional)
            }
            ruta_salida: Path donde se escribirá el PDF.

        Returns:
            Path confirmada del PDF generado.

        Raises:
            Exception propagada si ReportLab falla.
        """
        ruta_salida = Path(ruta_salida)
        ruta_salida.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(ruta_salida),
            pagesize=LETTER,
            leftMargin=_MARGIN,
            rightMargin=_MARGIN,
            topMargin=_MARGIN,
            bottomMargin=2 * cm,
        )

        story = []
        story += self._build_header(datos_plan)
        story.append(Spacer(1, 0.4 * cm))
        story += self._build_client_card(datos_plan.get("cliente", {}))
        story.append(Spacer(1, 0.4 * cm))
        story += self._build_macro_summary(datos_plan.get("macros", {}))
        story.append(Spacer(1, 0.5 * cm))
        story += self._build_meal_plan(datos_plan.get("plan", {}))
        story.append(Spacer(1, 0.4 * cm))
        story += self._build_recommendations()
        story.append(Spacer(1, 0.4 * cm))
        story += self._build_footer_flowable()

        doc.build(story, onFirstPage=self._draw_page_border,
                  onLaterPages=self._draw_page_border)
        logger.info("PDF generado: %s", ruta_salida)
        return ruta_salida

    # ── Sección: Header ────────────────────────────────────────────────────────

    def _build_header(self, datos_plan: dict) -> list:
        flowables = []
        gym_nombre   = self.config["gym_nombre"]
        gym_telefono = self.config.get("gym_telefono", "")
        gym_dir      = self.config.get("gym_direccion", "")
        fecha = datos_plan.get("fecha_generacion") or datetime.now()
        if isinstance(fecha, str):
            fecha_str = fecha[:10]
        else:
            fecha_str = fecha.strftime("%d/%m/%Y")

        logo_path = self.config.get("gym_logo")
        usable_w = _PAGE_W - 2 * _MARGIN

        if logo_path and Path(logo_path).exists():
            # Header 2 columnas: logo izq, info gym der
            logo_img = Image(str(logo_path), width=3 * cm, height=1.6 * cm)
            logo_img.hAlign = "LEFT"
            gym_data = [
                [Paragraph(gym_nombre, self.styles["PDF_GymName"]),
                 Paragraph(f"Fecha: {fecha_str}", self.styles["PDF_SmallRight"])],
            ]
            if gym_dir or gym_telefono:
                sub = " | ".join(filter(None, [gym_dir, gym_telefono]))
                gym_data.append([
                    Paragraph(sub, self.styles["PDF_Sub"]),
                    Paragraph("", self.styles["PDF_Sub"]),
                ])
            header_tbl = Table(
                [[logo_img, Table(gym_data)]],
                colWidths=[3.5 * cm, usable_w - 3.5 * cm],
            )
            header_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))
            flowables.append(header_tbl)
        else:
            # Header sin logo: dos columnas de texto
            header_tbl = Table(
                [[Paragraph(gym_nombre, self.styles["PDF_GymName"]),
                  Paragraph(f"Fecha: {fecha_str}", self.styles["PDF_SmallRight"])]],
                colWidths=[usable_w * 0.65, usable_w * 0.35],
            )
            header_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))
            flowables.append(header_tbl)
            if gym_dir or gym_telefono:
                sub = " · ".join(filter(None, [gym_dir, gym_telefono]))
                flowables.append(Paragraph(sub, self.styles["PDF_Sub"]))

        flowables.append(Spacer(1, 0.2 * cm))
        flowables.append(HRFlowable(width="100%", thickness=2, color=self.C_PRIMARY))
        flowables.append(Spacer(1, 0.15 * cm))
        flowables.append(
            Paragraph("Plan Nutricional Personalizado", self.styles["PDF_Title"])
        )
        return flowables

    # ── Sección: Tarjeta cliente ───────────────────────────────────────────────

    def _build_client_card(self, cliente: dict) -> list:
        nombre    = cliente.get("nombre", "—")
        edad      = f"{cliente.get('edad', '—')} años"
        sexo_raw  = cliente.get("sexo") or ""
        sexo      = {"M": "Masculino", "F": "Femenino"}.get(sexo_raw.upper(), sexo_raw or "—")
        peso      = f"{cliente.get('peso_kg', '—')} kg"
        estatura  = f"{cliente.get('estatura_cm', '—')} cm"
        grasa     = cliente.get("grasa_corporal_pct")
        grasa_str = f"{grasa}%" if grasa else "No especificado"
        objetivo_map = {
            "deficit": "Déficit calórico (bajar grasa)",
            "mantenimiento": "Mantenimiento de peso",
            "superavit": "Superávit calórico (ganar masa)",
        }
        objetivo  = objetivo_map.get(str(cliente.get("objetivo", "")).lower(), str(cliente.get("objetivo", "—")))
        nivel_map = {
            "nula": "Sedentario",
            "leve": "Leve (1-3 días/sem)",
            "moderada": "Moderada (3-5 días/sem)",
            "intensa": "Intensa (6-7 días/sem)",
        }
        nivel     = nivel_map.get(str(cliente.get("nivel_actividad", "")).lower(), str(cliente.get("nivel_actividad", "—")))

        _s = self.styles
        data = [
            [Paragraph("Información del Cliente", _s["PDF_CardTitle"]), "", "", ""],
            [Paragraph(f"<b>Nombre:</b> {nombre}", _s["PDF_Cell"]),
             Paragraph(f"<b>Edad:</b> {edad}",     _s["PDF_Cell"]),
             Paragraph(f"<b>Sexo:</b> {sexo}",     _s["PDF_Cell"]),
             Paragraph(f"<b>Peso:</b> {peso}",     _s["PDF_Cell"])],
            [Paragraph(f"<b>Estatura:</b> {estatura}", _s["PDF_Cell"]),
             Paragraph(f"<b>% Grasa:</b> {grasa_str}", _s["PDF_Cell"]),
             Paragraph(f"<b>Objetivo:</b> {objetivo}", _s["PDF_Cell"]),
             Paragraph(f"<b>Actividad:</b> {nivel}",   _s["PDF_Cell"])],
        ]
        usable_w = _PAGE_W - 2 * _MARGIN
        col_w    = usable_w / 4

        tbl = Table(data, colWidths=[col_w] * 4)
        tbl.setStyle(TableStyle([
            # Header row spanning 4 cols
            ("SPAN",            (0, 0), (3, 0)),
            ("BACKGROUND",      (0, 0), (3, 0), self.C_SECONDARY),
            ("TEXTCOLOR",       (0, 0), (3, 0), _COLOR_WHITE),
            ("FONTNAME",        (0, 0), (3, 0), "Helvetica-Bold"),
            ("FONTSIZE",        (0, 0), (3, 0), 9),
            ("TOPPADDING",      (0, 0), (3, 0), 5),
            ("BOTTOMPADDING",   (0, 0), (3, 0), 5),
            # Data rows
            ("BACKGROUND",      (0, 1), (-1, -1), _COLOR_GRAY),
            ("ROWBACKGROUNDS",  (0, 1), (-1, -1), [_COLOR_GRAY, colors.white]),
            ("GRID",            (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("TOPPADDING",      (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING",   (0, 1), (-1, -1), 5),
            ("LEFTPADDING",     (0, 0), (-1, -1), 8),
        ]))
        return [tbl]

    # ── Sección: Resumen de macros ─────────────────────────────────────────────

    def _build_macro_summary(self, macros: dict) -> list:
        if not macros:
            return []

        tmb      = int(round(macros.get("tmb", 0)))
        get_tot  = int(round(macros.get("get_total", 0)))
        kcal_obj = int(round(macros.get("kcal_objetivo", 0)))
        prot     = round(macros.get("proteina_g", 0), 1)
        carb     = round(macros.get("carbs_g", 0), 1)
        fat      = round(macros.get("grasa_g", 0), 1)

        _s = self.styles

        def _macro_cell(valor, label, bg_hex):
            """Celda con valor grande y etiqueta pequeña."""
            bg = colors.HexColor(bg_hex)
            inner = Table(
                [[Paragraph(str(valor), _s["PDF_MacroNum"])],
                 [Paragraph(label,      _s["PDF_MacroLabel"])]],
                colWidths=[None],
            )
            inner.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), bg),
                ("TEXTCOLOR",     (0, 0), (-1, -1), _COLOR_WHITE),
                ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING",    (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("ROUNDEDCORNERS", [4]),
            ]))
            return inner

        usable_w = _PAGE_W - 2 * _MARGIN
        cw       = usable_w / 6

        cells = [
            _macro_cell(f"{tmb}", "TMB (kcal)",       "#6366F1"),
            _macro_cell(f"{get_tot}", "GET (kcal)",   "#0EA5E9"),
            _macro_cell(f"{kcal_obj}", "Objetivo",    "#FF6B35"),
            _macro_cell(f"{prot}g", "Proteína",       "#10B981"),
            _macro_cell(f"{carb}g", "Carbohidratos",  "#F59E0B"),
            _macro_cell(f"{fat}g", "Grasas",          "#EF4444"),
        ]
        tbl = Table([cells], colWidths=[cw] * 6)
        tbl.setStyle(TableStyle([
            ("LEFTPADDING",   (0, 0), (-1, -1), 3),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        return [
            Paragraph("Resumen Nutricional Diario", self.styles["PDF_SectionTitle"]),
            Spacer(1, 0.2 * cm),
            tbl,
        ]

    # ── Sección: Plan de comidas ───────────────────────────────────────────────

    def _build_meal_plan(self, plan: dict) -> list:
        if not plan:
            return []

        COMIDAS_ORDER = [
            ("desayuno",  "Desayuno"),
            ("almuerzo",  "Colación matutina / Almuerzo"),
            ("comida",    "Comida principal"),
            ("cena",      "Cena"),
        ]

        _s = self.styles
        flowables = [
            Paragraph("Plan de Alimentación", _s["PDF_SectionTitle"]),
            Spacer(1, 0.2 * cm),
        ]

        usable_w = _PAGE_W - 2 * _MARGIN
        cols     = [usable_w * 0.40, usable_w * 0.30, usable_w * 0.15, usable_w * 0.15]

        for key, label in COMIDAS_ORDER:
            if key not in plan:
                continue
            comida     = plan[key]
            alimentos  = comida.get("alimentos", {})
            kcal_real  = int(round(comida.get("kcal_real", 0)))

            # Header de esta comida
            header_row = [
                Paragraph(label, _s["PDF_MealHeader"]),
                Paragraph("Porción (g)", _s["PDF_MealHeaderC"]),
                Paragraph("Kcal est.", _s["PDF_MealHeaderC"]),
                Paragraph("", _s["PDF_MealHeader"]),
            ]

            # Filas de alimentos
            rows = [header_row]
            for alimento, gramos in alimentos.items():
                nombre_fmt = alimento.replace("_", " ").title()
                gramos_int = int(round(gramos))
                rows.append([
                    Paragraph(nombre_fmt, _s["PDF_Cell"]),
                    Paragraph(f"{gramos_int} g",  _s["PDF_CellC"]),
                    Paragraph("",                  _s["PDF_CellC"]),
                    Paragraph("",                  _s["PDF_CellC"]),
                ])

            # Fila de total
            rows.append([
                Paragraph("<b>Total comida</b>", _s["PDF_CellBold"]),
                Paragraph("",        _s["PDF_CellC"]),
                Paragraph(f"<b>{kcal_real} kcal</b>", _s["PDF_CellCBold"]),
                Paragraph("",        _s["PDF_CellC"]),
            ])

            tbl = Table(rows, colWidths=cols)
            tbl.setStyle(TableStyle([
                # Header
                ("BACKGROUND",    (0, 0), (-1, 0), self.C_PRIMARY),
                ("TEXTCOLOR",     (0, 0), (-1, 0), _COLOR_WHITE),
                ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, 0), 8),
                # Zebra
                ("ROWBACKGROUNDS", (0, 1), (-1, -2),
                 [colors.white, _COLOR_GRAY]),
                # Total row
                ("BACKGROUND",    (0, -1), (-1, -1), colors.HexColor("#E0F2FE")),
                # Grid
                ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                ("SPAN",          (0, -1), (-2, -1)),  # "Total comida" spans 2 cols
            ]))
            flowables.append(KeepTogether([tbl, Spacer(1, 0.4 * cm)]))

        return flowables

    # ── Sección: Recomendaciones ───────────────────────────────────────────────

    def _build_recommendations(self) -> list:
        tips = [
            ("Cocción", "Utiliza aceite en aerosol (spray) para controlar la cantidad de grasa."),
            ("Medidas", "Las tazas y cucharas deben ser medidas estándar y rasas."),
            ("Pesaje", "Pesa los alimentos en crudo (antes de cocinar) salvo indicación contraria."),
            ("Hidratación", "Mantén una ingesta de agua constante de 2 a 3 litros diarios."),
            ("Ansiedad", "Puedes consumir gelatina sin azúcar (light) libremente entre comidas."),
        ]
        _s = self.styles
        rows = [[Paragraph("Recomendaciones Básicas", _s["PDF_CardTitle"]), ""]]
        for titulo, texto in tips:
            rows.append([
                Paragraph(f"<b>{titulo}:</b>", _s["PDF_Cell"]),
                Paragraph(texto, _s["PDF_Cell"]),
            ])

        usable_w = _PAGE_W - 2 * _MARGIN
        tbl = Table(rows, colWidths=[usable_w * 0.20, usable_w * 0.80])
        tbl.setStyle(TableStyle([
            ("SPAN",          (0, 0), (1, 0)),
            ("BACKGROUND",    (0, 0), (1, 0), self.C_SECONDARY),
            ("TEXTCOLOR",     (0, 0), (1, 0), _COLOR_WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _COLOR_GRAY]),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#E5E7EB")),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ]))
        return [tbl]

    # ── Footer flowable ────────────────────────────────────────────────────────

    def _build_footer_flowable(self) -> list:
        disclaimer = (
            "AVISO: Este plan es una guía general basada en objetivos de entrenamiento y composición corporal. "
            "No constituye consulta médica ni nutricional profesional. Ante condiciones de salud crónicas, "
            "consulte con un médico o nutriólogo certificado antes de seguir cualquier plan alimenticio."
        )
        _s = self.styles
        return [
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#D1D5DB")),
            Spacer(1, 0.15 * cm),
            Paragraph(f"Generado con <b>Método Base</b> · {datetime.now().strftime('%d/%m/%Y')}", _s["PDF_Footer"]),
            Spacer(1, 0.1 * cm),
            Paragraph(disclaimer, _s["PDF_Disclaimer"]),
        ]

    # ── Decoración de página ───────────────────────────────────────────────────

    def _draw_page_border(self, canvas, doc):
        """Dibuja un borde sutil alrededor de cada página."""
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#E5E7EB"))
        canvas.setLineWidth(0.5)
        canvas.rect(
            _MARGIN * 0.7, _MARGIN * 0.7,
            _PAGE_W - _MARGIN * 1.4,
            _PAGE_H - _MARGIN * 1.4,
        )
        canvas.restoreState()

    # ── Estilos ────────────────────────────────────────────────────────────────

    def _build_styles(self) -> None:
        """Registra todos los ParagraphStyle personalizados."""
        add = self.styles.add

        add(ParagraphStyle("PDF_GymName",     parent=self.styles["Normal"],
                           fontSize=14, fontName="Helvetica-Bold",
                           textColor=self.C_SECONDARY))
        add(ParagraphStyle("PDF_Sub",         parent=self.styles["Normal"],
                           fontSize=7.5, textColor=_COLOR_MID))
        add(ParagraphStyle("PDF_SmallRight",  parent=self.styles["Normal"],
                           fontSize=8, alignment=TA_RIGHT, textColor=_COLOR_MID))
        add(ParagraphStyle("PDF_Title",       parent=self.styles["Normal"],
                           fontSize=16, fontName="Helvetica-Bold",
                           textColor=self.C_PRIMARY, alignment=TA_CENTER,
                           spaceAfter=2))
        add(ParagraphStyle("PDF_SectionTitle", parent=self.styles["Normal"],
                           fontSize=10, fontName="Helvetica-Bold",
                           textColor=self.C_SECONDARY, spaceBefore=4))
        add(ParagraphStyle("PDF_CardTitle",   parent=self.styles["Normal"],
                           fontSize=9, fontName="Helvetica-Bold", textColor=_COLOR_WHITE))
        add(ParagraphStyle("PDF_Cell",        parent=self.styles["Normal"],
                           fontSize=8, leading=11))
        add(ParagraphStyle("PDF_CellBold",    parent=self.styles["Normal"],
                           fontSize=8, fontName="Helvetica-Bold", leading=11))
        add(ParagraphStyle("PDF_CellC",       parent=self.styles["Normal"],
                           fontSize=8, leading=11, alignment=TA_CENTER))
        add(ParagraphStyle("PDF_CellCBold",   parent=self.styles["Normal"],
                           fontSize=8, fontName="Helvetica-Bold",
                           leading=11, alignment=TA_CENTER))
        add(ParagraphStyle("PDF_MealHeader",  parent=self.styles["Normal"],
                           fontSize=8.5, fontName="Helvetica-Bold",
                           textColor=_COLOR_WHITE))
        add(ParagraphStyle("PDF_MealHeaderC", parent=self.styles["Normal"],
                           fontSize=8.5, fontName="Helvetica-Bold",
                           textColor=_COLOR_WHITE, alignment=TA_CENTER))
        add(ParagraphStyle("PDF_MacroNum",    parent=self.styles["Normal"],
                           fontSize=14, fontName="Helvetica-Bold",
                           textColor=_COLOR_WHITE, alignment=TA_CENTER))
        add(ParagraphStyle("PDF_MacroLabel",  parent=self.styles["Normal"],
                           fontSize=6.5, textColor=_COLOR_WHITE, alignment=TA_CENTER))
        add(ParagraphStyle("PDF_Footer",      parent=self.styles["Normal"],
                           fontSize=7.5, alignment=TA_CENTER, textColor=_COLOR_MID))
        add(ParagraphStyle("PDF_Disclaimer",  parent=self.styles["Normal"],
                           fontSize=6.5, textColor=_COLOR_MID, leading=9))

    # ── Config predeterminada ──────────────────────────────────────────────────

    @staticmethod
    def _default_config() -> dict:
        return {
            "gym_nombre":      "Método Base",
            "gym_logo":        None,
            "gym_telefono":    "",
            "gym_direccion":   "",
            "color_primario":  "#FF6B35",
            "color_secundario": "#004E89",
        }
