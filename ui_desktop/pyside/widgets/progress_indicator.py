# -*- coding: utf-8 -*-
"""Indicador de progreso reutilizable PySide6 — reemplaza gui/widgets_progress.ProgressIndicator."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar

from design_system.tokens import Colors, Radius


class ProgressIndicator(QWidget):
    """
    Barra de progreso con etiqueta de estado y porcentaje.

    Uso::

        progress = ProgressIndicator(parent)
        layout.addWidget(progress)
        progress.set_progress(0.5, "Seleccionando alimentos...")
        progress.complete()
        progress.reset()
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QWidget {{ background-color: {Colors.BG_CARD}; border: 1px solid {Colors.BORDER_DEFAULT};"
            f" border-radius: {Radius.LG}px; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        self.lbl_estado = QLabel("Preparando flujo de trabajo...")
        self.lbl_estado.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(self.lbl_estado)

        self.barra = QProgressBar()
        self.barra.setRange(0, 100)
        self.barra.setValue(0)
        self.barra.setTextVisible(False)
        self.barra.setFixedHeight(20)
        self.barra.setStyleSheet(
            f"QProgressBar {{ background-color: {Colors.BG_HOVER}; border: none; border-radius: {Radius.LG}px; }}"
            f"QProgressBar::chunk {{ background-color: {Colors.PRIMARY}; border-radius: {Radius.LG}px; }}"
        )
        layout.addWidget(self.barra)

        self.lbl_pct = QLabel("0%")
        self.lbl_pct.setStyleSheet(
            f"color: {Colors.PRIMARY}; font-size: 14px; font-weight: bold;"
            " background: transparent; border: none;"
        )
        layout.addWidget(self.lbl_pct)

    # ------------------------------------------------------------------

    def set_progress(self, value: float, status: str = "") -> None:
        """Actualiza el progreso. *value* es 0.0 – 1.0."""
        value = max(0.0, min(1.0, value))
        self.barra.setValue(int(value * 100))
        if status:
            self.lbl_estado.setText(status)
        self.lbl_pct.setText(f"{int(value * 100)}%")

    def complete(self, status: str = "✓ Completado") -> None:
        """Marca como completado (verde)."""
        self.barra.setValue(100)
        self.barra.setStyleSheet(
            f"QProgressBar {{ background-color: {Colors.BG_HOVER}; border: none; border-radius: {Radius.LG}px; }}"
            f"QProgressBar::chunk {{ background-color: {Colors.SUCCESS}; border-radius: {Radius.LG}px; }}"
        )
        self.lbl_estado.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 12px; background: transparent; border: none;")
        self.lbl_estado.setText(status)
        self.lbl_pct.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        self.lbl_pct.setText("100%")

    def error(self, mensaje: str = "Error en la operación") -> None:
        """Marca con error (rojo)."""
        self.lbl_estado.setStyleSheet(f"color: {Colors.ERROR}; font-size: 12px; background: transparent; border: none;")
        self.lbl_estado.setText(f"✗ {mensaje}")
        self.lbl_pct.setStyleSheet(f"color: {Colors.ERROR}; font-size: 14px; font-weight: bold; background: transparent; border: none;")

    def reset(self) -> None:
        """Reinicia el indicador."""
        self.barra.setValue(0)
        self.barra.setStyleSheet(
            f"QProgressBar {{ background-color: {Colors.BG_HOVER}; border: none; border-radius: {Radius.LG}px; }}"
            f"QProgressBar::chunk {{ background-color: {Colors.PRIMARY}; border-radius: {Radius.LG}px; }}"
        )
        self.lbl_estado.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent; border: none;")
        self.lbl_estado.setText("Preparando flujo de trabajo...")
        self.lbl_pct.setStyleSheet(
            f"color: {Colors.PRIMARY}; font-size: 14px; font-weight: bold;"
            " background: transparent; border: none;"
        )
        self.lbl_pct.setText("0%")
