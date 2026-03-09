"""Ventana modal de preview del plan nutricional antes de confirmar el PDF."""
import customtkinter as ctk
from typing import Callable


class PlanPreviewWindow(ctk.CTkToplevel):
    """
    Ventana modal que muestra el resumen del plan antes de generar el PDF.
    Permite confirmar o rechazar antes de continuar.
    """

    COMIDAS_ORDEN = ["desayuno", "almuerzo", "comida", "cena"]
    COMIDAS_LABEL = {
        "desayuno": "🌅 Desayuno",
        "almuerzo": "☀️ Almuerzo",
        "comida":   "🍽  Comida",
        "cena":     "🌙 Cena",
    }

    # Colores consistentes con la app principal
    COLOR_BG      = "#0D0D0D"
    COLOR_CARD    = "#1A1A1A"
    COLOR_PRIMARY = "#9B4FB0"
    COLOR_PRIMARY_HOVER = "#B565C6"
    COLOR_TEXT    = "#F5F5F5"
    COLOR_TEXT_MUTED = "#B8B8B8"
    COLOR_SUCCESS = "#4CAF50"
    COLOR_SECONDARY = "#D4A84B"

    def __init__(self, parent, cliente, plan: dict,
                 on_confirm: Callable, on_cancel: Callable):
        super().__init__(parent)
        self.title("Vista Previa del Plan")
        self.geometry("680x780")
        self.resizable(False, True)
        self.configure(fg_color=self.COLOR_BG)
        self.grab_set()
        self.focus()

        self._on_confirm = on_confirm
        self._on_cancel = on_cancel

        # ── Título ──
        ctk.CTkLabel(
            self,
            text=f"Plan para {cliente.nombre}",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=self.COLOR_TEXT,
        ).pack(pady=(18, 2))

        obj  = getattr(cliente, "objetivo", "")
        kcal = getattr(cliente, "kcal_objetivo", 0)
        ctk.CTkLabel(
            self,
            text=f"Objetivo: {obj.upper()}   |   Kcal objetivo: {kcal:.0f}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.COLOR_SECONDARY,
        ).pack(pady=(0, 10))

        # ── Área scrolleable ──
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=self.COLOR_PRIMARY,
            scrollbar_button_hover_color=self.COLOR_PRIMARY_HOVER,
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        self._renderizar_preview(scroll, cliente, plan)

        # ── Botones ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(4, 16))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_frame, text="📄 Generar PDF",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=self.COLOR_PRIMARY, hover_color=self.COLOR_PRIMARY_HOVER,
            text_color="#FFFFFF", height=42, corner_radius=10,
            command=self._confirmar,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="✏️ Modificar",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color="transparent", hover_color="#2A2A2A",
            border_width=1, border_color="#444444",
            text_color=self.COLOR_TEXT_MUTED,
            height=42, corner_radius=10,
            command=self._cancelar,
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.protocol("WM_DELETE_WINDOW", self._cancelar)

    # ------------------------------------------------------------------
    def _renderizar_preview(self, parent, cliente, plan: dict) -> None:
        kcal_total = 0.0
        for clave in self.COMIDAS_ORDEN:
            if clave not in plan:
                continue
            comida = plan[clave]
            label  = self.COMIDAS_LABEL.get(clave, clave.capitalize())

            card = ctk.CTkFrame(
                parent, fg_color=self.COLOR_CARD,
                corner_radius=10, border_width=1, border_color="#444444",
            )
            card.pack(fill="x", pady=6)

            kcal_comida = comida.get("kcal_real", comida.get("kcal_objetivo", 0))
            kcal_total += kcal_comida

            ctk.CTkLabel(
                card,
                text=f"{label}  —  {kcal_comida:.0f} kcal",
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=self.COLOR_SECONDARY, anchor="w",
            ).pack(padx=14, pady=(10, 4), anchor="w")

            alimentos = comida.get("alimentos", {})
            for alimento, gramos in alimentos.items():
                nombre_fmt = alimento.replace("_", " ").title()
                row_frame = ctk.CTkFrame(card, fg_color="transparent")
                row_frame.pack(fill="x", padx=14, pady=1)

                ctk.CTkLabel(
                    row_frame,
                    text=f"  • {nombre_fmt}",
                    font=ctk.CTkFont(family="Consolas", size=11),
                    text_color="#CCCCCC", anchor="w",
                ).pack(side="left")

                equiv = self._equivalencia(alimento, gramos)
                ctk.CTkLabel(
                    row_frame,
                    text=f"{gramos:.0f} g{equiv}",
                    font=ctk.CTkFont(family="Consolas", size=11),
                    text_color=self.COLOR_TEXT_MUTED, anchor="e",
                ).pack(side="right")

            ctk.CTkFrame(card, height=1, fg_color="#333333").pack(
                fill="x", padx=14, pady=(6, 0))

            macros_text = self._macros_texto(comida)
            ctk.CTkLabel(
                card, text=macros_text,
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color="#666666", anchor="w",
            ).pack(padx=14, pady=(4, 10), anchor="w")

        # Total
        ctk.CTkLabel(
            parent,
            text=f"Total estimado: {kcal_total:.0f} kcal",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.COLOR_TEXT,
        ).pack(pady=(8, 4))

    @staticmethod
    def _macros_texto(comida: dict) -> str:
        p = comida.get("proteinas_g", 0)
        c = comida.get("carbohidratos_g", 0)
        g = comida.get("grasas_g", 0)
        if p or c or g:
            return f"P: {p:.0f}g   C: {c:.0f}g   G: {g:.0f}g"
        return ""

    @staticmethod
    def _equivalencia(alimento: str, gramos: float) -> str:
        """Devuelve texto de equivalencia fácil de leer (entre paréntesis)."""
        if alimento == "huevo":
            n = int(round(gramos / 50))
            if n >= 1:
                return f"  ({n} huevo{'s' if n > 1 else ''})"
        elif alimento == "tortilla_maiz":
            n = int(round(gramos / 30))
            if n >= 1:
                return f"  ({n} tortilla{'s' if n > 1 else ''})"
        elif alimento in ("aguacate",):
            n = round(gramos / 150, 1)
            if n >= 0.5:
                return f"  ({n} aguacate{'s' if n > 1 else ''})"
        elif alimento in ("banana", "platano"):
            n = int(round(gramos / 100))
            if n >= 1:
                return f"  ({n} plátano{'s' if n > 1 else ''})"
        return ""

    def _confirmar(self) -> None:
        self.destroy()
        self._on_confirm()

    def _cancelar(self) -> None:
        self.destroy()
        self._on_cancel()
