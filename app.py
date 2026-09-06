
"""
app.py
------
Aplicación Streamlit del proyecto "DataViz Python Lab".

Consume datos de la API REST de datos.gob.cl (CKAN DataStore), los
procesa con pandas y los presenta de forma interactiva con filtros,
KPIs y gráficos de matplotlib.

Ejecutar con:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd

from config import (
    RESOURCE_ID,
    DATASET_NAME,
    DATASET_URL,
    RAW_DATA_PATH,
    CACHE_TTL_SECONDS,
)
from api_client import get_dataset_records, ApiClientError
from data_processing import (
    records_to_dataframe,
    clean_dataframe,
    detect_key_columns,
    value_counts_table,
    apply_filters,
)
from charts import (
    bar_chart_top_categories,
    pie_chart_distribution,
    grouped_bar_chart,
)

st.set_page_config(
    page_title=DATASET_NAME,
    page_icon="📈",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Carga de datos (con caché de Streamlit para no golpear la API en cada clic)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def load_data(force_refresh: bool = False) -> pd.DataFrame:
    records = get_dataset_records(
        resource_id=RESOURCE_ID,
        use_cache=True,
        cache_path=RAW_DATA_PATH,
        force_refresh=force_refresh,
    )
    df = records_to_dataframe(records)
    df = clean_dataframe(df)
    return df


# ---------------------------------------------------------------------------
# Barra lateral: título, fuente y controles globales
# ---------------------------------------------------------------------------
st.sidebar.title("Panel de control")
st.sidebar.markdown(
    f"**Fuente de datos:** [datos.gob.cl]({DATASET_URL})\n\n"
    f"**Recurso (resource_id):**\n`{RESOURCE_ID}`"
)

if st.sidebar.button("Recargar datos desde la API"):
    load_data.clear()
    st.session_state["force_refresh"] = True

with st.spinner("Consultando la API de datos.gob.cl..."):
    try:
        df = load_data(force_refresh=st.session_state.get("force_refresh", False))
    except ApiClientError as e:
        st.error(
            "No se pudo obtener información desde la API de datos.gob.cl.\n\n"
            f"Detalle técnico: {e}"
        )
        st.stop()

st.session_state["force_refresh"] = False

if df.empty:
    st.warning("La consulta no retornó registros. Intenta recargar los datos.")
    st.stop()

key_columns = detect_key_columns(df)

# ---------------------------------------------------------------------------
# Filtros interactivos (se arman dinámicamente según columnas detectadas)
# ---------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Filtros")

filters = {}
for label, col_key in [("Región", "region"), ("Comuna", "comuna"), ("Tipo de establecimiento", "tipo")]:
    column = key_columns.get(col_key)
    if column and column in df.columns:
        options = sorted(df[column].dropna().unique().tolist())
        selected = st.sidebar.multiselect(label, options)
        filters[column] = selected

filtered_df = apply_filters(df, filters)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Registros totales: {len(df):,}\n\n"
    f"Registros tras filtros: {len(filtered_df):,}"
)

# ---------------------------------------------------------------------------
# Encabezado principal
# ---------------------------------------------------------------------------
st.title(DATASET_NAME)
st.caption(
    "Datos obtenidos en vivo mediante una consulta GET a la API REST (CKAN) "
    "del Portal de Datos Abiertos del Gobierno de Chile."
)

tab_resumen, tab_graficos, tab_explorador, tab_datos = st.tabs(
    ["Resumen", "Gráficos", "Explorador", "Datos crudos"]
)

# ---------------------------------------------------------------------------
# TAB 1: Resumen (KPIs)
# ---------------------------------------------------------------------------
with tab_resumen:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Registros (filtrados)", f"{len(filtered_df):,}")

    region_col = key_columns.get("region")
    comuna_col = key_columns.get("comuna")
    tipo_col = key_columns.get("tipo")

    col2.metric(
        "Regiones representadas",
        filtered_df[region_col].nunique() if region_col else "N/A",
    )
    col3.metric(
        "Comunas representadas",
        filtered_df[comuna_col].nunique() if comuna_col else "N/A",
    )
    col4.metric(
        "Tipos de establecimiento",
        filtered_df[tipo_col].nunique() if tipo_col else "N/A",
    )

    st.markdown("### Vista previa de los datos filtrados")
    st.dataframe(filtered_df.head(20), use_container_width=True)

    if region_col:
        st.markdown("### Top regiones por cantidad de registros")
        st.dataframe(value_counts_table(filtered_df, region_col, top_n=10), use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 2: Gráficos (matplotlib)
# ---------------------------------------------------------------------------
with tab_graficos:
    categorical_cols = filtered_df.select_dtypes(include="object").columns.tolist()

    if not categorical_cols:
        st.info("No se detectaron columnas categóricas para graficar.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            default_idx = categorical_cols.index(region_col) if region_col in categorical_cols else 0
            col_bar = st.selectbox("Columna para gráfico de barras", categorical_cols, index=default_idx, key="bar")
            top_n_bar = st.slider("Cantidad de categorías a mostrar", 3, 20, 10, key="bar_n")
            st.pyplot(bar_chart_top_categories(filtered_df, col_bar, top_n=top_n_bar))

        with c2:
            default_idx2 = categorical_cols.index(tipo_col) if tipo_col in categorical_cols else 0
            col_pie = st.selectbox("Columna para gráfico circular", categorical_cols, index=default_idx2, key="pie")
            top_n_pie = st.slider("Categorías a destacar (resto = 'Otros')", 3, 12, 6, key="pie_n")
            st.pyplot(pie_chart_distribution(filtered_df, col_pie, top_n=top_n_pie))

        st.markdown("### Composición cruzada entre dos variables")
        c3, c4 = st.columns(2)
        with c3:
            group_col = st.selectbox("Agrupar por", categorical_cols, index=default_idx, key="group")
        with c4:
            remaining = [c for c in categorical_cols if c != group_col] or categorical_cols
            cat_col = st.selectbox("Desglosar por", remaining, key="cat")

        if group_col and cat_col and group_col != cat_col:
            st.pyplot(grouped_bar_chart(filtered_df, group_col, cat_col))
        else:
            st.info("Selecciona dos columnas distintas para ver el cruce.")

# ---------------------------------------------------------------------------
# TAB 3: Explorador libre
# ---------------------------------------------------------------------------
with tab_explorador:
    st.markdown("### Explora cualquier columna del dataset")
    all_cols = filtered_df.columns.tolist()
    chosen_col = st.selectbox("Selecciona una columna", all_cols)

    if pd.api.types.is_numeric_dtype(filtered_df[chosen_col]) or filtered_df[chosen_col].str.replace(
        ".", "", regex=False
    ).str.isnumeric().fillna(False).all():
        numeric_series = pd.to_numeric(filtered_df[chosen_col], errors="coerce")
        st.write(numeric_series.describe())
    else:
        st.dataframe(value_counts_table(filtered_df, chosen_col, top_n=30), use_container_width=True)

    search_term = st.text_input("Buscar texto libre en todo el dataset filtrado")
    if search_term:
        mask = filtered_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False, na=False).any(), axis=1)
        st.dataframe(filtered_df[mask], use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 4: Datos crudos + descarga
# ---------------------------------------------------------------------------
with tab_datos:
    st.markdown("### Datos crudos filtrados")
    st.dataframe(filtered_df, use_container_width=True)

    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar datos filtrados (CSV)",
        data=csv_bytes,
        file_name="datos_filtrados.csv",
        mime="text/csv",
    )

st.markdown("---")
st.caption(
    "Proyecto Final DataViz Python Lab · Datos: Portal de Datos Abiertos del Gobierno de Chile "
    "(datos.gob.cl) · API CKAN DataStore · Procesamiento: pandas · Gráficos: matplotlib · UI: Streamlit"
)
