# -*- coding: utf-8 -*-
"""Diálogo de confirmación temático para PySide6 — reemplaza QMessageBox.question()."""

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt

from design_system.tokens import Colors, Radius, Spacing


class ConfirmDialog(QDialog):
    """Diálogo modal de confirmación con estilo Yellow Neon Premium."""

    def __init__(
        self,
        parent: QWidget,
        titulo: str,
        mensaje: str,
        texto_si: str = "Sí",
        texto_no: str = "No",
    ):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(360)
        self.setMaximumWidth(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(Spacing.LG)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.LG)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(
            f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: 700;"
            " background: transparent;"
        )
        layout.addWidget(lbl_titulo)

        lbl_msg = QLabel(mensaje)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 14px;"
            " background: transparent;"
        )
        layout.addWidget(lbl_msg)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(Spacing.SM)
        btn_row.addStretch()

        btn_no = QPushButton(texto_no)
        btn_no.setObjectName("btnGhost")
        btn_no.setFixedHeight(36)
        btn_no.setCursor(Qt.PointingHandCursor)
        btn_no.clicked.connect(self.reject)
        btn_row.addWidget(btn_no)

        btn_si = QPushButton(texto_si)
        btn_si.setObjectName("btnPrimary")
        btn_si.setFixedHeight(36)
        btn_si.setCursor(Qt.PointingHandCursor)
        btn_si.clicked.connect(self.accept)
        btn_row.addWidget(btn_si)

        layout.addLayout(btn_row)


def confirmar(
    parent: QWidget,
    titulo: str,
    mensaje: str,
    texto_si: str = "Sí",
    texto_no: str = "No",
) -> bool:
    """Muestra un diálogo de confirmación temático. Retorna True si el usuario acepta."""
    dlg = ConfirmDialog(parent, titulo, mensaje, texto_si, texto_no)
    return dlg.exec() == QDialog.DialogCode.Accepted
