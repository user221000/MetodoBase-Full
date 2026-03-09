"""Funciones utilitarias generales."""
import os
import sys
import json
import glob
import platform
import subprocess

from utils.logger import logger


def resource_path(relative_path):
    """Resuelve rutas portables para PyInstaller y desarrollo."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def abrir_carpeta_pdf(ruta: str | None = None) -> None:
    """Abre la carpeta de PDFs en el explorador de archivos. Compatible Windows/macOS/Linux."""
    from config.constantes import CARPETA_SALIDA
    carpeta = ruta or CARPETA_SALIDA
    if not os.path.exists(carpeta):
        os.makedirs(carpeta, exist_ok=True)
    sistema = platform.system()
    try:
        if sistema == "Windows":
            os.startfile(carpeta)
        elif sistema == "Darwin":
            subprocess.Popen(["open", carpeta])
        else:
            subprocess.Popen(["xdg-open", carpeta])
    except Exception as exc:
        logger.warning("No se pudo abrir carpeta %s: %s", carpeta, exc)


def cargar_plan_anterior_cliente(cliente_id: str, directorio_planes: str = ".") -> dict | None:
    """
    Carga el último plan JSON del cliente para obtener peso_base_mes anterior.
    
    Args:
        cliente_id: ID único del cliente
        directorio_planes: Ruta donde buscar archivos plan_*.json
        
    Returns:
        dict: Último plan JSON encontrado o None si no existe
    """
    try:
        pattern = f"plan_{cliente_id}_*.json"
        archivos = glob.glob(os.path.join(directorio_planes, pattern))
        
        if not archivos:
            return None
        
        archivo_reciente = max(archivos, key=os.path.getctime)
        
        with open(archivo_reciente, 'r', encoding='utf-8') as f:
            plan_anterior = json.load(f)
        
        return plan_anterior
    except Exception:
        return None
