"""Sistema de notificaciones toast no intrusivas."""
import customtkinter as ctk


class ToastNotification(ctk.CTkFrame):
    """
    Notificación toast que aparece temporalmente en la esquina superior derecha.

    Uso::

        toast = ToastNotification(parent, "✓ Plan generado", tipo="success")
        toast.show()
    """

    TIPOS = {
        'success': {'bg': "#4CAF50", 'icon': "✓"},
        'error':   {'bg': "#F44336", 'icon': "✗"},
        'warning': {'bg': "#FF9800", 'icon': "⚠"},
        'info':    {'bg': "#2196F3", 'icon': "ℹ"},
    }

    def __init__(self, master, mensaje: str, tipo: str = "info", duracion: int = 3000):
        config = self.TIPOS.get(tipo, self.TIPOS['info'])
        super().__init__(
            master,
            fg_color=config['bg'],
            corner_radius=8,
            border_width=0,
        )
        self.duracion = duracion

        ctk.CTkLabel(
            self, text=config['icon'],
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#FFFFFF",
        ).pack(side="left", padx=(15, 5), pady=10)

        ctk.CTkLabel(
            self, text=mensaje,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#FFFFFF",
            wraplength=300,
        ).pack(side="left", padx=(5, 15), pady=10)

        # Fuera de pantalla hasta que se muestre
        self.place(x=10000, y=10000)

    def show(self) -> None:
        """Muestra el toast en esquina superior derecha."""
        self.update_idletasks()
        master_w = self.master.winfo_width()
        toast_w = self.winfo_reqwidth()
        x = max(10, master_w - toast_w - 20)
        self.place(x=x, y=20)
        self.lift()
        if self.duracion > 0:
            self.after(self.duracion, self.hide)

    def hide(self) -> None:
        """Oculta y destruye el toast."""
        try:
            self.place_forget()
            self.destroy()
        except Exception:
            pass


def mostrar_toast(parent, mensaje: str, tipo: str = "info", duracion: int = 3000) -> ToastNotification:
    """
    Helper para mostrar un toast desde cualquier método de la app.

    Ejemplo::

        mostrar_toast(self, "✓ Plan generado", tipo="success")
    """
    toast = ToastNotification(parent, mensaje, tipo=tipo, duracion=duracion)
    toast.show()
    return toast
