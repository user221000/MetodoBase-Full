"""Interfaz gráfica CustomTkinter para Método Base."""
import os
import re
import threading
import webbrowser
import urllib.parse
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageFilter, ImageEnhance

from utils.helpers import resource_path, abrir_carpeta_pdf
from config.constantes import (
    FACTORES_ACTIVIDAD, NIVELES_ACTIVIDAD, OBJETIVOS_VALIDOS, CARPETA_SALIDA,
)
from core.modelos import ClienteEvaluacion
from core.motor_nutricional import MotorNutricional
from core.generador_planes import ConstructorPlanNuevo
from core.exportador_salida import GeneradorPDFProfesional


# ─────────────────────────────────────────────
# Validación de campos en tiempo real
# ─────────────────────────────────────────────

from gui.validadores import ValidadorCamposTiempoReal  # noqa: E402

# ─────────────────────────────────────────────
# Widget de progreso de generación
# ─────────────────────────────────────────────

class ProgressIndicator(ctk.CTkFrame):
    """Barra de progreso + etiqueta de estado para la generación del plan."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#1E1E1E", corner_radius=10,
                         border_width=1, border_color="#444444", **kwargs)

        self.lbl_estado = ctk.CTkLabel(
            self, text="Iniciando…", anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#888888",
        )
        self.lbl_estado.pack(padx=16, pady=(10, 4), anchor="w")

        self.barra = ctk.CTkProgressBar(self, mode="determinate", height=10,
                                        corner_radius=5, progress_color="#7B2D8E")
        self.barra.set(0)
        self.barra.pack(fill="x", padx=16, pady=(0, 10))

    def set_progress(self, value: float, status: str = "") -> None:
        """``value`` es 0.0 – 1.0."""
        self.barra.set(max(0.0, min(1.0, value)))
        if status:
            self.lbl_estado.configure(text=status)

    def complete(self, status: str = "✓ Listo") -> None:
        self.barra.set(1.0)
        self.barra.configure(progress_color="#2B5B2B")
        self.lbl_estado.configure(text=status, text_color="#3D7A3D")

    def reset(self) -> None:
        self.barra.set(0)
        self.barra.configure(progress_color="#7B2D8E")
        self.lbl_estado.configure(text="Iniciando…", text_color="#888888")



class PlanPreviewWindow(ctk.CTkToplevel):
    """Ventana modal que muestra el resumen del plan antes de generar el PDF."""

    COMIDAS_ORDEN = ["desayuno", "almuerzo", "comida", "cena"]
    COMIDAS_LABEL = {
        "desayuno": "🌅 Desayuno",
        "almuerzo": "☀️ Almuerzo",
        "comida":   "🍽  Comida",
        "cena":     "🌙 Cena",
    }

    def __init__(self, parent, cliente, plan, on_confirm, on_cancel):
        super().__init__(parent)
        self.title("Vista Previa del Plan")
        self.geometry("680x780")
        self.resizable(False, True)
        self.configure(fg_color="#121212")
        self.grab_set()          # modal
        self.focus()

        self._on_confirm = on_confirm
        self._on_cancel = on_cancel

        # ── Título ──
        ctk.CTkLabel(
            self, text=f"Plan para {cliente.nombre}",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF",
        ).pack(pady=(18, 2))

        obj = getattr(cliente, "objetivo", "")
        kcal = getattr(cliente, "kcal_objetivo", 0)
        ctk.CTkLabel(
            self, text=f"Objetivo: {obj.upper()}   |   Kcal objetivo: {kcal:.0f}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#D4A84B",
        ).pack(pady=(0, 10))

        # ── Área scrolleable ──
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color="#7B2D8E",
            scrollbar_button_hover_color="#9B3DB0",
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
            fg_color="#7B2D8E", hover_color="#9B3DB0", text_color="#FFFFFF",
            height=42, corner_radius=10, command=self._confirmar,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="✏️ Modificar",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color="transparent", hover_color="#2A2A2A",
            border_width=1, border_color="#444444", text_color="#888888",
            height=42, corner_radius=10, command=self._cancelar,
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.protocol("WM_DELETE_WINDOW", self._cancelar)

    def _renderizar_preview(self, parent, cliente, plan):
        kcal_total = 0.0
        for clave in self.COMIDAS_ORDEN:
            if clave not in plan:
                continue
            comida = plan[clave]
            label = self.COMIDAS_LABEL.get(clave, clave.capitalize())

            card = ctk.CTkFrame(parent, fg_color="#1E1E1E", corner_radius=10,
                                border_width=1, border_color="#444444")
            card.pack(fill="x", pady=6)

            kcal_comida = comida.get("kcal_real", comida.get("kcal_objetivo", 0))
            kcal_total += kcal_comida

            ctk.CTkLabel(
                card,
                text=f"{label}  —  {kcal_comida:.0f} kcal",
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color="#D4A84B", anchor="w",
            ).pack(padx=14, pady=(10, 4), anchor="w")

            alimentos = comida.get("alimentos", {})
            for alimento, gramos in alimentos.items():
                nombre_fmt = alimento.replace("_", " ").title()
                ctk.CTkLabel(
                    card,
                    text=f"  • {nombre_fmt}:  {gramos:.0f} g",
                    font=ctk.CTkFont(family="Consolas", size=11),
                    text_color="#CCCCCC", anchor="w",
                ).pack(padx=14, pady=1, anchor="w")

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
            text_color="#FFFFFF",
        ).pack(pady=(8, 4))

    @staticmethod
    def _macros_texto(comida: dict) -> str:
        p = comida.get("proteinas_g", 0)
        c = comida.get("carbohidratos_g", 0)
        g = comida.get("grasas_g", 0)
        if p or c or g:
            return f"P: {p:.0f}g   C: {c:.0f}g   G: {g:.0f}g"
        return ""

    def _confirmar(self):
        self.destroy()
        self._on_confirm()

    def _cancelar(self):
        self.destroy()
        self._on_cancel()


class GymApp(ctk.CTk):
    """Aplicacion principal con CustomTkinter - Diseño profesional moderno."""
    
    # Paleta de colores
    COLOR_BG = "#121212"
    COLOR_CARD = "#1E1E1E"
    COLOR_PRIMARY = "#7B2D8E"
    COLOR_PRIMARY_HOVER = "#9B3DB0"
    COLOR_SECONDARY = "#D4A84B"
    COLOR_SECONDARY_HOVER = "#E4B85B"
    COLOR_BORDER = "#444444"
    COLOR_TEXT = "#FFFFFF"
    COLOR_TEXT_MUTED = "#888888"
    COLOR_INPUT_BG = "#2A2A2A"
    COLOR_SUCCESS = "#2B5B2B"
    COLOR_SUCCESS_HOVER = "#3D7A3D"
    COLOR_ERROR = "#B22222"
    
    def __init__(self):
        super().__init__()

        self.title("Método Base - Consultoría Hernández")
        self.geometry("820x900")
        self.resizable(False, False)
        self.configure(fg_color=self.COLOR_BG)
        ctk.set_appearance_mode("Dark")
        
        self.ultimo_pdf = None
        self.ultima_ruta_pdf = None
        
        # Contenedor principal con scroll
        self.main_container = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=self.COLOR_PRIMARY,
            scrollbar_button_hover_color=self.COLOR_PRIMARY_HOVER
        )
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # ═══════════════ HEADER / BRANDING ═══════════════
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(20, 4))
        
        self.title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_container.pack()
        
        self._crear_header_watermark(self.title_container)
        
        self.lbl_titulo = ctk.CTkLabel(
            self.title_container, text="Metodo Base",
            font=ctk.CTkFont(family="Segoe UI", size=42, weight="bold"),
            text_color=self.COLOR_TEXT
        )
        self.lbl_titulo.pack(pady=(0, 2))

        self.lbl_subtitulo = ctk.CTkLabel(
            self.header_frame, text="Fitness Gym Real del Valle",
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color=self.COLOR_SECONDARY
        )
        self.lbl_subtitulo.pack(pady=(0, 4))

        self.lbl_contexto = ctk.CTkLabel(
            self.header_frame, text="Powered by C. H.",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.COLOR_TEXT_MUTED
        )
        self.lbl_contexto.pack(pady=(0, 10))
        
        self.separator = ctk.CTkFrame(self.main_container, height=2, fg_color=self.COLOR_PRIMARY)
        self.separator.pack(fill="x", padx=60, pady=(0, 12))

        # ═══════════════ SECCIÓN 1: DATOS DEL CLIENTE ═══════════════
        self.section_cliente = self._crear_seccion("Datos del Cliente", "👤")
        
        self.entry_nombre, self.lbl_error_nombre = self._crear_input_full(
            self.section_cliente, "Nombre completo", "Ej: Oscar Hernández", row=0
        )

        self.entry_telefono, self.entry_edad, self.lbl_error_telefono, self.lbl_error_edad = self._crear_input_duo(
            self.section_cliente,
            "Teléfono", "Ej: 5213312345678",
            "Edad", "Ej: 25", row=1
        )

        # ═══════════════ SECCIÓN 2: MEDIDAS CORPORALES ═══════════════
        self.section_medidas = self._crear_seccion("Medidas Corporales", "⚖")
        
        self.entry_peso, self.entry_estatura, self.lbl_error_peso, self.lbl_error_estatura = self._crear_input_duo(
            self.section_medidas,
            "Peso (kg)", "Ej: 80.5",
            "Estatura (cm)", "Ej: 175", row=0
        )

        self.entry_grasa, self.lbl_error_grasa = self._crear_input_full(
            self.section_medidas, "Grasa corporal (%)", "Ej: 18", row=1
        )

        # ═══════════════ SECCIÓN 3: PERFIL DE ENTRENAMIENTO ═══════════════
        self.section_perfil = self._crear_seccion("Perfil de Entrenamiento", "🏋")
        
        self.combo_actividad, self.combo_objetivo = self._crear_combo_duo(
            self.section_perfil,
            "Actividad", list(NIVELES_ACTIVIDAD), "moderada",
            "Objetivo", list(OBJETIVOS_VALIDOS), "mantenimiento", row=0
        )

        # ─── Bindings de validación en tiempo real ───
        self.entry_nombre.bind("<KeyRelease>", lambda e: self._validar_campo(
            self.entry_nombre, self.lbl_error_nombre, ValidadorCamposTiempoReal.validar_nombre))
        self.entry_telefono.bind("<KeyRelease>", lambda e: self._validar_campo(
            self.entry_telefono, self.lbl_error_telefono, ValidadorCamposTiempoReal.validar_telefono))
        self.entry_edad.bind("<KeyRelease>", lambda e: self._validar_campo(
            self.entry_edad, self.lbl_error_edad, ValidadorCamposTiempoReal.validar_edad))
        self.entry_peso.bind("<KeyRelease>", lambda e: self._validar_campo(
            self.entry_peso, self.lbl_error_peso, ValidadorCamposTiempoReal.validar_peso))
        self.entry_estatura.bind("<KeyRelease>", lambda e: self._validar_campo(
            self.entry_estatura, self.lbl_error_estatura, ValidadorCamposTiempoReal.validar_estatura))
        self.entry_grasa.bind("<KeyRelease>", lambda e: self._validar_campo(
            self.entry_grasa, self.lbl_error_grasa, ValidadorCamposTiempoReal.validar_grasa))
        self.buttons_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.buttons_frame.pack(fill="x", padx=40, pady=(20, 12))
        
        self.btn_shadow = ctk.CTkFrame(
            self.buttons_frame, fg_color="#5a1e6a",
            corner_radius=12, height=68,
        )
        self.btn_shadow.pack(fill="x", pady=(0, 18), ipady=0)
        self.btn_shadow.pack_propagate(False)

        self.btn_procesar = ctk.CTkButton(
            self.btn_shadow, text="GENERAR PLAN Y PDF",
            command=self._on_procesar_click, height=60, corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=19, weight="bold"),
            fg_color=self.COLOR_PRIMARY, hover_color=self.COLOR_PRIMARY_HOVER,
            border_width=2, border_color=self.COLOR_PRIMARY_HOVER,
            text_color=self.COLOR_TEXT
        )
        self.btn_procesar.pack(fill="x", padx=2, pady=2, ipady=2)
        
        self.secondary_buttons = ctk.CTkFrame(self.buttons_frame, fg_color="transparent")
        self.secondary_buttons.pack(fill="x")
        self.secondary_buttons.grid_columnconfigure(0, weight=1)
        self.secondary_buttons.grid_columnconfigure(1, weight=1)

        self.btn_whatsapp = ctk.CTkButton(
            self.secondary_buttons, text="Enviar por WhatsApp",
            command=self.enviar_por_whatsapp, state="disabled",
            height=36, corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.COLOR_SUCCESS, hover_color=self.COLOR_SUCCESS_HOVER,
            border_width=1, border_color=self.COLOR_SUCCESS_HOVER,
            text_color=self.COLOR_TEXT
        )
        self.btn_whatsapp.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=0)

        self.btn_abrir_pdf = ctk.CTkButton(
            self.secondary_buttons, text="Abrir carpeta de PDF",
            command=abrir_carpeta_pdf, height=36, corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent", hover_color=self.COLOR_CARD,
            border_width=1, border_color=self.COLOR_BORDER,
            text_color=self.COLOR_TEXT_MUTED
        )
        self.btn_abrir_pdf.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=0)

        # ═══════════════ PROGRESO ═══════════════
        self.progress_indicator = ProgressIndicator(self.main_container)
        self.progress_indicator.pack(fill="x", padx=40, pady=(0, 8))
        self.progress_indicator.pack_forget()  # oculto hasta que se genere

        # ═══════════════ REGISTRO DE OPERACIONES ═══════════════
        self.log_frame = ctk.CTkFrame(
            self.main_container, fg_color=self.COLOR_CARD,
            corner_radius=10, border_width=1, border_color=self.COLOR_BORDER
        )
        self.log_frame.pack(fill="x", padx=40, pady=(16, 24))
        
        self.lbl_status = ctk.CTkLabel(
            self.log_frame, text="Registro de Operaciones", anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.COLOR_TEXT_MUTED
        )
        self.lbl_status.pack(padx=16, pady=(12, 4), anchor="w")
        
        self.textbox_log = ctk.CTkTextbox(
            self.log_frame, height=100, corner_radius=6,
            fg_color=self.COLOR_INPUT_BG, border_width=0,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=self.COLOR_TEXT_MUTED
        )
        self.textbox_log.pack(padx=12, pady=(0, 12), fill="x")
        
        self._log("Sistema listo. Esperando datos del cliente...")

    # ───── Helpers de creación de UI ─────

    def _crear_seccion(self, titulo, icono=""):
        card = ctk.CTkFrame(
            self.main_container, fg_color=self.COLOR_CARD,
            corner_radius=12, border_width=1, border_color=self.COLOR_BORDER
        )
        card.pack(fill="x", padx=40, pady=8)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        
        if icono:
            lbl_icono = ctk.CTkLabel(
                header, text=icono,
                font=ctk.CTkFont(family="Segoe UI", size=14),
                text_color=self.COLOR_PRIMARY, anchor="w"
            )
            lbl_icono.pack(side="left", padx=(0, 8))
        
        lbl_titulo = ctk.CTkLabel(
            header, text=titulo,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.COLOR_SECONDARY, anchor="w"
        )
        lbl_titulo.pack(side="left")
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=8, pady=(0, 12))
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(2, weight=1)
        content.grid_columnconfigure(3, weight=1)
        
        return content
    
    def _crear_label_campo(self, parent, texto, fila, col=0):
        label = ctk.CTkLabel(
            parent, text=texto,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.COLOR_TEXT, anchor="w"
        )
        label.grid(row=fila, column=col, columnspan=2, padx=(16, 4), pady=(8, 2), sticky="w")
        return label
    
    def _crear_input_full(self, parent, label_text, placeholder, row):
        base_row = row * 3
        self._crear_label_campo(parent, label_text, base_row, col=0)

        entry = ctk.CTkEntry(
            parent, placeholder_text=placeholder, height=38, corner_radius=8,
            border_width=1, border_color=self.COLOR_BORDER,
            fg_color=self.COLOR_INPUT_BG,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            placeholder_text_color=self.COLOR_TEXT_MUTED
        )
        entry.grid(row=base_row + 1, column=0, columnspan=4, padx=16, pady=(0, 2), sticky="ew")

        lbl_error = ctk.CTkLabel(
            parent, text="", anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.COLOR_ERROR,
        )
        lbl_error.grid(row=base_row + 2, column=0, columnspan=4, padx=20, pady=(0, 6), sticky="w")

        return entry, lbl_error
    
    def _crear_input_duo(self, parent, label1, placeholder1, label2, placeholder2, row):
        base_row = row * 3

        lbl1 = ctk.CTkLabel(parent, text=label1, font=ctk.CTkFont(family="Segoe UI", size=12),
                           text_color=self.COLOR_TEXT, anchor="w")
        lbl1.grid(row=base_row, column=0, columnspan=2, padx=(16, 4), pady=(8, 2), sticky="w")

        lbl2 = ctk.CTkLabel(parent, text=label2, font=ctk.CTkFont(family="Segoe UI", size=12),
                           text_color=self.COLOR_TEXT, anchor="w")
        lbl2.grid(row=base_row, column=2, columnspan=2, padx=(16, 4), pady=(8, 2), sticky="w")

        entry1 = ctk.CTkEntry(
            parent, placeholder_text=placeholder1, height=38, corner_radius=8,
            border_width=1, border_color=self.COLOR_BORDER,
            fg_color=self.COLOR_INPUT_BG,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            placeholder_text_color=self.COLOR_TEXT_MUTED
        )
        entry1.grid(row=base_row + 1, column=0, columnspan=2, padx=(16, 8), pady=(0, 2), sticky="ew")

        entry2 = ctk.CTkEntry(
            parent, placeholder_text=placeholder2, height=38, corner_radius=8,
            border_width=1, border_color=self.COLOR_BORDER,
            fg_color=self.COLOR_INPUT_BG,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            placeholder_text_color=self.COLOR_TEXT_MUTED
        )
        entry2.grid(row=base_row + 1, column=2, columnspan=2, padx=(8, 16), pady=(0, 2), sticky="ew")

        lbl_error1 = ctk.CTkLabel(
            parent, text="", anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.COLOR_ERROR,
        )
        lbl_error1.grid(row=base_row + 2, column=0, columnspan=2, padx=(20, 4), pady=(0, 6), sticky="w")

        lbl_error2 = ctk.CTkLabel(
            parent, text="", anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.COLOR_ERROR,
        )
        lbl_error2.grid(row=base_row + 2, column=2, columnspan=2, padx=(20, 16), pady=(0, 6), sticky="w")

        return entry1, entry2, lbl_error1, lbl_error2
    
    def _crear_combo_duo(self, parent, label1, values1, default1, label2, values2, default2, row):
        base_row = row * 2
        
        lbl1 = ctk.CTkLabel(parent, text=label1, font=ctk.CTkFont(family="Segoe UI", size=12),
                           text_color=self.COLOR_TEXT, anchor="w")
        lbl1.grid(row=base_row, column=0, columnspan=2, padx=(16, 4), pady=(8, 2), sticky="w")
        
        lbl2 = ctk.CTkLabel(parent, text=label2, font=ctk.CTkFont(family="Segoe UI", size=12),
                           text_color=self.COLOR_TEXT, anchor="w")
        lbl2.grid(row=base_row, column=2, columnspan=2, padx=(16, 4), pady=(8, 2), sticky="w")
        
        combo1 = ctk.CTkComboBox(
            parent, values=values1, height=38, corner_radius=8,
            border_width=1, border_color=self.COLOR_BORDER,
            button_color=self.COLOR_PRIMARY, button_hover_color=self.COLOR_PRIMARY_HOVER,
            dropdown_fg_color=self.COLOR_CARD, dropdown_hover_color=self.COLOR_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        combo1.grid(row=base_row + 1, column=0, columnspan=2, padx=(16, 8), pady=(0, 8), sticky="ew")
        combo1.set(default1)
        
        combo2 = ctk.CTkComboBox(
            parent, values=values2, height=38, corner_radius=8,
            border_width=1, border_color=self.COLOR_BORDER,
            button_color=self.COLOR_PRIMARY, button_hover_color=self.COLOR_PRIMARY_HOVER,
            dropdown_fg_color=self.COLOR_CARD, dropdown_hover_color=self.COLOR_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        combo2.grid(row=base_row + 1, column=2, columnspan=2, padx=(8, 16), pady=(0, 8), sticky="ew")
        combo2.set(default2)
        
        return combo1, combo2

    def _crear_header_watermark(self, parent):
        try:
            logo_path = resource_path("assets/logo.png")
            if not os.path.exists(logo_path):
                return
            
            logo_img = Image.open(logo_path)
            watermark_size = 120
            logo_img = logo_img.resize((watermark_size, watermark_size), Image.Resampling.LANCZOS)
            logo_img = logo_img.filter(ImageFilter.GaussianBlur(radius=1.5))
            
            if logo_img.mode == 'RGBA':
                alpha = logo_img.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(0.07)
                logo_img.putalpha(alpha)
            else:
                logo_img = logo_img.convert('RGBA')
                alpha = logo_img.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(0.07)
                logo_img.putalpha(alpha)
            
            self.header_watermark_photo = ImageTk.PhotoImage(logo_img)
            
            from tkinter import Label
            self.header_watermark_label = Label(
                parent._canvas if hasattr(parent, '_canvas') else parent,
                image=self.header_watermark_photo,
                bg=self.COLOR_BG, borderwidth=0
            )
            self.header_watermark_label.place(relx=0.5, rely=0.5, anchor="center")
        except Exception:
            pass

    # ───── Lógica de negocio ─────

    def _validar_campo(self, entry, lbl_error, validador_fn):
        """Actualiza el borde y la etiqueta de error de un campo en tiempo real."""
        valor = entry.get()
        ok, mensaje = validador_fn(valor)
        if ok:
            entry.configure(border_color=self.COLOR_BORDER)
            lbl_error.configure(text="")
        else:
            entry.configure(border_color=self.COLOR_ERROR)
            lbl_error.configure(text=mensaje)

    def _log(self, mensaje):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.textbox_log.insert("end", f"[{timestamp}] {mensaje}\n")
        self.textbox_log.see("end")

    def _on_procesar_click(self):
        self.btn_procesar.configure(state="disabled")
        self._show_spinner_on_button()
        self.progress_indicator.reset()
        self.progress_indicator.pack(fill="x", padx=40, pady=(0, 8),
                                     before=self.log_frame)
        thread = threading.Thread(target=self._procesar_datos, daemon=True)
        thread.start()

    def _procesar_datos(self):
        try:
            self._log("Iniciando procesamiento...")
            self.after(0, lambda: self.progress_indicator.set_progress(0.05, "Validando datos…"))

            nombre = self.entry_nombre.get().strip()
            if not nombre:
                raise ValueError("El nombre es obligatorio")
            telefono = self.entry_telefono.get().strip()
            if telefono:
                if not telefono.isdigit():
                    raise ValueError("Telefono invalido: solo numeros, sin espacios ni simbolos")
                if len(telefono) < 10:
                    raise ValueError("Telefono invalido: debe tener al menos 10 digitos")
            edad = int(self.entry_edad.get())
            if edad < 1:
                raise ValueError("Edad invalida: debe ser mayor a 0 anos")
            peso = float(self.entry_peso.get())
            if peso < 20:
                raise ValueError("Peso invalido: el peso minimo permitido es 20 kg")
            if peso > 155:
                raise ValueError("Peso invalido: el peso maximo permitido es 155 kg")
            estatura = float(self.entry_estatura.get())
            grasa = float(self.entry_grasa.get())
            if grasa < 5:
                raise ValueError("Grasa corporal invalida: el porcentaje minimo permitido es 5%")
            actividad = self.combo_actividad.get()
            objetivo = self.combo_objetivo.get()

            self.after(0, lambda: self.progress_indicator.set_progress(0.2, "Calculando metabolismo…"))

            cliente = ClienteEvaluacion(
                nombre=nombre,
                telefono=telefono if telefono else None,
                edad=edad, peso_kg=peso, estatura_cm=estatura,
                grasa_corporal_pct=grasa, nivel_actividad=actividad,
                objetivo=objetivo
            )
            cliente.factor_actividad = FACTORES_ACTIVIDAD.get(actividad, 1.2)
            self._log(f"Cliente creado: {cliente.nombre} ({cliente.objetivo})")

            cliente = MotorNutricional.calcular_motor(cliente)
            self._log(f"TMB={cliente.tmb:.0f}, GET={cliente.get_total:.0f}, Kcal={cliente.kcal_objetivo:.0f}")
            self.after(0, lambda: self.progress_indicator.set_progress(0.45, "Construyendo plan alimenticio…"))

            dir_planes = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "planes")
            os.makedirs(dir_planes, exist_ok=True)
            plan = ConstructorPlanNuevo.construir(cliente, plan_numero=1, directorio_planes=dir_planes)
            self._log("Plan nutricional estructurado correctamente.")
            self.after(0, lambda: self.progress_indicator.set_progress(0.65, "Mostrando vista previa…"))

            # ── Vista previa: bloquear hilo hasta confirmación ──
            confirm_event = threading.Event()
            self._preview_confirmed = False

            def on_confirm():
                self._preview_confirmed = True
                confirm_event.set()

            def on_cancel():
                self._preview_confirmed = False
                confirm_event.set()

            self.after(0, lambda: PlanPreviewWindow(self, cliente, plan, on_confirm, on_cancel))
            confirm_event.wait()

            if not self._preview_confirmed:
                self._log("Generación cancelada por el usuario.")
                return

            self.after(0, lambda: self.progress_indicator.set_progress(0.80, "Generando PDF…"))

            if not os.path.exists(CARPETA_SALIDA):
                os.makedirs(CARPETA_SALIDA)
            fecha = datetime.now().strftime("%Y-%m-%d")
            nombre_cliente_sanitizado = re.sub(r'[^a-zA-Z0-9_]', '', cliente.nombre.replace(" ", "_"))
            carpeta_cliente = os.path.join(CARPETA_SALIDA, nombre_cliente_sanitizado)
            os.makedirs(carpeta_cliente, exist_ok=True)
            hora = datetime.now().strftime("%H-%M-%S")
            nombre_pdf = f"{nombre_cliente_sanitizado}_{fecha}_{hora}.pdf"
            ruta_pdf_completa = os.path.join(carpeta_cliente, nombre_pdf)

            generador = GeneradorPDFProfesional(ruta_pdf_completa)
            ruta_pdf = generador.generar(cliente, plan)
            self.ultimo_pdf = ruta_pdf if ruta_pdf and os.path.exists(ruta_pdf) else None

            self.after(0, lambda: self.btn_abrir_pdf.configure(state="normal" if self.ultimo_pdf else "disabled"))
            self.after(0, lambda: self.btn_whatsapp.configure(state="normal" if self.ultimo_pdf else "disabled"))
            self.after(0, lambda: self.progress_indicator.complete("✓ Plan generado y PDF listo"))

            if self.ultimo_pdf:
                try:
                    os.startfile(self.ultimo_pdf)
                    self._log("PDF abierto automaticamente.")
                except Exception as e:
                    self._log(f"No se pudo abrir el PDF: {e}")

            comidas = ['desayuno', 'almuerzo', 'comida', 'cena']
            kcal_real = sum(plan[c].get('kcal_real', 0) for c in comidas if c in plan)
            desv_max = max(plan[c].get('desviacion_pct', 0) for c in comidas if c in plan)

            self._log(f"PLAN GENERADO — {nombre} | {objetivo.upper()} | "
                      f"Kcal obj: {cliente.kcal_objetivo:.0f} | "
                      f"Kcal real: {kcal_real:.0f} | Desv. máx: {desv_max:.2f}%")
            self._log(f"PDF: {ruta_pdf}")

        except ValueError as ve:
            self._log(f"Error de validacion: {ve}")
            self.after(0, lambda: messagebox.showerror(
                "Error de Validación", f"Por favor verifica los datos.\nDetalle: {ve}"))
        except Exception as e:
            self._log(f"ERROR: {str(e)}")
            self.after(0, lambda: messagebox.showerror("Error", f"Ocurrio un error:\n{str(e)}"))
            import traceback
            traceback.print_exc()
        finally:
            self.after(0, self._hide_spinner_on_button)
            self.after(0, lambda: self.btn_procesar.configure(state="normal", text="GENERAR PLAN Y PDF"))

    def _show_spinner_on_button(self):
        try:
            spinner_path = resource_path("assets/spinner_dark.gif")
            if not os.path.exists(spinner_path):
                self.btn_procesar.configure(text="Generando plan...", image=None)
                return
            self.spinner_img = Image.open(spinner_path)
            self.spinner_frames = []
            try:
                while True:
                    self.spinner_frames.append(ImageTk.PhotoImage(self.spinner_img.copy()))
                    self.spinner_img.seek(len(self.spinner_frames))
            except EOFError:
                pass
            self._spinner_frame = 0
            self._spinner_running = True
            self._animate_spinner()
        except Exception:
            self.btn_procesar.configure(text="Generando plan...", image=None)

    def _animate_spinner(self):
        if not getattr(self, '_spinner_running', False):
            return
        frame = self.spinner_frames[self._spinner_frame]
        self.btn_procesar.configure(text="Generando plan...", image=frame, compound="left")
        self._spinner_frame = (self._spinner_frame + 1) % len(self.spinner_frames)
        self.after(60, self._animate_spinner)

    def _hide_spinner_on_button(self):
        self._spinner_running = False
        self.btn_procesar.configure(text="GENERAR PLAN Y PDF", image=None)

    def _abrir_pdf(self):
        if self.ultimo_pdf and os.path.exists(self.ultimo_pdf):
            try:
                os.startfile(self.ultimo_pdf)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el PDF: {e}")
        else:
            messagebox.showwarning("Aviso", "No hay PDF disponible para abrir.")

    def abrir_carpeta_pdf(self):
        if not os.path.exists(CARPETA_SALIDA):
            os.makedirs(CARPETA_SALIDA)
        os.startfile(CARPETA_SALIDA)

    def enviar_por_whatsapp(self):
        if not self.ultimo_pdf or not os.path.exists(self.ultimo_pdf):
            messagebox.showerror("Error", "Primero debes generar el plan.")
            return
        telefono = self.entry_telefono.get().strip()
        if not telefono.isdigit():
            messagebox.showerror("Error", "Teléfono inválido.")
            return
        if not telefono.startswith("52"):
            messagebox.showerror("Error", "El número debe iniciar con 52 (México).")
            return
        nombre = self.entry_nombre.get().strip()

        mensaje = f"""
    Hola {nombre} 👋

    Tu plan personalizado de FitnessGym Real Del Valle ya está listo.
    Adjunto encontrarás tu plan alimenticio.
    Cualquier duda puedes consultarla directamente con tu entrenador de piso en recepción.
    FitnessGym Real Del Valle agradece tu preferencia y te espera el próximo mes con tu plan actualizado.
    """

        mensaje_codificado = urllib.parse.quote(mensaje)
        url = f"https://wa.me/{telefono}?text={mensaje_codificado}"
        webbrowser.open(url)
        
        messagebox.showinfo(
            "WhatsApp",
            "WhatsApp Web abierto. Adjunta el PDF manualmente y envía."
        )
