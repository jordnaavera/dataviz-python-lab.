# DataViz Python Lab — Establecimientos de Salud en Chile

Proyecto final: análisis y presentación de datos utilizando una **API REST
pública** del Gobierno de Chile, con procesamiento en **pandas**,
visualización con **matplotlib** y una interfaz web interactiva construida
con **Streamlit**.

## 1. Fuente de datos

- Portal: [datos.gob.cl](https://datos.gob.cl/group)
- Dataset: [Establecimientos de Salud Vigentes](https://datos.gob.cl/dataset/establecimientos-de-salud-vigentes) (Ministerio de Salud)
- Tecnología del portal: **CKAN** — los datos se obtienen mediante una
  consulta `GET` al endpoint `datastore_search` de la API de acción de CKAN:

```
https://datos.gob.cl/api/3/action/datastore_search?resource_id=2c44d782-3365-44e3-aefb-2c8b8363a1bc&limit=1000&offset=0
```

No se requiere API key: es un dataset público. La app pagina automáticamente
sobre `offset`/`limit` hasta traer todos los registros disponibles.

## 2. Estructura del proyecto

```
dataviz_project/
├── app.py               # Aplicación Streamlit (interfaz principal)
├── api_client.py        # Consumo de la API REST (requests + json, paginación)
├── data_processing.py   # Limpieza y transformación con pandas
├── charts.py             # Generación de gráficos con matplotlib
├── config.py             # Configuración central (resource_id, URLs, cache)
├── requirements.txt
├── data/                 # Cache local de datos descargados (se genera solo)
└── README.md
```

## 3. Instalación y ejecución local

```bash
# 1. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. (Opcional) Probar el cliente de API por separado
python api_client.py

# 4. Ejecutar la aplicación
streamlit run app.py
```

Streamlit abrirá automáticamente `http://localhost:8501` en tu navegador.

## 4. Cómo funciona

1. **`api_client.py`** hace las consultas GET a la API de datos.gob.cl,
   pagina los resultados, valida errores de red/HTTP/JSON y guarda una
   copia local en `data/raw_data.json` para no volver a golpear la API
   en cada recarga.
2. **`data_processing.py`** transforma la lista de registros en un
   DataFrame de pandas, limpia texto y valores vacíos, y detecta
   automáticamente columnas clave (región, comuna, tipo de
   establecimiento) buscando por palabras clave en los nombres de columna.
   Esto hace que la app sea **reutilizable con otros datasets** de
   datos.gob.cl sin reescribir código.
3. **`charts.py`** genera gráficos de barras, circulares (dona) y de
   barras apiladas con matplotlib.
4. **`app.py`** arma la interfaz: filtros dinámicos en la barra lateral
   (región, comuna, tipo), KPIs, pestañas de Resumen / Gráficos /
   Explorador libre / Datos crudos, y un botón de descarga en CSV.

## 5. Usar otro dataset de datos.gob.cl

El proyecto no está atado a un solo dataset. Para cambiarlo:

1. Ve a <https://datos.gob.cl/group>, elige una categoría (Educación, Empleo,
   Finanzas, Emergencias, etc.) y abre un dataset con un recurso en
   formato tabular (CSV/XLSX) que tenga **"Datastore activo: True"**.
2. En la página del recurso, entra a "API de datos" y copia el
   `resource_id` de la URL de ejemplo.
3. Reemplaza `RESOURCE_ID` (y `DATASET_NAME`/`DATASET_URL` si quieres) en
   `config.py`.
4. Borra `data/raw_data.json` (o usa el botón "Recargar datos" en la app)
   y vuelve a ejecutar `streamlit run app.py`. Los filtros y gráficos se
   adaptan solos a las nuevas columnas.

## 6. Despliegue (Streamlit Community Cloud)

1. Sube este proyecto a un repositorio de GitHub.
2. Entra a <https://share.streamlit.io/>, conecta tu cuenta de GitHub.
3. Selecciona el repositorio, la rama y como archivo principal `app.py`.
4. Streamlit instalará automáticamente `requirements.txt` y publicará
   la app en una URL pública tipo `https://tuapp.streamlit.app`.
5. Copia ese enlace como entregable del proyecto.

Si prefieres ejecución local, basta con entregar este código y las
instrucciones de la sección 3.

## 7. Pruebas de usabilidad realizadas

- Verificación de manejo de errores cuando la API no responde o cambia
  el `resource_id` (mensaje claro en la interfaz, sin caída de la app).
- Verificación de que los filtros combinados (región + comuna + tipo)
  no dejan el dataset vacío sin advertencia al usuario.
- Verificación de que los gráficos se actualizan correctamente al
  cambiar los controles (sliders y selectboxes).
- Prueba de descarga del CSV filtrado.

## 8. Librerías utilizadas

`requests`, `json` (estándar de Python), `pandas`, `matplotlib`, `streamlit`
— tal como exige la pauta del proyecto.
