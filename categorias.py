"""
CATEGORÍAS DEL ROBOT (data/categorias.json)
===========================================
Una sola lista, editable por ti, que dice qué categorías trabaja el robot y cómo:
  "clave": {"nombre": "Nombre de la categoría en WordPress", "descripcion": "cómo se busca en internet",
            "activa": true/false,            # false = el robot no descubre ni publica esa categoría
            "cola_minima": 12,                # modo automático: si ya hay tantos productos pendientes, hoy no se busca más
            "marcas_por_ejecucion": 2,        # cuántas marcas/temas busca cada día
            "marcas": ["Apple", ...],         # se busca "<marca> <descripcion> ..." (una marca por búsqueda)
            "consultas": ["mejores monitores gaming 2026", ...]   # alternativa sin marcas: búsquedas libres
            "secciones": ["Pantalla", "Conectividad", ...]}       # opcional: secciones de la ficha técnica
Una categoría que no esté en el archivo también funciona si la pides a mano (DESCUBRIR_CATEGORIAS): usa búsquedas genéricas.
"""
import os
import json

RUTA = os.path.join(os.environ.get("CARPETA_DATOS", "data"), "categorias.json")

_POR_DEFECTO = {
    "smartphone": {"nombre": "Smartphones", "descripcion": "smartphones (móviles)", "activa": True, "marcas_por_ejecucion": 2,
                   "marcas": ["Apple", "Samsung", "Xiaomi", "POCO", "Redmi", "Google Pixel", "Motorola", "OnePlus", "OPPO", "vivo",
                              "realme", "Honor", "Huawei", "Nothing", "ASUS", "Sony", "HMD", "ZTE nubia", "Tecno", "Infinix"]},
    "smartwatch": {"nombre": "Smartwatches", "descripcion": "smartwatches y relojes deportivos con GPS", "activa": True,
                   "marcas_por_ejecucion": 1,
                   "marcas": ["Apple", "Samsung", "Garmin", "Huawei", "Xiaomi", "Amazfit", "COROS", "Suunto", "Polar", "Google Pixel Watch",
                              "Honor", "OnePlus", "Withings", "Mibro", "CMF by Nothing", "OPPO", "realme", "Fossil", "Casio", "Fitbit"]},
}


def cargar():
    datos = dict(_POR_DEFECTO)
    if os.path.exists(RUTA):
        try:
            with open(RUTA, "r", encoding="utf-8") as fh:
                for clave, cfg in json.load(fh).items():
                    if isinstance(cfg, dict) and not clave.startswith("_"):
                        datos[clave.strip().lower()] = {**_POR_DEFECTO.get(clave.strip().lower(), {}), **cfg}
        except (json.JSONDecodeError, OSError, AttributeError) as err:
            print(f"⚠️ No se pudo leer {RUTA}: {err}. Se usan las categorías por defecto.")
    return datos


def info(clave):
    """Configuración de una categoría; si no está en el archivo, una genérica con ese nombre."""
    clave = str(clave).strip().lower()
    cfg = cargar().get(clave)
    if cfg:
        return cfg
    return {"nombre": clave.capitalize(), "descripcion": clave, "activa": True, "marcas_por_ejecucion": 1, "marcas": []}


def nombre_wp(clave):
    return info(clave).get("nombre") or str(clave).capitalize()


def esta_pausada(clave):
    cfg = cargar().get(str(clave).strip().lower())
    return bool(cfg) and cfg.get("activa") is False
