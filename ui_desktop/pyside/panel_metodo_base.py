# -*- coding: utf-8 -*-
"""
PanelMetodoBase — Dashboard personal del usuario regular.

Muestra:
  · Saludo + rol
  · Tarjetas de estadísticas (peso, IMC, objetivo, nivel actividad)
  · Sección "Tus Calorías": TMB, GET, Kcal objetivo, macros (P/G/C)
  · Barra visual de macros proporcional
  · Botón principal "Mis alimentos" → señal abrir_preferencias
  · Botón secundario "Generar mi plan" → señal generar_plan

El panel es puramente de presentación; el FlowController conecta las señales.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from core.services.auth_service import SesionActiva
from ui_desktop.pyside.theme_manager import ThemeSwitcher


# ── Textos de actividad ────────────────────────────────────────────────────────
_ETIQUETA_ACTIVIDAD: dict[str, str] = {
    "sedentario":  "Sedentario",
    "ligero":      "Ligero",
    "moderado":    "Moderado",
    "activo":      "Activo",
    "muy_activo":  "Muy activo",
}
_ETIQUETA_OBJETIVO: dict[str, str] = {
    "perder_peso": "Perder peso",
    "mantener":    "Mantener",
    "ganar_masa":  "Ganar masa",
}


class PanelMetodoBase(QDialog):
    """Panel dashboard del usuario regular."""

    abrir_preferencias = Signal()
    generar_plan = Signal()
    editar_perfil = Signal()
    cerrar_sesion = Signal()

    def __init__(
        self,
        sesion: SesionActiva,
        perfil: dict[str, Any] | None = None,
        alimentos_excluidos: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._sesion = sesion
        self._perfil = perfil or {}
        self._excluidos = alimentos_excluidos or []
        self.setWindowTitle(f"Método Base — {sesion.nombre_display}")
        self.setMinimumSize(540, 600)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self._build_ui()

    # ── Construcción de UI ────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Barra superior ────────────────────────────────────────────────
        topbar = QFrame()
        topbar.setObjectName("card")
        topbar.setStyleSheet(
            "QFrame#card { border-radius: 0; border-bottom: 1px solid #232323;"
            "border-left: none; border-right: none; border-top: none; }"
        )
        topbar_lay = QHBoxLayout(topbar)
        topbar_lay.setContentsMargins(28, 18, 28, 18)

        brand = QLabel("● Método Base")
        brand.setStyleSheet(
            "color: #FF6F0F; font-size: 14px; font-weight: 700; background: transparent;"
        )
        topbar_lay.addWidget(brand)
        topbar_lay.addStretch()

        # Selector de tema visual (dark / light / aurora)
        theme_sw = ThemeSwitcher(parent=topbar)
        topbar_lay.addWidget(theme_sw)
        topbar_lay.addSpacerItem(QSpacerItem(16, 0, QSizePolicy.Fixed))

        # Rol badge
        rol_text = {"admin": "ADMIN", "gym": "GYM", "usuario": "USUARIO"}.get(
            self._sesion.rol, self._sesion.rol.upper()
        )
        rol_obj = {"admin": "role_badge_admin", "gym": "role_badge_gym"}.get(
            self._sesion.rol, "role_badge_usuario"
        )
        rol_lbl = QLabel(rol_text)
        rol_lbl.setObjectName(rol_obj)
        topbar_lay.addWidget(rol_lbl)
        topbar_lay.addSpacerItem(QSpacerItem(12, 0, QSizePolicy.Fixed))

        btn_out = QPushButton("Cerrar sesión")
        btn_out.setObjectName("btn_text")
        btn_out.clicked.connect(self._on_cerrar)
        topbar_lay.addWidget(btn_out)
        outer.addWidget(topbar)

        # ── Contenido con scroll ──────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(36, 36, 36, 36)
        lay.setSpacing(0)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        # Saludo
        greeting = QLabel(f"Hola, {self._sesion.nombre_display} 👋")
        greeting.setObjectName("display")
        lay.addWidget(greeting)

        sub_text = "Aquí está tu resumen personal y accesos directos a tu plan."
        sub = QLabel(sub_text)
        sub.setObjectName("subheadline")
        sub.setWordWrap(True)
        lay.addWidget(sub)
        lay.addSpacerItem(QSpacerItem(0, 28, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # ── Tarjetas de estadísticas ──────────────────────────────────────
        sec_stats = QLabel("TU PERFIL")
        sec_stats.setObjectName("section_title")
        lay.addWidget(sec_stats)
        lay.addSpacerItem(QSpacerItem(0, 12, QSizePolicy.Minimum, QSizePolicy.Fixed))

        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)
        stats_data = self._build_stats()
        for idx, (val, label, unit) in enumerate(stats_data):
            stats_grid.addWidget(_StatCard(val, label, unit), idx // 2, idx % 2)
        lay.addLayout(stats_grid)
        lay.addSpacerItem(QSpacerItem(0, 28, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # ── Sección Calorías y Macros ─────────────────────────────────────
        calc = self._calcular_nutricional()
        if calc is not None:
            sec_cal = QLabel("TUS CALORÍAS Y MACROS")
            sec_cal.setObjectName("section_title")
            lay.addWidget(sec_cal)
            lay.addSpacerItem(QSpacerItem(0, 12, QSizePolicy.Minimum, QSizePolicy.Fixed))
            lay.addWidget(_CaloriasCard(calc))
            lay.addSpacerItem(QSpacerItem(0, 28, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # ── Sección Alimentos ─────────────────────────────────────────────
        sec_food = QLabel("PREFERENCIAS ALIMENTARIAS")
        sec_food.setObjectName("section_title")
        lay.addWidget(sec_food)
        lay.addSpacerItem(QSpacerItem(0, 12, QSizePolicy.Minimum, QSizePolicy.Fixed))

        food_card = QFrame()
        food_card.setObjectName("card")
        food_lay = QVBoxLayout(food_card)
        food_lay.setContentsMargins(20, 18, 20, 18)
        food_lay.setSpacing(8)

        n_excluidos = len(self._excluidos)
        food_lbl = QLabel(
            f"{n_excluidos} alimentos excluidos de tu plan"
            if n_excluidos else "Todos los alimentos activos en tu plan."
        )
        food_lbl.setObjectName("headline")
        food_lay.addWidget(food_lbl)

        food_sub = QLabel("Personaliza qué alimentos aparecen en tus planes nutricionales.")
        food_sub.setObjectName("subheadline")
        food_lay.addWidget(food_sub)
        food_lay.addSpacerItem(QSpacerItem(0, 8, QSizePolicy.Minimum, QSizePolicy.Fixed))

        btn_food = QPushButton("🥗  Configurar mis alimentos")
        btn_food.setObjectName("btn_choice_card")
        btn_food.setFixedHeight(64)
        btn_food.setStyleSheet(
            "QPushButton#btn_choice_card { font-size: 14px; min-height: 64px;"
            "text-align: left; padding-left: 20px; }"
        )
        btn_food.clicked.connect(self.abrir_preferencias)
        food_lay.addWidget(btn_food)
        lay.addWidget(food_card)
        lay.addSpacerItem(QSpacerItem(0, 16, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # ── Acciones principales ──────────────────────────────────────────
        sec_acc = QLabel("ACCIONES")
        sec_acc.setObjectName("section_title")
        lay.addWidget(sec_acc)
        lay.addSpacerItem(QSpacerItem(0, 12, QSizePolicy.Minimum, QSizePolicy.Fixed))

        btn_plan = QPushButton("⚡  Generar mi plan nutricional")
        btn_plan.setFixedHeight(52)
        btn_plan.clicked.connect(self.generar_plan)
        lay.addWidget(btn_plan)
        lay.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        btn_edit = QPushButton("✏️  Editar mi perfil")
        btn_edit.setObjectName("btn_secondary")
        btn_edit.setFixedHeight(44)
        btn_edit.clicked.connect(self.editar_perfil)
        lay.addWidget(btn_edit)

        lay.addStretch()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _build_stats(self) -> list[tuple[str, str, str]]:
        """Devuelve lista de (valor, etiqueta, unidad) para las stat cards."""
        p = self._perfil
        rows: list[tuple[str, str, str]] = []

        # Peso
        peso = p.get("peso_kg")
        rows.append((f"{peso:.1f}" if peso else "—", "Peso", "kg"))

        # IMC
        estatura = p.get("estatura_cm")
        if peso and estatura and estatura > 0:
            imc = peso / ((estatura / 100) ** 2)
            rows.append((f"{imc:.1f}", "IMC", ""))
        else:
            rows.append(("—", "IMC", ""))

        # Actividad
        actividad = _ETIQUETA_ACTIVIDAD.get(p.get("nivel_actividad", ""), "—")
        rows.append((actividad, "Actividad", ""))

        # Objetivo
        objetivo = _ETIQUETA_OBJETIVO.get(p.get("objetivo", ""), "—")
        rows.append((objetivo, "Objetivo", ""))

        return rows

    def _calcular_nutricional(self) -> dict | None:
        """
        Calcula TMB, GET, kcal objetivo y macros a partir del perfil.

        Retorna None si faltan datos esenciales.
        """
        p = self._perfil
        peso = p.get("peso_kg")
        grasa = p.get("grasa_corporal_pct")
        nivel = p.get("nivel_actividad")
        objetivo = p.get("objetivo")

        if not all((peso, grasa, nivel, objetivo)):
            return None

        try:
            from config.constantes import FACTORES_ACTIVIDAD
            from core.motor_nutricional import MotorNutricional

            factor = FACTORES_ACTIVIDAD.get(nivel, 1.2)
            masa_magra = MotorNutricional.calcular_masa_magra(peso, grasa)
            tmb = MotorNutricional.calcular_tmb(masa_magra)
            get_total = MotorNutricional.calcular_get(tmb, factor)
            kcal_obj = MotorNutricional.calcular_kcal_objetivo(get_total, objetivo)
            macros = MotorNutricional.calcular_macros(peso, kcal_obj)

            return {
                "tmb": round(tmb),
                "get_total": round(get_total),
                "kcal_objetivo": round(kcal_obj),
                "proteina_g": round(macros["proteina_g"], 1),
                "grasa_g": round(macros["grasa_g"], 1),
                "carbs_g": round(macros["carbs_g"], 1),
                "kcal_proteina": round(macros["proteina_g"] * 4),
                "kcal_grasa": round(macros["grasa_g"] * 9),
                "kcal_carbs": round(macros["carbs_g"] * 4),
            }
        except Exception:
            return None

    # ── Slots ─────────────────────────────────────────────────────────────

    def _on_cerrar(self) -> None:
        self.cerrar_sesion.emit()
        self.reject()

    def actualizar_excluidos(self, excluidos: list[str]) -> None:
        """Llama esto tras editar preferencias para refrescar el conteo."""
        self._excluidos = excluidos
        # Re-build es costoso; basta con actualizar el label
        # (FlowController puede llamar rebuild si prefiere)


# ── Widgets internos ──────────────────────────────────────────────────────────

class _StatCard(QFrame):
    """Tarjeta individual de estadística."""

    def __init__(self, valor: str, etiqueta: str, unidad: str) -> None:
        super().__init__()
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(2)

        val_lbl = QLabel(f"{valor} {unidad}".strip())
        val_lbl.setObjectName("stat_value")
        lay.addWidget(val_lbl)

        et_lbl = QLabel(etiqueta)
        et_lbl.setObjectName("stat_label")
        lay.addWidget(et_lbl)


class _CaloriasCard(QFrame):
    """
    Tarjeta de calorías y macronutrientes con barra visual proporcional.

    Muestra:
    - TMB, GET, Kcal objetivo en fila de KPIs
    - Barra de macros coloreada (proteína / grasa / carbohidratos)
    - Gramos y kcal de cada macro
    """

    _COLOR_PROTEINA = "#4CAF50"   # verde
    _COLOR_GRASA    = "#FF9800"   # naranja
    _COLOR_CARBS    = "#2196F3"   # azul
    _COLOR_ROW_BG   = "#222222"

    def __init__(self, calc: dict) -> None:
        super().__init__()
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._calc = calc
        self._build()

    def _build(self) -> None:
        c = self._calc
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        # ── Fila de KPIs calóricos ────────────────────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(0)
        for label, valor, unidad, tooltip in [
            ("TMB",           str(c["tmb"]),           "kcal", "Tasa Metabólica Basal (Katch-McArdle)"),
            ("GET",           str(c["get_total"]),      "kcal", "Gasto Energético Total (TMB × factor actividad)"),
            ("Kcal objetivo", str(c["kcal_objetivo"]),  "kcal", "Calorías ajustadas a tu objetivo"),
        ]:
            cell = QWidget()
            cell.setToolTip(tooltip)
            cell_lay = QVBoxLayout(cell)
            cell_lay.setContentsMargins(8, 8, 8, 8)
            cell_lay.setSpacing(2)

            v_lbl = QLabel(valor)
            v_lbl.setAlignment(Qt.AlignCenter)
            v_lbl.setStyleSheet(
                "color: #FF6F0F; font-size: 22px; font-weight: 700; background: transparent;"
            )
            cell_lay.addWidget(v_lbl)

            u_lbl = QLabel(unidad)
            u_lbl.setAlignment(Qt.AlignCenter)
            u_lbl.setStyleSheet("color: #888; font-size: 10px; background: transparent;")
            cell_lay.addWidget(u_lbl)

            l_lbl = QLabel(label)
            l_lbl.setAlignment(Qt.AlignCenter)
            l_lbl.setStyleSheet("color: #B8B8B8; font-size: 11px; background: transparent;")
            cell_lay.addWidget(l_lbl)

            kpi_row.addWidget(cell, 1)

            if label != "Kcal objetivo":
                sep = QFrame()
                sep.setFrameShape(QFrame.VLine)
                sep.setStyleSheet("color: #333; background: #333;")
                kpi_row.addWidget(sep)

        kpi_frame = QFrame()
        kpi_frame.setStyleSheet(
            f"QFrame {{ background-color: {self._COLOR_ROW_BG}; border-radius: 8px; border: none; }}"
        )
        kpi_frame.setLayout(kpi_row)
        root.addWidget(kpi_frame)

        # ── Título macros ─────────────────────────────────────────────────
        macros_title = QLabel("Distribución de macronutrientes")
        macros_title.setStyleSheet("color: #B8B8B8; font-size: 11px; font-weight: 600;")
        root.addWidget(macros_title)

        # ── Barra proporcional ────────────────────────────────────────────
        kcal_p = c["kcal_proteina"]
        kcal_g = c["kcal_grasa"]
        kcal_c = c["kcal_carbs"]
        total_kcal = max(kcal_p + kcal_g + kcal_c, 1)

        bar_row = QHBoxLayout()
        bar_row.setSpacing(2)
        for kcal_part, color, tooltip in [
            (kcal_p, self._COLOR_PROTEINA, f"Proteína: {kcal_p:.0f} kcal"),
            (kcal_g, self._COLOR_GRASA,    f"Grasa: {kcal_g:.0f} kcal"),
            (kcal_c, self._COLOR_CARBS,    f"Carbs: {kcal_c:.0f} kcal"),
        ]:
            pct = int(round(kcal_part / total_kcal * 100))
            bar = QProgressBar()
            bar.setFixedHeight(12)
            bar.setRange(0, 100)
            bar.setValue(pct)
            bar.setTextVisible(False)
            bar.setToolTip(tooltip)
            bar.setStyleSheet(
                f"QProgressBar {{ border-radius: 6px; background: #333; border: none; }}"
                f"QProgressBar::chunk {{ background: {color}; border-radius: 6px; }}"
            )
            bar_row.addWidget(bar, max(pct, 1))
        root.addLayout(bar_row)

        # ── Fila de macros detallados ─────────────────────────────────────
        macro_row = QHBoxLayout()
        macro_row.setSpacing(0)
        for label, grams, kcal_val, color in [
            ("Proteína", c["proteina_g"], kcal_p, self._COLOR_PROTEINA),
            ("Grasa",    c["grasa_g"],    kcal_g, self._COLOR_GRASA),
            ("Carbs",    c["carbs_g"],    kcal_c, self._COLOR_CARBS),
        ]:
            cell = QWidget()
            cell_lay = QVBoxLayout(cell)
            cell_lay.setContentsMargins(8, 10, 8, 10)
            cell_lay.setSpacing(1)

            dot_lbl = QLabel(f"● {label}")
            dot_lbl.setAlignment(Qt.AlignCenter)
            dot_lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 700;")
            cell_lay.addWidget(dot_lbl)

            g_lbl = QLabel(f"{grams:.1f} g")
            g_lbl.setAlignment(Qt.AlignCenter)
            g_lbl.setStyleSheet("color: #F5F5F5; font-size: 16px; font-weight: 700;")
            cell_lay.addWidget(g_lbl)

            k_lbl = QLabel(f"{kcal_val:.0f} kcal")
            k_lbl.setAlignment(Qt.AlignCenter)
            k_lbl.setStyleSheet("color: #888; font-size: 10px;")
            cell_lay.addWidget(k_lbl)

            pct_macro = int(round(kcal_val / total_kcal * 100))
            p_lbl = QLabel(f"{pct_macro}%")
            p_lbl.setAlignment(Qt.AlignCenter)
            p_lbl.setStyleSheet("color: #B8B8B8; font-size: 10px;")
            cell_lay.addWidget(p_lbl)

            macro_row.addWidget(cell, 1)

            if label != "Carbs":
                sep = QFrame()
                sep.setFrameShape(QFrame.VLine)
                sep.setStyleSheet("color: #333; background: #333;")
                macro_row.addWidget(sep)

        macro_frame = QFrame()
        macro_frame.setStyleSheet(
            f"QFrame {{ background-color: {self._COLOR_ROW_BG}; border-radius: 8px; border: none; }}"
        )
        macro_frame.setLayout(macro_row)
        root.addWidget(macro_frame)
