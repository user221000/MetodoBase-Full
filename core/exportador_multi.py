"""Exportación de planes nutricionales a múltiples formatos (Excel / CSV)."""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.alimentos_base import ALIMENTOS_BASE

_COMIDAS_ORDEN = ["desayuno", "almuerzo", "comida", "cena"]


class ExportadorMultiformato:
    """Exporta planes a múltiples formatos."""

    # ------------------------------------------------------------------ #
    # Excel                                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def a_excel(cliente, plan, ruta_salida: str) -> str:
        """
        Genera Excel con cuatro hojas:
          1. Cliente  — resumen de datos del cliente
          2. Plan Semanal — alimentos y gramos por comida
          3. Lista de Compras — totales agrupados por alimento
          4. Macros Detallados — proteínas, carbs, grasas y kcal reales
        """
        with pd.ExcelWriter(ruta_salida, engine="xlsxwriter") as writer:
            wb = writer.book

            # ── formatos ──
            fmt_header = wb.add_format({
                "bold": True, "bg_color": "#7B2D8E", "font_color": "#FFFFFF",
                "border": 1, "align": "center",
            })
            fmt_num = wb.add_format({"num_format": "0.0", "align": "right"})
            fmt_int = wb.add_format({"num_format": "0", "align": "right"})

            # ── Hoja 1: Cliente ──────────────────────────────────────── #
            df_cliente = pd.DataFrame([{
                "Nombre":       cliente.nombre,
                "Edad":         getattr(cliente, "edad", ""),
                "Peso (kg)":    getattr(cliente, "peso_kg", ""),
                "Estatura (cm)": getattr(cliente, "estatura_cm", ""),
                "% Grasa":      getattr(cliente, "grasa_corporal_pct", ""),
                "Objetivo":     getattr(cliente, "objetivo", ""),
                "Actividad":    getattr(cliente, "nivel_actividad", ""),
                "TMB":          round(getattr(cliente, "tmb", 0), 1),
                "GET":          round(getattr(cliente, "get_total", 0), 1),
                "Kcal objetivo": round(getattr(cliente, "kcal_objetivo", 0), 1),
                "Proteína (g)": round(getattr(cliente, "proteina_g", 0), 1),
                "Carbs (g)":    round(getattr(cliente, "carbs_g", 0), 1),
                "Grasas (g)":   round(getattr(cliente, "grasa_g", 0), 1),
                "Fecha":        datetime.now().strftime("%Y-%m-%d"),
            }])
            df_cliente.to_excel(writer, sheet_name="Cliente", index=False)
            _autofit(writer.sheets["Cliente"], df_cliente, fmt_header)

            # ── Hoja 2: Plan Semanal ─────────────────────────────────── #
            rows_plan = []
            for comida_nombre in _COMIDAS_ORDEN:
                if comida_nombre not in plan:
                    continue
                comida = plan[comida_nombre]
                kcal_obj = comida.get("kcal_objetivo", 0)
                for alimento, gramos in comida.get("alimentos", {}).items():
                    rows_plan.append({
                        "Comida":        comida_nombre.capitalize(),
                        "Alimento":      alimento.replace("_", " ").capitalize(),
                        "Cantidad (g)":  int(gramos),
                        "Kcal objetivo": round(kcal_obj, 1),
                    })
            df_plan = pd.DataFrame(rows_plan) if rows_plan else pd.DataFrame(
                columns=["Comida", "Alimento", "Cantidad (g)", "Kcal objetivo"])
            df_plan.to_excel(writer, sheet_name="Plan Semanal", index=False)
            _autofit(writer.sheets["Plan Semanal"], df_plan, fmt_header)

            # ── Hoja 3: Lista de Compras ─────────────────────────────── #
            if not df_plan.empty:
                df_compras = (
                    df_plan.groupby("Alimento")["Cantidad (g)"]
                    .sum()
                    .reset_index()
                    .rename(columns={"Cantidad (g)": "Total diario (g)"})
                    .sort_values("Alimento")
                )
                df_compras["Total semanal (g)"] = df_compras["Total diario (g)"] * 7
            else:
                df_compras = pd.DataFrame(
                    columns=["Alimento", "Total diario (g)", "Total semanal (g)"])
            df_compras.to_excel(writer, sheet_name="Lista de Compras", index=False)
            _autofit(writer.sheets["Lista de Compras"], df_compras, fmt_header)

            # ── Hoja 4: Macros Detallados ────────────────────────────── #
            rows_macros = []
            totales = {"proteina_g": 0.0, "carbs_g": 0.0, "grasa_g": 0.0, "kcal": 0.0}
            for comida_nombre in _COMIDAS_ORDEN:
                if comida_nombre not in plan:
                    continue
                comida = plan[comida_nombre]
                p = c = g = k = 0.0
                for alimento, gramos in comida.get("alimentos", {}).items():
                    data = ALIMENTOS_BASE.get(alimento, {})
                    factor = gramos / 100
                    p += data.get("proteina", 0) * factor
                    c += data.get("carbs",    0) * factor
                    g += data.get("grasa",    0) * factor
                    k += data.get("kcal",     0) * factor
                rows_macros.append({
                    "Comida":       comida_nombre.capitalize(),
                    "Proteína (g)": round(p, 1),
                    "Carbs (g)":    round(c, 1),
                    "Grasas (g)":   round(g, 1),
                    "Kcal reales":  round(k, 1),
                    "Kcal objetivo": round(comida.get("kcal_objetivo", 0), 1),
                    "Desviación (%)": round(comida.get("desviacion_pct", 0), 2),
                })
                totales["proteina_g"] += p
                totales["carbs_g"]    += c
                totales["grasa_g"]    += g
                totales["kcal"]       += k

            rows_macros.append({
                "Comida":       "TOTAL",
                "Proteína (g)": round(totales["proteina_g"], 1),
                "Carbs (g)":    round(totales["carbs_g"],    1),
                "Grasas (g)":   round(totales["grasa_g"],    1),
                "Kcal reales":  round(totales["kcal"],       1),
                "Kcal objetivo": round(getattr(cliente, "kcal_objetivo", 0), 1),
                "Desviación (%)": "",
            })

            df_macros = pd.DataFrame(rows_macros)
            df_macros.to_excel(writer, sheet_name="Macros Detallados", index=False)
            _autofit(writer.sheets["Macros Detallados"], df_macros, fmt_header)

        return ruta_salida

    # ------------------------------------------------------------------ #
    # CSV                                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def a_csv_simple(plan, ruta_salida: str) -> str:
        """CSV simple para impresión rápida (compatible con Excel vía utf-8-sig)."""
        rows = []
        for comida, datos in plan.items():
            if comida == "metadata_mes_anterior":
                continue
            for ali, gramos in datos.get("alimentos", {}).items():
                rows.append({
                    "comida":   comida,
                    "alimento": ali.replace("_", " ").capitalize(),
                    "gramos":   int(gramos),
                })
        df = pd.DataFrame(rows)
        df.to_csv(ruta_salida, index=False, encoding="utf-8-sig")
        return ruta_salida


# ────────────────────────────────────────────────────────────────────────── #
# Helpers                                                                    #
# ────────────────────────────────────────────────────────────────────────── #

def _autofit(sheet, df: pd.DataFrame, fmt_header) -> None:
    """Aplica ancho automático y formato de encabezado."""
    for col_idx, col_name in enumerate(df.columns):
        width = max(len(str(col_name)), df[col_name].astype(str).map(len).max()
                    if not df.empty else 0) + 2
        sheet.set_column(col_idx, col_idx, min(width, 40))
        sheet.write(0, col_idx, col_name, fmt_header)
