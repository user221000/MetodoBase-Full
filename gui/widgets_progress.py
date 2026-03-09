"""Widgets de progreso reutilizables para operaciones largas."""
import customtkinter as ctk


class ProgressIndicator(ctk.CTkFrame):
    """
    Indicador de progreso con barra, etiqueta de estado y porcentaje.

    Uso::

        progress = ProgressIndicator(parent, width=400)
        progress.pack(pady=20)
        progress.set_progress(0.5, "Seleccionando alimentos...")
        progress.complete()   # marca como completado
        progress.reset()      # reinicia
    """

    def __init__(self, master, width: int = 400, **kwargs):
        super().__init__(master, fg_color="#1E1E1E", corner_radius=10,
                         border_width=1, border_color="#444444", **kwargs)
        self.width = width

        # Etiqueta de estado
        self.lbl_estado = ctk.CTkLabel(
            self, text="Iniciando…", anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#CCCCCC",
        )
        self.lbl_estado.pack(padx=16, pady=(12, 4), anchor="w")

        # Barra de progreso
        self.barra = ctk.CTkProgressBar(
            self, width=self.width, height=20, corner_radius=10,
            progress_color="#9B4FB0", fg_color="#2A2A2A",
            mode="determinate",
        )
        self.barra.set(0)
        self.barra.pack(padx=16, pady=(0, 6), fill="x")

        # Etiqueta de porcentaje
        self.lbl_pct = ctk.CTkLabel(
            self, text="0%",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#9B4FB0",
        )
        self.lbl_pct.pack(pady=(0, 12))

    def set_progress(self, value: float, status: str = "") -> None:
        """Actualiza el progreso. ``value`` es 0.0 – 1.0."""
        value = max(0.0, min(1.0, value))
        self.barra.set(value)
        if status:
            self.lbl_estado.configure(text=status)
        self.lbl_pct.configure(text=f"{int(value * 100)}%")
        self.update_idletasks()

    def complete(self, status: str = "✓ Completado") -> None:
        """Marca como completado (verde)."""
        self.barra.set(1.0)
        self.barra.configure(progress_color="#4CAF50")
        self.lbl_estado.configure(text=status, text_color="#4CAF50")
        self.lbl_pct.configure(text="100%", text_color="#4CAF50")

    def error(self, mensaje: str = "Error en la operación") -> None:
        """Marca con error (rojo)."""
        self.lbl_estado.configure(text=f"✗ {mensaje}", text_color="#F44336")
        self.lbl_pct.configure(text_color="#F44336")

    def reset(self) -> None:
        """Reinicia el indicador."""
        self.barra.set(0)
        self.barra.configure(progress_color="#9B4FB0")
        self.lbl_estado.configure(text="Iniciando…", text_color="#CCCCCC")
        self.lbl_pct.configure(text="0%", text_color="#9B4FB0")


class SpinnerIndicator(ctk.CTkFrame):
    """
    Indicador de carga tipo spinner para operaciones sin progreso medible.

    Uso::

        spinner = SpinnerIndicator(parent)
        spinner.pack(pady=20)
        spinner.start("Procesando...")
        spinner.stop()
    """

    _CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.label = ctk.CTkLabel(
            self, text="⏳ Procesando…",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#CCCCCC",
        )
        self.label.pack()
        self._running = False
        self._idx = 0

    def start(self, message: str = "Procesando…") -> None:
        self._running = True
        self.label.configure(text=f"{self._CHARS[0]} {message}", text_color="#CCCCCC")
        self._animate()

    def stop(self) -> None:
        self._running = False
        self.label.configure(text="✓ Completado", text_color="#4CAF50")

    def _animate(self) -> None:
        if not self._running:
            return
        self._idx = (self._idx + 1) % len(self._CHARS)
        current = self.label.cget("text")
        if current:
            self.label.configure(text=self._CHARS[self._idx] + current[1:])
        self.after(100, self._animate)
