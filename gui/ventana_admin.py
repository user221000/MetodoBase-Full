# -*- coding: utf-8 -*-
"""
Panel de administración para configuración del sistema.

Permite:
- Editar branding del gym
- Ver estadísticas
- Backup de base de datos
- Búsqueda de clientes
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from typing import Dict

from core.branding import branding
from src.gestor_bd import GestorBDClientes
from gui.ventana_reportes import VentanaReportes
from utils.logger import logger


class VentanaAdmin(ctk.CTkToplevel):
    """
    Ventana de administración del sistema.

    Pestañas:
    1. Branding: Editar nombre, colores, contacto
    2. Base de Datos: Backups y estadísticas
    3. Búsqueda: Buscar y ver clientes

    Acceso: Ctrl+Shift+A en la ventana principal
    """

    COLOR_BG = "#0D0D0D"
    COLOR_CARD = "#1A1A1A"
    COLOR_PRIMARY = "#9B4FB0"
    COLOR_TEXT = "#F5F5F5"
    COLOR_TEXT_MUTED = "#B8B8B8"
    COLOR_SUCCESS = "#4CAF50"
    COLOR_ERROR = "#F44336"
    COLOR_WARNING = "#FF9800"

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Panel de Administración - Método Base")
        self.geometry("800x700")
        self.resizable(True, True)
        self.configure(fg_color=self.COLOR_BG)

        # Modal
        self.transient(parent)
        self.grab_set()

        # Gestores
        self.branding = branding
        self.gestor_bd = GestorBDClientes()

        self._crear_ui()

        logger.info("[ADMIN] Panel de administración abierto")

    def _crear_ui(self):
        """Crea la interfaz del panel."""
        # Header
        header = ctk.CTkFrame(self, fg_color=self.COLOR_CARD, height=80)
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="⚙️ Panel de Administración",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=self.COLOR_PRIMARY,
        ).pack(pady=10)

        ctk.CTkLabel(
            header,
            text="Configuración avanzada del sistema",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.COLOR_TEXT_MUTED,
        ).pack()

        # Tabview
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=self.COLOR_BG,
            segmented_button_fg_color=self.COLOR_CARD,
            segmented_button_selected_color=self.COLOR_PRIMARY,
            segmented_button_selected_hover_color=self.COLOR_PRIMARY,
            text_color=self.COLOR_TEXT,
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        tab_branding = self.tabview.add("🎨 Branding")
        tab_bd = self.tabview.add("💾 Base de Datos")
        tab_busqueda = self.tabview.add("🔍 Búsqueda")

        self._crear_tab_branding(tab_branding)
        self._crear_tab_bd(tab_bd)
        self._crear_tab_busqueda(tab_busqueda)

        # Botón cerrar
        ctk.CTkButton(
            self,
            text="Cerrar",
            command=self.destroy,
            width=120,
            height=36,
            fg_color="transparent",
            border_width=1,
            border_color=self.COLOR_TEXT_MUTED,
            hover_color=self.COLOR_CARD,
        ).pack(pady=(0, 20))

    # ========== Pestaña Branding ==========

    def _crear_tab_branding(self, parent):
        """Crea la pestaña de configuración de branding."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        self._crear_seccion_admin(scroll, "Información del Gimnasio")

        self.entry_nombre_gym = self._crear_campo_admin(
            scroll, "Nombre del Gym:", self.branding.get("nombre_gym")
        )
        self.entry_nombre_corto = self._crear_campo_admin(
            scroll, "Nombre Corto:", self.branding.get("nombre_corto")
        )
        self.entry_tagline = self._crear_campo_admin(
            scroll, "Tagline:", self.branding.get("tagline")
        )

        self._crear_seccion_admin(scroll, "Información de Contacto")

        self.entry_telefono = self._crear_campo_admin(
            scroll, "Teléfono:", self.branding.get("contacto.telefono", "")
        )
        self.entry_email = self._crear_campo_admin(
            scroll, "Email:", self.branding.get("contacto.email", "")
        )
        self.entry_direccion = self._crear_campo_admin(
            scroll, "Dirección:", self.branding.get("contacto.direccion", "")
        )
        self.entry_whatsapp = self._crear_campo_admin(
            scroll, "WhatsApp:", self.branding.get("contacto.whatsapp", "")
        )

        self._crear_seccion_admin(scroll, "Colores Corporativos")

        self.entry_color_primario = self._crear_campo_admin(
            scroll, "Color Primario (hex):", self.branding.get("colores.primario")
        )
        self.entry_color_secundario = self._crear_campo_admin(
            scroll, "Color Secundario (hex):", self.branding.get("colores.secundario")
        )

        ctk.CTkButton(
            scroll,
            text="💾 Guardar Configuración",
            command=self._guardar_branding,
            height=44,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.COLOR_SUCCESS,
            hover_color="#43A047",
        ).pack(pady=30, fill="x")

    # ========== Pestaña Base de Datos ==========

    def _crear_tab_bd(self, parent):
        """Crea la pestaña de gestión de base de datos."""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        stats = self.gestor_bd.obtener_estadisticas_gym()

        # Card de estadísticas
        card_stats = ctk.CTkFrame(container, fg_color=self.COLOR_CARD, corner_radius=10)
        card_stats.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card_stats,
            text="📊 Estadísticas del Gimnasio",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLOR_PRIMARY,
        ).pack(pady=(20, 15))

        stats_grid = ctk.CTkFrame(card_stats, fg_color="transparent")
        stats_grid.pack(fill="x", padx=20, pady=(0, 20))
        stats_grid.grid_columnconfigure((0, 1), weight=1)

        self._crear_stat_box(
            stats_grid, "👥 Total Clientes",
            str(stats.get("total_clientes", 0)), row=0, col=0,
        )
        self._crear_stat_box(
            stats_grid, "📈 Clientes Nuevos (30d)",
            str(stats.get("clientes_nuevos", 0)), row=0, col=1,
        )
        self._crear_stat_box(
            stats_grid, "🍽️ Planes Generados (30d)",
            str(stats.get("planes_periodo", 0)), row=1, col=0,
        )
        self._crear_stat_box(
            stats_grid, "⚡ Promedio Kcal",
            f"{stats.get('promedio_kcal', 0):.0f}", row=1, col=1,
        )

        # Card de backups
        card_backup = ctk.CTkFrame(container, fg_color=self.COLOR_CARD, corner_radius=10)
        card_backup.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            card_backup,
            text="💾 Gestión de Backups",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.COLOR_PRIMARY,
        ).pack(pady=(20, 15))

        ctk.CTkLabel(
            card_backup,
            text=(
                "Los backups se crean automáticamente cada 7 días.\n"
                "Puedes crear un backup manual en cualquier momento."
            ),
            font=ctk.CTkFont(size=11),
            text_color=self.COLOR_TEXT_MUTED,
            wraplength=600,
        ).pack(pady=(0, 15))

        btn_backup_frame = ctk.CTkFrame(card_backup, fg_color="transparent")
        btn_backup_frame.pack(fill="x", padx=20, pady=(0, 20))
        btn_backup_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_backup_frame,
            text="📦 Crear Backup",
            command=self._crear_backup,
            height=40,
            fg_color=self.COLOR_SUCCESS,
        ).grid(row=0, column=0, padx=(0, 10), sticky="ew")

        ctk.CTkButton(
            btn_backup_frame,
            text="🗑️ Limpiar Antiguos",
            command=self._limpiar_backups,
            height=40,
            fg_color=self.COLOR_WARNING,
        ).grid(row=0, column=1, padx=(10, 0), sticky="ew")

        # Botón de reportes completos
        ctk.CTkButton(
            container,
            text="📊 Ver Reportes Completos",
            command=lambda: VentanaReportes(self),
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.COLOR_PRIMARY,
        ).pack(pady=20, fill="x", padx=20)

    # ========== Pestaña Búsqueda ==========

    def _crear_tab_busqueda(self, parent):
        """Crea la pestaña de búsqueda de clientes."""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        search_frame = ctk.CTkFrame(container, fg_color=self.COLOR_CARD, corner_radius=10)
        search_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            search_frame,
            text="🔍 Buscar Cliente",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.COLOR_PRIMARY,
        ).pack(pady=(15, 10))

        entry_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        entry_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.entry_busqueda = ctk.CTkEntry(
            entry_frame,
            placeholder_text="Nombre, teléfono o ID del cliente...",
            height=40,
            font=ctk.CTkFont(size=13),
        )
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            entry_frame,
            text="Buscar",
            command=self._buscar_clientes,
            width=100,
            height=40,
            fg_color=self.COLOR_PRIMARY,
        ).pack(side="left")

        # Área de resultados
        self.resultados_frame = ctk.CTkScrollableFrame(
            container, fg_color=self.COLOR_BG, corner_radius=10
        )
        self.resultados_frame.pack(fill="both", expand=True)

    # ========== Métodos auxiliares ==========

    def _crear_seccion_admin(self, parent, titulo: str):
        """Crea un encabezado de sección."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(15, 10))

        ctk.CTkLabel(
            frame,
            text=titulo,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.COLOR_PRIMARY,
            anchor="w",
        ).pack(side="left")

        sep = ctk.CTkFrame(frame, fg_color=self.COLOR_PRIMARY, height=2)
        sep.pack(side="left", fill="x", expand=True, padx=(15, 0))

    def _crear_campo_admin(self, parent, label: str, valor_default: str) -> ctk.CTkEntry:
        """Crea un campo de entrada con label."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=self.COLOR_TEXT,
            anchor="w",
            width=150,
        ).pack(side="left", padx=(0, 10))

        entry = ctk.CTkEntry(frame, height=36, font=ctk.CTkFont(size=12))
        entry.pack(side="left", fill="x", expand=True)
        entry.insert(0, valor_default or "")

        return entry

    def _crear_info_label(self, parent, label: str, valor: str):
        """Crea una fila de información."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.COLOR_TEXT,
            anchor="w",
            width=180,
        ).pack(side="left")

        ctk.CTkLabel(
            frame,
            text=valor,
            font=ctk.CTkFont(size=11),
            text_color=self.COLOR_TEXT_MUTED,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

    def _crear_stat_box(self, parent, label: str, valor: str, row: int, col: int):
        """Crea una caja de estadística."""
        box = ctk.CTkFrame(parent, fg_color=self.COLOR_BG, corner_radius=8)
        box.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            box,
            text=valor,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.COLOR_PRIMARY,
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            box,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color=self.COLOR_TEXT_MUTED,
        ).pack(pady=(0, 15))

    # ========== Handlers ==========

    def _guardar_branding(self):
        """Guarda la configuración de branding."""
        try:
            self.branding.set("nombre_gym", self.entry_nombre_gym.get())
            self.branding.set("nombre_corto", self.entry_nombre_corto.get())
            self.branding.set("tagline", self.entry_tagline.get())
            self.branding.set("contacto.telefono", self.entry_telefono.get())
            self.branding.set("contacto.email", self.entry_email.get())
            self.branding.set("contacto.direccion", self.entry_direccion.get())
            self.branding.set("contacto.whatsapp", self.entry_whatsapp.get())
            self.branding.set("colores.primario", self.entry_color_primario.get())
            self.branding.set("colores.secundario", self.entry_color_secundario.get())

            messagebox.showinfo(
                "Éxito",
                "Configuración guardada exitosamente.\n\n"
                "Reinicia la aplicación para ver los cambios.",
            )
            logger.info("[ADMIN] Configuración de branding guardada")

        except Exception as e:
            logger.error("[ADMIN] Error guardando branding: %s", e, exc_info=True)
            messagebox.showerror("Error", f"No se pudo guardar la configuración:\n{e}")

    def _crear_backup(self):
        """Crea un backup manual de la BD."""
        try:
            ruta_backup = self.gestor_bd.crear_backup()

            if ruta_backup:
                messagebox.showinfo(
                    "Backup Creado",
                    f"Backup creado exitosamente:\n\n{ruta_backup}",
                )
            else:
                messagebox.showerror("Error", "No se pudo crear el backup")

        except Exception as e:
            logger.error("[ADMIN] Error creando backup: %s", e, exc_info=True)
            messagebox.showerror("Error", f"Error creando backup:\n{e}")

    def _limpiar_backups(self):
        """Limpia backups antiguos (>90 días)."""
        respuesta = messagebox.askyesno(
            "Confirmar",
            "¿Deseas eliminar backups con más de 90 días de antigüedad?\n\n"
            "Los backups recientes se mantendrán intactos.",
        )

        if respuesta:
            try:
                eliminados = self.gestor_bd.limpiar_backups_antiguos(90)
                messagebox.showinfo(
                    "Limpieza Completada",
                    f"Se eliminaron {eliminados} backups antiguos.",
                )

            except Exception as e:
                logger.error("[ADMIN] Error limpiando backups: %s", e, exc_info=True)
                messagebox.showerror("Error", f"Error limpiando backups:\n{e}")

    def _buscar_clientes(self):
        """Busca clientes y muestra resultados."""
        termino = self.entry_busqueda.get().strip()

        if not termino:
            messagebox.showwarning("Aviso", "Ingresa un término de búsqueda")
            return

        try:
            # Limpiar resultados anteriores
            for widget in self.resultados_frame.winfo_children():
                widget.destroy()

            resultados = self.gestor_bd.buscar_clientes(termino, limite=50)

            if not resultados:
                ctk.CTkLabel(
                    self.resultados_frame,
                    text="No se encontraron resultados",
                    font=ctk.CTkFont(size=13),
                    text_color=self.COLOR_TEXT_MUTED,
                ).pack(pady=40)
                return

            for cliente in resultados:
                self._crear_card_cliente(self.resultados_frame, cliente)

            logger.info("[ADMIN] Búsqueda '%s': %s resultados", termino, len(resultados))

        except Exception as e:
            logger.error("[ADMIN] Error en búsqueda: %s", e, exc_info=True)
            messagebox.showerror("Error", f"Error buscando clientes:\n{e}")

    def _crear_card_cliente(self, parent, cliente: Dict):
        """Crea una tarjeta con información de un cliente."""
        card = ctk.CTkFrame(parent, fg_color=self.COLOR_CARD, corner_radius=10)
        card.pack(fill="x", pady=10, padx=10)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            header,
            text=cliente["nombre"],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.COLOR_TEXT,
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"{cliente['total_planes']} planes",
            font=ctk.CTkFont(size=11),
            text_color=self.COLOR_PRIMARY,
            anchor="e",
        ).pack(side="right")

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 15))

        info_text = []
        if cliente["telefono"]:
            info_text.append(f"📱 {cliente['telefono']}")
        if cliente["edad"]:
            info_text.append(f"👤 {cliente['edad']} años")
        if cliente["objetivo"]:
            info_text.append(f"🎯 {cliente['objetivo'].title()}")

        ctk.CTkLabel(
            info_frame,
            text=" | ".join(info_text),
            font=ctk.CTkFont(size=11),
            text_color=self.COLOR_TEXT_MUTED,
            anchor="w",
        ).pack()
