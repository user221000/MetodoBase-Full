"""Gestor de rotación de alimentos para evitar repeticiones."""

import json
import os
from collections import Counter
from typing import Set, Dict, List

from config.catalogo_alimentos import (
    CATALOGO_POR_TIPO, categoria_de,
)
from utils.logger import logger
from config.constantes import CARPETA_REGISTROS

# Pesos de penalización por distancia al plan actual
_PESOS_VENTANA = {0: 1.0, 1: 0.6, 2: 0.3}   # índice 0 = plan más reciente


# ============================================================================
# NUEVA CLASE: Rotación inteligente con ventana deslizante
# ============================================================================

class RotacionInteligenteAlimentos:
    """
    Sistema de rotación con ventana deslizante de N planes y balanceo
    automático de alimentos infrautilizados.

    Formato del historial en disco
    ──────────────────────────────
    El JSON guardado en ``registros/<id>_rotacion_inteligente.json`` tiene la
    siguiente estructura:

    .. code-block:: json

        {
            "planes": [
                {
                    "proteina": ["pechuga_de_pollo", "huevo"],
                    "carbs":    ["arroz_blanco"],
                    "grasa":    ["aguacate"]
                },
                ...
            ]
        }

    El índice -1 corresponde al plan inmediatamente anterior.  La lista se
    limita a ``max_historial`` entradas para no crecer indefinidamente.
    """

    MAX_HISTORIAL: int = 10
    VENTANA_FRECUENCIAS: int = 7

    def __init__(self, id_cliente: str, ventana_planes: int = 3):
        self.id_cliente = id_cliente
        self.ventana_planes = ventana_planes
        self._archivo = os.path.join(
            CARPETA_REGISTROS, f"{id_cliente}_rotacion_inteligente.json"
        )
        self.historial: List[Dict[str, List[str]]] = self._cargar_historial()
        self.frecuencias: Dict[str, int] = self._calcular_frecuencias()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def obtener_penalizaciones_ponderadas(self) -> Dict[str, float]:
        """Retorna ``{alimento: peso_penalizacion}`` para los últimos N planes.

        Ponderación: plan n-1 = 1.0, n-2 = 0.6, n-3 = 0.3.
        Alimentos no vistos en la ventana tienen peso 0.0.
        """
        pesos: Dict[str, float] = {}
        ventana = self.historial[-self.ventana_planes:]

        # Recorremos de más reciente (índice -1) a más antiguo
        for distancia, entrada in enumerate(reversed(ventana)):
            peso = _PESOS_VENTANA.get(distancia, 0.0)
            for alimentos in entrada.values():
                for alimento in alimentos:
                    # Si ya apareció más cerca (peso mayor), no lo sobreescribimos
                    if pesos.get(alimento, 0.0) < peso:
                        pesos[alimento] = peso

        return pesos

    def sugerir_alimentos_infrautilizados(
        self, categoria: str, top_n: int = 3
    ) -> List[str]:
        """Retorna los ``top_n`` alimentos de la categoría menos usados
        en los últimos :attr:`VENTANA_FRECUENCIAS` planes.

        Args:
            categoria: ``'proteina'``, ``'carbs'``, ``'grasa'``, ``'verdura'``,
                ``'fruta'``
            top_n: Cantidad de sugerencias a devolver.

        Returns:
            Lista ordenada de alimentos poco utilizados (menos frecuente primero).
        """
        candidatos = CATALOGO_POR_TIPO.get(categoria, [])
        if not candidatos:
            return []

        # frecuencia 0 para alimentos que nunca aparecen en el historial
        frecuencia = {ali: self.frecuencias.get(ali, 0) for ali in candidatos}
        ordenados = sorted(frecuencia, key=lambda a: frecuencia[a])
        return ordenados[:top_n]

    def registrar_plan_nuevo(self, plan: Dict) -> None:
        """Registra el plan actual, actualiza frecuencias y persiste el historial.

        Limita el historial a :attr:`MAX_HISTORIAL` entradas.
        """
        entrada: Dict[str, List[str]] = {
            'proteina': [],
            'carbs': [],
            'grasa': [],
        }
        for comida_data in plan.values():
            if not isinstance(comida_data, dict) or 'alimentos' not in comida_data:
                continue
            for alimento, gramos in comida_data['alimentos'].items():
                if gramos > 0:
                    cat = categoria_de(alimento)
                    if cat in entrada:
                        if alimento not in entrada[cat]:
                            entrada[cat].append(alimento)

        self.historial.append(entrada)
        if len(self.historial) > self.MAX_HISTORIAL:
            self.historial = self.historial[-self.MAX_HISTORIAL:]

        # Recalcular frecuencias con el nuevo plan incluido
        self.frecuencias = self._calcular_frecuencias()
        self._guardar_historial()

    def como_penalizados_por_categoria(self) -> Dict[str, List[str]]:
        """Compatibilidad con ``SelectorAlimentos``.

        Convierte las penalizaciones ponderadas a un dict ``{cat: [alimentos]}``
        donde solo se incluyen alimentos con peso >= 0.3 (aparecieron en los
        últimos 3 planes).
        """
        ponderadas = self.obtener_penalizaciones_ponderadas()
        resultado: Dict[str, List[str]] = {'proteina': [], 'carbs': [], 'grasa': []}
        for alimento, peso in ponderadas.items():
            if peso >= 0.3:
                cat = categoria_de(alimento)
                if cat in resultado:
                    resultado[cat].append(alimento)
        return resultado

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _cargar_historial(self) -> List[Dict[str, List[str]]]:
        try:
            if os.path.exists(self._archivo):
                with open(self._archivo, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                return datos.get('planes', [])
        except Exception:
            pass
        return []

    def _guardar_historial(self) -> None:
        os.makedirs(CARPETA_REGISTROS, exist_ok=True)
        with open(self._archivo, 'w', encoding='utf-8') as f:
            json.dump({'planes': self.historial}, f, indent=2, ensure_ascii=False)

    def _calcular_frecuencias(self) -> Dict[str, int]:
        """Cuenta cuántas veces aparece cada alimento en los últimos
        :attr:`VENTANA_FRECUENCIAS` planes."""
        ventana = self.historial[-self.VENTANA_FRECUENCIAS:]
        contador: Counter = Counter()
        for entrada in ventana:
            for alimentos in entrada.values():
                contador.update(alimentos)
        return dict(contador)


class GestorRotacionAlimentos:
    """Gestiona rotación de alimentos por cliente para evitar repeticiones.

    Delega la lógica de ventana deslizante a :class:`RotacionInteligenteAlimentos`
    internamente, manteniendo compatibilidad con el historial legacy.
    """
    
    def __init__(self, id_cliente: str):
        """Inicializa gestor de rotación."""
        self.id_cliente = id_cliente
        self.historial_alimentos = {
            'proteinas': [],
            'carbs': [],
            'grasas': []
        }
        self.cargar_historial()
        # Sistema inteligente acoplado
        self._inteligente = RotacionInteligenteAlimentos(id_cliente)
    
    def cargar_historial(self) -> None:
        """Carga historial de alimentos usados por este cliente."""
        try:
            archivo_hist = os.path.join(
                CARPETA_REGISTROS, f"{self.id_cliente}_historial.json"
            )
            if os.path.exists(archivo_hist):
                with open(archivo_hist, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    self.historial_alimentos = datos
                    logger.info("[OK] Historial cargado (%d planes)", len(self.historial_alimentos['proteinas']))
            else:
                logger.info("[INIT] Primer historial para este cliente")
                self.historial_alimentos = {'proteinas': [], 'carbs': [], 'grasas': []}
        except Exception as e:
            logger.error("[ERROR] Error cargando historial: %s", e)
            self.historial_alimentos = {'proteinas': [], 'carbs': [], 'grasas': []}
    
    def obtener_penalizados(self) -> Dict[str, List[str]]:
        """Retorna alimentos penalizados estructurados por categoría.

        Usa la ventana deslizante de :class:`RotacionInteligenteAlimentos`
        cuando hay historial disponible; de lo contrario solo devuelve el
        plan inmediatamente anterior (comportamiento original).
        """
        if self._inteligente.historial:
            penalizados = self._inteligente.como_penalizados_por_categoria()
            if any(penalizados.values()):
                for cat, items in penalizados.items():
                    if items:
                        logger.debug("%s penalizados (ventana): %s", cat.capitalize(), items)
            return penalizados

        # fallback legacy
        penalizados: Dict[str, List[str]] = {
            'proteina': [],
            'carbs': [],
            'grasa': [],
        }
        if self.historial_alimentos['proteinas']:
            penalizados['proteina'] = list(self.historial_alimentos['proteinas'][-1])
            logger.debug("Proteínas penalizadas: %s", penalizados['proteina'])
        if self.historial_alimentos['carbs']:
            penalizados['carbs'] = list(self.historial_alimentos['carbs'][-1])
            logger.debug("Carbos penalizados: %s", penalizados['carbs'])
        if self.historial_alimentos['grasas']:
            penalizados['grasa'] = list(self.historial_alimentos['grasas'][-1])
            logger.debug("Grasas penalizadas: %s", penalizados['grasa'])
        return penalizados

    def obtener_penalizados_flat(self) -> Set[str]:
        """Retrocompatibilidad: devuelve un set plano con todos los penalizados."""
        structured = self.obtener_penalizados()
        flat: Set[str] = set()
        for items in structured.values():
            flat.update(items)
        return flat
    
    def registrar_plan(self, plan: Dict) -> None:
        """Registra alimentos del plan en el historial legacy Y en el sistema
        de rotación inteligente con ventana deslizante.
        """
        proteinas_plan: set[str] = set()
        carbs_plan: set[str] = set()
        grasas_plan: set[str] = set()

        for comida_data in plan.values():
            if not isinstance(comida_data, dict) or 'alimentos' not in comida_data:
                continue
            for alimento, gramos in comida_data['alimentos'].items():
                if gramos > 0:
                    cat = categoria_de(alimento)
                    if cat == 'proteina':
                        proteinas_plan.add(alimento)
                    elif cat == 'carbs':
                        carbs_plan.add(alimento)
                    elif cat == 'grasa':
                        grasas_plan.add(alimento)

        # Historial legacy
        self.historial_alimentos['proteinas'].append(list(proteinas_plan))
        self.historial_alimentos['carbs'].append(list(carbs_plan))
        self.historial_alimentos['grasas'].append(list(grasas_plan))

        logger.info("Plan registrado: P=%s | C=%s | G=%s",
                    list(proteinas_plan), list(carbs_plan), list(grasas_plan))

        self.guardar_historial()

        # Rotación inteligente
        self._inteligente.registrar_plan_nuevo(plan)
    
    def guardar_historial(self) -> None:
        """Guarda historial a archivo JSON."""
        os.makedirs(CARPETA_REGISTROS, exist_ok=True)
        
        archivo_hist = os.path.join(
            CARPETA_REGISTROS, f"{self.id_cliente}_historial.json"
        )
        with open(archivo_hist, 'w', encoding='utf-8') as f:
            json.dump(self.historial_alimentos, f, indent=2, ensure_ascii=False)
    
    def es_primer_plan(self) -> bool:
        """Retorna True si es el primer plan del cliente."""
        return (
            len(self.historial_alimentos['proteinas']) == 0 and
            len(self.historial_alimentos['carbs']) == 0 and
            len(self.historial_alimentos['grasas']) == 0
        )
    
    def cantidad_planes(self) -> int:
        """Retorna cantidad total de planes generados."""
        return len(self.historial_alimentos['proteinas'])