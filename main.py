"""
Método Base - Punto de entrada principal.
Sistema de generación de planes nutricionales personalizados.
"""

# === SETUP DE PATHS ===
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# === SPLASH SCREEN DE CARGA (no bloqueante) ===
import tkinter as tk

splash = tk.Tk()
splash.title("Método Base")
splash.geometry("400x200")
splash.configure(bg="#0D0D0D")
splash.overrideredirect(True)   # sin barra de título
splash.update_idletasks()
sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
splash.geometry(f"400x200+{(sw-400)//2}+{(sh-200)//2}")

tk.Label(splash, text="🏋️ Método Base", bg="#0D0D0D", fg="#9B4FB0",
         font=("Segoe UI", 20, "bold")).pack(expand=True)
tk.Label(splash, text="Sistema de Planes Nutricionales", bg="#0D0D0D", fg="#B8B8B8",
         font=("Segoe UI", 11)).pack(pady=(0, 30))

bar_canvas = tk.Canvas(splash, width=200, height=6, bg="#2A2A2A",
                       highlightthickness=0)
bar_canvas.pack(pady=(0, 20))
bar_rect = bar_canvas.create_rectangle(0, 0, 0, 6, fill="#9B4FB0", outline="")

_splash_step = [0]

def _animar_splash():
    _splash_step[0] += 5
    bar_canvas.coords(bar_rect, 0, 0, _splash_step[0] * 2, 6)
    if _splash_step[0] < 100:
        splash.after(15, _animar_splash)
    else:
        splash.after(100, splash.destroy)

splash.after(50, _animar_splash)
splash.mainloop()

# === IMPORTS ===
from datetime import datetime

from config.constantes import FACTORES_ACTIVIDAD, CARPETA_SALIDA
from core.modelos import ClienteEvaluacion
from core.motor_nutricional import MotorNutricional
from core.generador_planes import ConstructorPlanNuevo
from core.exportador_salida import GeneradorPDFProfesional
from core.licencia import GestorLicencias
from utils.logger import logger

# Intentar cargar GUI
try:
    import customtkinter as ctk
    from gui.app_gui import GymApp
    GUI_DISPONIBLE = True
except ImportError:
    GUI_DISPONIBLE = False


def validar_licencia_startup() -> bool:
    """Valida la licencia al iniciar. Retorna True si es válida."""
    gestor = GestorLicencias()
    es_valida, mensaje, datos = gestor.validar_licencia()
    logger.info("[LICENCIA] %s", mensaje)

    if not es_valida:
        if GUI_DISPONIBLE:
            from tkinter import messagebox as mb
            root = ctk.CTk(); root.withdraw()
            mb.showerror(
                "Licencia Inválida",
                f"{mensaje}\n\n"
                "Para activar o renovar tu licencia, contacta a:\n"
                "📧 Consultoría Hernández\n\n"
                "La aplicación se cerrará.",
            )
            root.destroy()
        else:
            print(f"\n❌ {mensaje}")
        return False

    # Advertir si expira pronto
    if datos:
        fecha_exp = datetime.fromisoformat(datos["fecha_expiracion"])
        dias_rest = (fecha_exp - datetime.now()).days
        if dias_rest <= 30 and GUI_DISPONIBLE:
            from tkinter import messagebox as mb
            root = ctk.CTk(); root.withdraw()
            mb.showwarning(
                "Licencia Próxima a Expirar",
                f"Tu licencia expira en {dias_rest} días "
                f"({fecha_exp.strftime('%Y-%m-%d')}).\n\n"
                "Te recomendamos renovarla pronto.",
            )
            root.destroy()

    return True


# === EJECUCIÓN ===
if __name__ == "__main__":
    # Paso 1: Validar licencia
    if not validar_licencia_startup():
        logger.warning("[STARTUP] Cerrada por licencia inválida")
        sys.exit(1)

    # Paso 2: Iniciar
    if GUI_DISPONIBLE:
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        app = GymApp()
        app.mainloop()
    else:
        # Fallback a modo consola
        print("\n" + "=" * 60)
        print("    SISTEMA MVP GYMS - GENERADOR DE PLANES NUTRICIONALES")
        print("    (Modo Consola - instala customtkinter para GUI)")
        print("=" * 60)
        
        os.makedirs("planes", exist_ok=True)
        os.makedirs("datos", exist_ok=True)
        
        print("\nIngrese los datos del cliente:\n")
        
        nombre = input("Nombre completo: ").strip()
        if not nombre:
            nombre = "Cliente"
        
        while True:
            try:
                edad = int(input("Edad (14-80): "))
                if 14 <= edad <= 80:
                    break
                print("  -> Edad debe estar entre 14 y 80 anos.")
            except ValueError:
                print("  -> Ingrese un numero valido.")
        
        while True:
            try:
                peso = float(input("Peso (kg): "))
                if 30 <= peso <= 250:
                    break
                print("  -> Peso debe estar entre 30 y 250 kg.")
            except ValueError:
                print("  -> Ingrese un numero valido.")
        
        while True:
            try:
                altura = float(input("Estatura (cm): "))
                if 100 <= altura <= 250:
                    break
                print("  -> Estatura debe estar entre 100 y 250 cm.")
            except ValueError:
                print("  -> Ingrese un numero valido.")
        
        while True:
            try:
                grasa = float(input("Grasa corporal (%): "))
                if 3 <= grasa <= 60:
                    break
                print("  -> Grasa corporal debe estar entre 3% y 60%.")
            except ValueError:
                print("  -> Ingrese un numero valido.")
        
        print("\nNivel de actividad fisica:")
        print("  1. Sedentario (nula)")
        print("  2. Leve")
        print("  3. Moderada")
        print("  4. Intensa")
        
        niveles = {1: "nula", 2: "leve", 3: "moderada", 4: "intensa"}
        while True:
            try:
                opcion = int(input("Seleccione (1-4): "))
                if opcion in niveles:
                    nivel = niveles[opcion]
                    break
                print("  -> Seleccione una opcion valida (1-4).")
            except ValueError:
                print("  -> Ingrese un numero valido.")
        
        print("\nObjetivo nutricional:")
        print("  1. Deficit (bajar de peso)")
        print("  2. Mantenimiento")
        print("  3. Superavit (subir de peso/volumen)")
        
        objetivos = {1: "deficit", 2: "mantenimiento", 3: "superavit"}
        while True:
            try:
                opcion = int(input("Seleccione (1-3): "))
                if opcion in objetivos:
                    objetivo = objetivos[opcion]
                    break
                print("  -> Seleccione una opcion valida (1-3).")
            except ValueError:
                print("  -> Ingrese un numero valido.")
        
        print("\n" + "-" * 40)
        print("Procesando...")
        
        cliente = ClienteEvaluacion(
            nombre=nombre, edad=edad, peso_kg=peso,
            estatura_cm=altura, grasa_corporal_pct=grasa,
            nivel_actividad=nivel, objetivo=objetivo
        )
        
        cliente.factor_actividad = FACTORES_ACTIVIDAD.get(nivel, 1.2)
        cliente = MotorNutricional.calcular_motor(cliente)
        plan = ConstructorPlanNuevo.construir(cliente, plan_numero=1, directorio_planes="planes")
        
        if not os.path.exists(CARPETA_SALIDA):
            os.makedirs(CARPETA_SALIDA)
        
        nombre_pdf = f"plan_{cliente.nombre.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        ruta_pdf_completa = os.path.join(CARPETA_SALIDA, nombre_pdf)
        generador = GeneradorPDFProfesional(ruta_pdf_completa)
        ruta_pdf = generador.generar(cliente, plan)
        
        comidas = ['desayuno', 'almuerzo', 'comida', 'cena']
        kcal_real = sum(plan[c].get('kcal_real', 0) for c in comidas if c in plan)
        desv_max = max(plan[c].get('desviacion_pct', 0) for c in comidas if c in plan)
        
        print("\n" + "=" * 60)
        print("  PLAN GENERADO EXITOSAMENTE!")
        print("=" * 60)
        print(f"\n  Cliente: {nombre}")
        print(f"  Objetivo: {objetivo.upper()}")
        print(f"  Kcal objetivo: {cliente.kcal_objetivo:.0f}")
        print(f"  Kcal reales: {kcal_real:.0f}")
        print(f"  Desviacion maxima: {desv_max:.2f}%")
        print(f"\n  PDF guardado en: {ruta_pdf}")
        print("\n" + "=" * 60)
