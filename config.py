"""
config.py
----------
Configuración central del proyecto DataViz Python Lab.

Aquí se define QUÉ dataset de datos.gob.cl se va a consumir.
Si quieres usar otro conjunto de datos, solo necesitas cambiar
RESOURCE_ID (y opcionalmente DATASET_NAME) por los de otro
recurso publicado en https://datos.gob.cl/dataset/

Cómo obtener el resource_id de otro dataset:
1. Entra a https://datos.gob.cl/group y elige una categoría.
2. Abre un dataset y luego un recurso (archivo) dentro de él.
3. En la página del recurso, haz clic en "API de datos".
4. Copia el valor resource_id que aparece en la URL de ejemplo.
"""

# URL base del API de acción de CKAN para datos.gob.cl
CKAN_BASE_URL = "https://datos.gob.cl/api/3/action"

# Endpoint específico para consultar registros de un recurso (equivalente a un GET)
DATASTORE_SEARCH_ENDPOINT = f"{CKAN_BASE_URL}/datastore_search"

# --- Dataset por defecto: Establecimientos de Salud (Ministerio de Salud) ---
# Fuente: https://datos.gob.cl/dataset/establecimientos-de-salud-vigentes
DATASET_NAME = "Establecimientos de Salud Vigentes en Chile"
DATASET_URL = "https://datos.gob.cl/dataset/establecimientos-de-salud-vigentes"
RESOURCE_ID = "2c44d782-3365-44e3-aefb-2c8b8363a1bc"

# Cuántos registros se piden por página al API (CKAN suele limitar a 100 o 32000 según config)
PAGE_SIZE = 1000

# Máximo de registros a traer en total (protección ante datasets enormes).
# None = traer todos los registros disponibles.
MAX_RECORDS = None

# Ruta donde se guarda una copia local de los datos crudos (cache) para no
# tener que golpear la API cada vez que se recarga la app de Streamlit.
RAW_DATA_PATH = "data/raw_data.json"
PROCESSED_DATA_PATH = "data/processed_data.csv"

# Tiempo (segundos) que Streamlit mantiene en caché los datos antes de
# permitir un refresco manual.
CACHE_TTL_SECONDS = 3600
