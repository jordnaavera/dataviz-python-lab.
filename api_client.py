"""
api_client.py
--------------
Responsable de TODA la comunicación con la API REST de datos.gob.cl
(API de acción de CKAN). Usa exclusivamente la librería `requests`
para hacer consultas GET y `json` para interpretar las respuestas.

Funciones principales:
    - fetch_all_records(resource_id): trae todos los registros de un
      recurso, paginando automáticamente.
    - save_raw_json(records, path): guarda una copia local (cache).
    - load_raw_json(path): recupera la copia local si existe.
"""

import json
import os
import time
from typing import List, Dict, Any, Optional

import requests

from config import DATASTORE_SEARCH_ENDPOINT, PAGE_SIZE, MAX_RECORDS


class ApiClientError(Exception):
    """Error controlado al consultar el API de datos.gob.cl."""
    pass


def _get(params: Dict[str, Any], timeout: int = 15) -> Dict[str, Any]:
    """
    Ejecuta una consulta GET al API de acción de CKAN y valida la respuesta.

    Parameters
    ----------
    params : dict
        Parámetros de query string (resource_id, limit, offset, etc.)
    timeout : int
        Segundos máximos de espera por la respuesta.

    Returns
    -------
    dict
        El contenido de la clave "result" de la respuesta JSON.
    """
    try:
        response = requests.get(DATASTORE_SEARCH_ENDPOINT, params=params, timeout=timeout)
    except requests.exceptions.RequestException as exc:
        raise ApiClientError(f"No fue posible conectar con la API: {exc}") from exc

    if response.status_code != 200:
        raise ApiClientError(
            f"La API respondió con código {response.status_code}: {response.text[:300]}"
        )

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        raise ApiClientError("La respuesta de la API no es un JSON válido.") from exc

    if not payload.get("success", False):
        raise ApiClientError(f"La API reportó un error: {payload.get('error')}")

    return payload["result"]


def fetch_all_records(
    resource_id: str,
    page_size: int = PAGE_SIZE,
    max_records: Optional[int] = MAX_RECORDS,
    query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Descarga todos los registros de un recurso de datos.gob.cl usando
    paginación (offset/limit), tal como recomienda la documentación
    del DataStore de CKAN.

    Parameters
    ----------
    resource_id : str
        Identificador del recurso a consultar (ver config.py).
    page_size : int
        Cantidad de registros a pedir por request.
    max_records : int | None
        Límite total de registros a traer. None = sin límite (trae todo).
    query : str | None
        Texto libre opcional para filtrar registros en el servidor (parámetro `q`).

    Returns
    -------
    list[dict]
        Lista de registros (cada uno es un diccionario columna -> valor).
    """
    records: List[Dict[str, Any]] = []
    offset = 0

    while True:
        params = {
            "resource_id": resource_id,
            "limit": page_size,
            "offset": offset,
        }
        if query:
            params["q"] = query

        result = _get(params)
        page_records = result.get("records", [])
        records.extend(page_records)

        total_available = result.get("total", len(records))

        # Condiciones de corte: no llegaron más registros, se alcanzó el
        # total reportado por la API, o se alcanzó el máximo pedido por el usuario.
        if not page_records:
            break
        if len(records) >= total_available:
            break
        if max_records is not None and len(records) >= max_records:
            records = records[:max_records]
            break

        offset += page_size
        time.sleep(0.1)  # pequeña pausa para no saturar la API pública

    return records


def save_raw_json(records: List[Dict[str, Any]], path: str) -> None:
    """Guarda los registros crudos en un archivo JSON local (cache)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def load_raw_json(path: str) -> Optional[List[Dict[str, Any]]]:
    """Carga registros previamente cacheados, si el archivo existe."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_dataset_records(
    resource_id: str,
    use_cache: bool = True,
    cache_path: str = "data/raw_data.json",
    force_refresh: bool = False,
) -> List[Dict[str, Any]]:
    """
    Punto de entrada de alto nivel: intenta usar la cache local y, si no
    existe o se pide refrescar, consulta la API en vivo y actualiza la cache.
    """
    if use_cache and not force_refresh:
        cached = load_raw_json(cache_path)
        if cached:
            return cached

    records = fetch_all_records(resource_id)

    if use_cache:
        save_raw_json(records, cache_path)

    return records


if __name__ == "__main__":
    # Prueba manual: python api_client.py
    from config import RESOURCE_ID

    print(f"Consultando resource_id={RESOURCE_ID} ...")
    data = fetch_all_records(RESOURCE_ID, max_records=5)
    print(f"Se obtuvieron {len(data)} registros de prueba.")
    if data:
        print("Columnas detectadas:", list(data[0].keys()))
        print(json.dumps(data[0], ensure_ascii=False, indent=2))
