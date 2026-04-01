# -*- coding: utf-8 -*-
"""
animations.py — Micro-animation helpers for MetodoBase SaaS 2026.

Reusable animation utilities for fade-in, stagger, hover glow, and
smooth transitions. Uses PySide6 QPropertyAnimation since QSS does
NOT support CSS transitions.

Usage:
    from ui_desktop.pyside.widgets.animations import (
        fade_in_widget,
        stagger_fade_in,
        apply_hover_glow,
        pulse_widget,
    )
"""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QTimer,
    QObject,
    QEvent,
    Property,
    Qt,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QWidget,
)

from design_system.tokens import Animation, Colors


# ══════════════════════════════════════════════════════════════════════════════
# FADE-IN — Opacity animation for widgets and panels
# ══════════════════════════════════════════════════════════════════════════════


def fade_in_widget(
    widget: QWidget,
    duration: int = Animation.SMOOTH,
    delay: int = 0,
    easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
) -> None:
    """Apply a fade-in opacity animation to any widget.

    The QGraphicsOpacityEffect is automatically removed once the
    animation completes (opacity=1.0) so it doesn't conflict with
    other effects like QGraphicsDropShadowEffect (PySide6 allows
    only ONE graphics effect per widget).

    Args:
        widget: Target widget.
        duration: Animation length in ms (default 400).
        delay: Optional delay before starting in ms.
        easing: Easing curve type.
    """
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)

    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(easing)

    # Remove the effect after animation so it doesn't block other effects
    def _cleanup():
        widget.setGraphicsEffect(None)
        # Clear refs
        widget._fade_anim = None
        widget._fade_effect = None

    anim.finished.connect(_cleanup)

    # Store reference to prevent GC during animation
    widget._fade_anim = anim
    widget._fade_effect = effect

    if delay > 0:
        QTimer.singleShot(delay, anim.start)
    else:
        anim.start()


def fade_in_dialog(
    dialog: QWidget,
    duration: int = Animation.SMOOTH,
) -> QPropertyAnimation:
    """Fade-in for QDialog using windowOpacity (like panel_inicio)."""
    dialog.setWindowOpacity(0)
    anim = QPropertyAnimation(dialog, b"windowOpacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    # prevent GC
    dialog._fade_in = anim
    return anim


# ══════════════════════════════════════════════════════════════════════════════
# STAGGER — Sequential fade-in for lists of widgets (cards, rows)
# ══════════════════════════════════════════════════════════════════════════════


def stagger_fade_in(
    widgets: list[QWidget],
    base_delay: int = 60,
    duration: int = Animation.SLOW,
) -> None:
    """Fade-in a list of widgets sequentially with staggered delay.

    Args:
        widgets: List of widgets to animate.
        base_delay: Delay between each widget start (ms).
        duration: Duration of each individual fade.
    """
    for i, widget in enumerate(widgets):
        fade_in_widget(widget, duration=duration, delay=i * base_delay)


# ══════════════════════════════════════════════════════════════════════════════
# HOVER GLOW — Smooth shadow animation on enter/leave
# ══════════════════════════════════════════════════════════════════════════════


class _HoverGlowFilter(QObject):
    """Event filter that animates a drop shadow on hover."""

    def __init__(
        self,
        target: QWidget,
        color: str = Colors.PRIMARY,
        blur_rest: int = 0,
        blur_hover: int = 24,
        duration: int = Animation.NORMAL,
    ):
        super().__init__(target)
        self._target = target
        self._blur_rest = blur_rest
        self._blur_hover = blur_hover
        self._duration = duration

        self._shadow = QGraphicsDropShadowEffect(target)
        self._shadow.setBlurRadius(blur_rest)
        self._shadow.setColor(QColor(color))
        self._shadow.setOffset(0, 2)
        target.setGraphicsEffect(self._shadow)

        self._anim = QPropertyAnimation(self._shadow, b"blurRadius", self)
        self._anim.setDuration(duration)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self._target:
            if event.type() == QEvent.Type.Enter:
                self._animate(self._blur_hover)
            elif event.type() == QEvent.Type.Leave:
                self._animate(self._blur_rest)
        return False

    def _animate(self, target_blur: int) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._shadow.blurRadius())
        self._anim.setEndValue(target_blur)
        self._anim.start()


def apply_hover_glow(
    widget: QWidget,
    color: str = Colors.PRIMARY,
    blur_rest: int = 0,
    blur_hover: int = 24,
    duration: int = Animation.NORMAL,
) -> None:
    """Add a smooth hover glow effect to a widget.

    On mouse enter the shadow grows smoothly, on leave it fades out.

    Args:
        widget: Target widget (card, frame, etc.)
        color: Glow color (hex string).
        blur_rest: Shadow blur at rest.
        blur_hover: Shadow blur on hover.
        duration: Transition time in ms.
    """
    f = _HoverGlowFilter(widget, color, blur_rest, blur_hover, duration)
    widget.installEventFilter(f)
    # prevent GC
    widget._hover_glow_filter = f


# ══════════════════════════════════════════════════════════════════════════════
# STATIC GLOW — One-time shadow (like panel_inicio cards)
# ══════════════════════════════════════════════════════════════════════════════


def apply_card_shadow(
    widget: QWidget,
    color: str = Colors.PRIMARY,
    blur: int = 32,
    offset_y: int = 4,
) -> QGraphicsDropShadowEffect:
    """Apply a static neon glow shadow to a card.

    Args:
        widget: Target widget.
        color: Shadow color (hex).
        blur: Blur radius.
        offset_y: Vertical offset.

    Returns:
        The QGraphicsDropShadowEffect applied.
    """
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(color))
    shadow.setOffset(0, offset_y)
    widget.setGraphicsEffect(shadow)
    return shadow


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE-IN — Horizontal/vertical slide from off-screen
# ══════════════════════════════════════════════════════════════════════════════


def slide_in_widget(
    widget: QWidget,
    direction: str = "up",
    distance: int = 20,
    duration: int = Animation.SLOW,
    delay: int = 0,
) -> None:
    """Slide a widget in from a direction while fading in.

    Args:
        widget: Target widget.
        direction: "up", "down", "left", "right".
        distance: Pixels to slide.
        duration: Animation duration in ms.
        delay: Delay before start.
    """
    # Fade
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)

    fade = QPropertyAnimation(effect, b"opacity", widget)
    fade.setDuration(duration)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(QEasingCurve.Type.OutCubic)

    # Clean up effect after animation completes
    def _cleanup():
        widget.setGraphicsEffect(None)
        widget._slide_fade = None
        widget._slide_effect = None

    fade.finished.connect(_cleanup)

    widget._slide_fade = fade
    widget._slide_effect = effect

    if delay > 0:
        QTimer.singleShot(delay, fade.start)
    else:
        fade.start()


# ══════════════════════════════════════════════════════════════════════════════
# HOVER SCALE — Smooth scale up/down on enter/leave via margins
# ══════════════════════════════════════════════════════════════════════════════


class _HoverScaleFilter(QObject):
    """Event filter that simulates scale-up on hover via negative margins."""

    def __init__(
        self,
        target: QWidget,
        scale_px: int = 2,
        duration: int = 150,
    ):
        super().__init__(target)
        self._target = target
        self._scale_px = scale_px
        self._duration = duration
        self._hovered = False

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self._target:
            if event.type() == QEvent.Type.Enter and not self._hovered:
                self._hovered = True
                m = self._target.contentsMargins()
                self._target.setContentsMargins(
                    m.left() - self._scale_px,
                    m.top() - self._scale_px,
                    m.right() - self._scale_px,
                    m.bottom() - self._scale_px,
                )
            elif event.type() == QEvent.Type.Leave and self._hovered:
                self._hovered = False
                m = self._target.contentsMargins()
                self._target.setContentsMargins(
                    m.left() + self._scale_px,
                    m.top() + self._scale_px,
                    m.right() + self._scale_px,
                    m.bottom() + self._scale_px,
                )
        return False


def apply_hover_scale(
    widget: QWidget,
    scale_px: int = 2,
    duration: int = 150,
) -> None:
    """Add a subtle hover scale effect by adjusting margins.

    Args:
        widget: Target widget (card, frame, button).
        scale_px: Pixels to grow on each side.
        duration: Reserved for future smooth animation.
    """
    f = _HoverScaleFilter(widget, scale_px, duration)
    widget.installEventFilter(f)
    widget._hover_scale_filter = f
