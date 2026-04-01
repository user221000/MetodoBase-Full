# -*- coding: utf-8 -*-
"""
Widget KPI card reutilizable con ícono, valor animado, contexto y cambio.

MEJORAS 2026:
- Contexto temporal ("este mes", "esta semana")  
- Indicador de cambio con flecha (↑/↓)
- Valor del cambio (+15%, -3 clientes)
- Mayor jerarquía visual
"""
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, Signal




class KPICard(QFrame):
    """
    Card KPI con business context y animación de contador.
    
    Args:
        icon_color: "purple" | "blue" | "yellow" | "cyan" | "green" | "red"
        icon_emoji: emoji para el ícono
        value: valor numérico principal
        label: descripción del KPI
        context: contexto temporal ("Este mes", "Esta semana", "Hoy")
        change_value: cambio numérico (ej: "+12", "-3")  
        change_text: texto del cambio (ej: "clientes", "%")
        trend: "up" | "down" | "neutral"
        parent: widget padre
    """

    clicked = Signal()  # Emitted when card is clicked — enables action-driven KPIs

    def __init__(
        self,
        icon_color: str,      
        icon_emoji: str,      
        value: int,
        label: str,
        context: str = "",    # ← NUEVO: "Este mes", "Esta semana"
        change_value: str = "",     # ← NUEVO: "+12", "-5"
        change_text: str = "",
        trend: str = "neutral",  
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._target_value = value
        self._current_value = 0
        self._timer: QTimer | None = None
        self._setup_ui(
            icon_color, icon_emoji, label, context,
            change_value, change_text, trend
        )

    # ── Construcción ──────────────────────────────────────────────────────────

    def _setup_ui(
        self, icon_color: str, icon_emoji: str,
        label: str, context: str,
        change_value: str, change_text: str, trend: str
    ) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(8)

        # ── Fila superior: Ícono + Contexto ────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(0)
        
        # Ícono
        icon_label = QLabel(icon_emoji)
        icon_label.setObjectName("kpiIcon")
        icon_label.setProperty("color", icon_color)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(44, 44)
        top_row.addWidget(icon_label, 0)
        
        top_row.addStretch()
        
        # Contexto temporal (derecha)
        if context:
            self._context_label = QLabel(context)
            self._context_label.setObjectName("kpiContext")
            self._context_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            top_row.addWidget(self._context_label)
        
        layout.addLayout(top_row)
        
        layout.addSpacing(8)

        # ── Valor principal ────────────────────────────────────────────────────
        self._value_label = QLabel("0")
        self._value_label.setObjectName("kpiValue")
        layout.addWidget(self._value_label)

        # ── Label del KPI ──────────────────────────────────────────────────────
        label_widget = QLabel(label)
        label_widget.setObjectName("kpiLabel")
        label_widget.setWordWrap(True)
        layout.addWidget(label_widget)
        
        layout.addSpacing(4)

        # ── Indicador de cambio (con flecha y valor) ───────────────────────────
        if change_value or change_text:
            change_row = QHBoxLayout()
            change_row.setSpacing(4)
            change_row.setContentsMargins(0, 0, 0, 0)
            
            # Flecha según tendencia
            arrow = ""
            if trend == "up":
                arrow = "↑"
            elif trend == "down":
                arrow = "↓"
            elif trend == "neutral":
                arrow = "→"
                
            # Label con flecha + valor + texto
            full_text = f"{arrow} {change_value} {change_text}".strip()
            
            self._change_label = QLabel(full_text)
            self._change_label.setObjectName("kpiChange")
            self._change_label.setProperty("trend", trend)
            change_row.addWidget(self._change_label)
            change_row.addStretch()
            
            layout.addLayout(change_row)
        else:
            # Fallback si no hay cambio
            self._change_label = QLabel("")
            self._change_label.setObjectName("kpiChange")
            self._change_label.setProperty("trend", trend)
            self._change_label.hide()

        layout.addStretch()

    # ── API pública ───────────────────────────────────────────────────────────

    def set_value(
        self, 
        value: int, 
        change_value: str = "", 
        change_text: str = "",
        trend: str = "neutral"
    ) -> None:
        """Actualiza el valor y el cambio sin animación."""
        self._target_value = value
        self._value_label.setText(str(value))
        
        if change_value or change_text:
            arrow = ""
            if trend == "up":
                arrow = "↑"
            elif trend == "down":
                arrow = "↓"
            elif trend == "neutral":
                arrow = "→"
            
            full_text = f"{arrow} {change_value} {change_text}".strip()
            self._change_label.setText(full_text)
            self._change_label.setProperty("trend", trend)
            self._change_label.style().unpolish(self._change_label)
            self._change_label.style().polish(self._change_label)
            self._change_label.show()

    def animate_value(self, duration_ms: int = 1000) -> None:
        """Anima el contador desde 0 hasta el valor objetivo."""
        if self._target_value == 0:
            self._value_label.setText("0")
            return

        steps = 40
        step_val = max(1, self._target_value // steps)
        interval = max(20, duration_ms // steps)
        self._current_value = 0

        if self._timer:
            self._timer.stop()
            self._timer.deleteLater()

        self._timer = QTimer(self)

        def _update() -> None:
            self._current_value = min(
                self._current_value + step_val, self._target_value
            )
            self._value_label.setText(str(self._current_value))
            if self._current_value >= self._target_value:
                self._timer.stop()
                self._value_label.setText(str(self._target_value))

        self._timer.timeout.connect(_update)
        self._timer.start(interval)

    def update_value(self, value: int, animate: bool = True) -> None:
        """Actualiza el valor, opcionalmente animado."""
        self._target_value = value
        if animate:
            self.animate_value()
        else:
            self.set_value(value)

    def mousePressEvent(self, event) -> None:
        """Emit clicked signal on card click — enables action-driven KPIs."""
        self.clicked.emit()
        super().mousePressEvent(event)
