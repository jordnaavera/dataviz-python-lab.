"""
data_processing.py
-------------------
Convierte los registros crudos (lista de diccionarios obtenida del API)
en un DataFrame de pandas limpio y listo para analizar/visualizar.

Como distintos datasets de datos.gob.cl usan distintos nombres de columna,
este módulo incluye un "detector" de columnas por palabras clave, para que
la app de Streamlit pueda adaptarse automáticamente a variaciones del
dataset (por ejemplo "Region" vs "REGION" vs "NombreRegion").
"""

from typing import List, Dict, Any, Optional

import pandas as pd


def records_to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convierte la lista de registros JSON del API en un DataFrame de pandas."""
    df = pd.DataFrame.from_records(records)

    # CKAN agrega una columna interna "_id" (llave del DataStore) que no
    # aporta valor analítico; la eliminamos si existe.
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])

    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpieza genérica aplicable a cualquier dataset tabular de datos.gob.cl:
    - Quita espacios en blanco al inicio/fin de texto.
    - Reemplaza strings vacíos por NaN.
    - Elimina filas completamente vacías y columnas completamente vacías.
    - Elimina registros duplicados exactos.
    """
    df = df.copy()

    # Normalizar texto en columnas tipo object
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"": None, "nan": None, "None": None, "NULL": None})

    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")
    df = df.drop_duplicates()
    df = df.reset_index(drop=True)

    return df


def find_column(df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
    """
    Busca, entre las columnas del DataFrame, la primera que contenga
    alguna de las palabras clave dadas (sin distinguir mayúsculas/acentos).

    Ejemplo: find_column(df, ["region"]) -> "Region" o "NombreRegion", etc.
    """
    normalized = {
        col: (
            col.lower()
            .replace("á", "a").replace("é", "e").replace("í", "i")
            .replace("ó", "o").replace("ú", "u")
        )
        for col in df.columns
    }
    for keyword in keywords:
        keyword = keyword.lower()
        for original_col, norm_col in normalized.items():
            if keyword in norm_col:
                return original_col
    return None


def detect_key_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Intenta identificar automáticamente las columnas más relevantes para
    el análisis (región, comuna, tipo de establecimiento, nombre, coordenadas).
    Si el dataset se reemplaza por otro, esta función seguirá intentando
    encontrar columnas equivalentes por nombre.
    """
    return {
        # Se prioriza la columna "...Glosa" (el nombre legible) por sobre
        # la columna "...Codigo" (el código numérico), para que los
        # filtros y gráficos muestren nombres en vez de números.
        "region": find_column(df, ["regionglosa", "region_glosa", "region"]),
        "comuna": find_column(df, ["comunaglosa", "comuna_glosa", "comuna"]),
        "tipo": find_column(df, ["tipoestablecimientoglosa", "tipoestablec", "tipo_establec", "tipo"]),
        "dependencia": find_column(df, ["dependenciaglosa", "dependencia", "dependencia_admin"]),
        "nombre": find_column(df, ["nombreoficial", "nombre_oficial", "nombre"]),
        "latitud": find_column(df, ["latitud", "lat"]),
        "longitud": find_column(df, ["longitud", "lng", "long"]),
    }


def value_counts_table(df: pd.DataFrame, column: str, top_n: Optional[int] = None) -> pd.DataFrame:
    """
    Devuelve una tabla resumen (conteo y porcentaje) de los valores de una
    columna categórica, ordenada de mayor a menor frecuencia.
    """
    counts = df[column].value_counts(dropna=True)
    if top_n:
        counts = counts.head(top_n)

    table = counts.reset_index()
    table.columns = [column, "Cantidad"]
    table["Porcentaje"] = (table["Cantidad"] / df[column].notna().sum() * 100).round(1)
    return table


def apply_filters(
    df: pd.DataFrame,
    filters: Dict[str, List[str]],
) -> pd.DataFrame:
    """
    Aplica filtros de tipo "columna en lista de valores seleccionados".
    Usado por los controles interactivos (selectboxes/multiselect) de Streamlit.

    Parameters
    ----------
    df : pd.DataFrame
    filters : dict
        Diccionario {nombre_columna: [valores_seleccionados]}. Si la lista
        de valores está vacía, no se filtra por esa columna.
    """
    filtered = df.copy()
    for column, selected_values in filters.items():
        if column and selected_values:
            filtered = filtered[filtered[column].isin(selected_values)]
    return filtered
