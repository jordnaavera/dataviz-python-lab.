"""
charts.py
---------
Funciones que generan figuras de matplotlib a partir de un DataFrame.
Cada función retorna un objeto `Figure` que luego se muestra en
Streamlit con `st.pyplot(fig)`.
"""

from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

# Paleta de colores consistente para todo el proyecto
PRIMARY_COLOR = "#0B5FFF"
PALETTE = ["#0B5FFF", "#00B8A9", "#F4A259", "#EF476F", "#7B61FF", "#2EC4B6", "#FF9F1C"]


def bar_chart_top_categories(
    df: pd.DataFrame,
    column: str,
    top_n: int = 10,
    title: Optional[str] = None,
    xlabel: str = "Cantidad",
) -> plt.Figure:
    """Gráfico de barras horizontales con las N categorías más frecuentes de una columna."""
    counts = df[column].value_counts(dropna=True).head(top_n).sort_values()

    fig, ax = plt.subplots(figsize=(8, max(3, 0.4 * len(counts))))
    ax.barh(counts.index.astype(str), counts.values, color=PRIMARY_COLOR)
    ax.set_xlabel(xlabel)
    ax.set_title(title or f"Top {top_n} - {column}")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return fig


def pie_chart_distribution(
    df: pd.DataFrame,
    column: str,
    top_n: int = 6,
    title: Optional[str] = None,
) -> plt.Figure:
    """
    Gráfico circular (dona) con la distribución de una columna categórica.
    Las categorías fuera del top_n se agrupan como "Otros".
    """
    counts = df[column].value_counts(dropna=True)
    top_counts = counts.head(top_n)
    others_sum = counts.iloc[top_n:].sum()
    if others_sum > 0:
        top_counts = pd.concat([top_counts, pd.Series({"Otros": others_sum})])

    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, _, autotexts = ax.pie(
        top_counts.values,
        labels=top_counts.index.astype(str),
        autopct="%1.1f%%",
        colors=PALETTE,
        startangle=90,
        pctdistance=0.8,
        wedgeprops={"width": 0.4, "edgecolor": "white"},
    )
    ax.set_title(title or f"Distribución de {column}")
    fig.tight_layout()
    return fig


def histogram_numeric(
    df: pd.DataFrame,
    column: str,
    bins: int = 20,
    title: Optional[str] = None,
) -> plt.Figure:
    """Histograma de una columna numérica."""
    series = pd.to_numeric(df[column], errors="coerce").dropna()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(series, bins=bins, color=PRIMARY_COLOR, edgecolor="white")
    ax.set_xlabel(column)
    ax.set_ylabel("Frecuencia")
    ax.set_title(title or f"Distribución de {column}")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return fig


def grouped_bar_chart(
    df: pd.DataFrame,
    group_column: str,
    category_column: str,
    top_groups: int = 8,
    top_categories: int = 5,
    title: Optional[str] = None,
) -> plt.Figure:
    """
    Gráfico de barras apiladas: para las `top_groups` categorías más
    frecuentes de group_column, muestra la composición según category_column.
    Útil, por ejemplo, para "tipo de establecimiento por región".
    """
    top_group_values = df[group_column].value_counts().head(top_groups).index
    top_category_values = df[category_column].value_counts().head(top_categories).index

    subset = df[df[group_column].isin(top_group_values) & df[category_column].isin(top_category_values)]
    pivot = pd.crosstab(subset[group_column], subset[category_column])
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(9, 5))
    bottom = None
    for i, category in enumerate(pivot.columns):
        values = pivot[category]
        ax.bar(pivot.index.astype(str), values, bottom=bottom, label=str(category), color=PALETTE[i % len(PALETTE)])
        bottom = values if bottom is None else bottom + values

    ax.set_ylabel("Cantidad")
    ax.set_title(title or f"{category_column} por {group_column}")
    ax.legend(title=category_column, bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return fig
