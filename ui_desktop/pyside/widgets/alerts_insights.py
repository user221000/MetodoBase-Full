# -*- coding: utf-8 -*-
"""
Widget de Alertas e Insights — Dashboard Business Intelligence.

Muestra insights accionables del negocio:
- Clientes sin plan activo
- Clientes inactivos por 30+ días  
- Suscripciones por vencer
- Recomendaciones automáticas

Diseño:
┌─────────────────────────────────────────────────────────┐
│  🔔 Alertas e Insights                                   │
├─────────────────────────────────────────────────────────┤
│  ⚠️  3 clientes no tienen plan activo                   │
│      [Ver clientes →]                                   │
│                                                          │
│  📉  5 clientes sin actualización en 30+ días           │
│      [Revisar inactivos →]                              │
│                                                          │
│  💰  12 suscripciones vencen esta semana                │
│      [Gestionar mensualidades →]                        │
└─────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AlertInsight(QWidget):
    """
    Widget individual de alerta/insight.
    
    Args:
        icon: emoji del ícono (⚠️, 📉, 💰, ✨, etc)
        type_: tipo de alerta ("warning" | "info" | "success" | "neutral")
        message: mensaje descriptivo
        action_text: texto del botón de acción (opcional)
        action_param: parámetro a emitir al hacer click
    """
    
    action_clicked = Signal(str)  # emite action_param
    
    def __init__(
        self,
        icon: str,
        type_: str,
        message: str,
        action_text: str = "",
        action_param: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._action_param = action_param
        self._setup_ui(icon, type_, message, action_text)
        
    def _setup_ui(
        self, icon: str, type_: str, message: str, action_text: str
    ) -> None:
        self.setObjectName("alertInsightItem")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Ícono
        icon_label = QLabel(icon)
        icon_label.setObjectName("alertIcon")
        icon_label.setProperty("type", type_)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(32, 32)
        layout.addWidget(icon_label)
        
        # Mensaje
        msg_label = QLabel(message)
        msg_label.setObjectName("alertMessage")
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(msg_label, 1)
        
        # Botón de acción (opcional)
        if action_text:
            btn = QPushButton(action_text)
            btn.setObjectName("alertActionBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda: self.action_clicked.emit(self._action_param))
            layout.addWidget(btn)


class AlertsInsightsWidget(QFrame):
    """
    Panel de alertas e insights accionables.
    
    Se posiciona en el dashboard y muestra información crítica
    que requiere atención del usuario.
    
    Signals:
        alert_action_clicked(action_param: str) - cuando se hace click en una acción
    """
    
    alert_action_clicked = Signal(str)
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("alertsInsightsPanel")
        self._alerts: list[AlertInsight] = []
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("alertsHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(8)
        
        # Ícono + Título
        bell_label = QLabel("🔔")
        bell_label.setObjectName("alertsBellIcon")
        bell_label.setFixedSize(24, 24)
        header_layout.addWidget(bell_label)
        
        title = QLabel("Alertas e Insights")
        title.setObjectName("alertsTitle")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        main_layout.addWidget(header)
        
        # Divider
        divider = QFrame()
        divider.setObjectName("alertsDivider")
        divider.setFixedHeight(1)
        main_layout.addWidget(divider)
        
        # Container para las alertas
        self._alerts_container = QWidget()
        self._alerts_container.setObjectName("alertsContainer")
        self._alerts_layout = QVBoxLayout(self._alerts_container)
        self._alerts_layout.setContentsMargins(0, 0, 0, 0)
        self._alerts_layout.setSpacing(0)
        
        main_layout.addWidget(self._alerts_container)
        
        # Empty state (se oculta cuando hay alertas)
        self._empty_state = QWidget()
        empty_layout = QVBoxLayout(self._empty_state)
        empty_layout.setContentsMargins(20, 24, 20, 24)
        empty_layout.setSpacing(8)
        
        empty_icon = QLabel("✅")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon.setStyleSheet("font-size: 32px; background: transparent;")
        empty_layout.addWidget(empty_icon)
        
        empty_msg = QLabel("Todo está en orden")
        empty_msg.setObjectName("alertsEmptyMessage")
        empty_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_msg)
        
        empty_submsg = QLabel("No hay alertas que requieran tu atención")
        empty_submsg.setObjectName("alertsEmptySubmessage")
        empty_submsg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_submsg)
        
        main_layout.addWidget(self._empty_state)
        
    def add_alert(
        self,
        icon: str,
        type_: str,
        message: str,
        action_text: str = "",
        action_param: str = "",
    ) -> None:
        """
        Agrega una alerta/insight al panel.
        
        Args:
            icon: emoji del ícono
            type_: "warning" | "info" | "success" | "neutral"
            message: texto del mensaje
            action_text: texto del botón (opcional)
            action_param: identificador de la acción
        """
        alert = AlertInsight(icon, type_, message, action_text, action_param)
        alert.action_clicked.connect(self.alert_action_clicked.emit)
        
        self._alerts.append(alert)
        self._alerts_layout.addWidget(alert)
        
        # Ocultar empty state
        self._empty_state.hide()
        self._alerts_container.show()
        
    def clear_alerts(self) -> None:
        """Remueve todas las alertas."""
        for alert in self._alerts:
            self._alerts_layout.removeWidget(alert)
            alert.deleteLater()
        
        self._alerts.clear()
        
        # Mostrar empty state
        self._alerts_container.hide()
        self._empty_state.show()
        
    def get_alert_count(self) -> int:
        """Retorna el número de alertas activas."""
        return len(self._alerts)
