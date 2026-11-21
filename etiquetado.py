"""
ETIQUETADO AUTOMÁTICO (solo con TUS etiquetas)
==============================================
Lee data/etiquetas.json (la lista de etiquetas que tú creas en WordPress) y decide qué etiquetas lleva cada producto:
  - tipo "precio"  : se asigna por el precio (sin IA).  Campos: min, max (en euros; max vacío = sin límite).
  - tipo "criterio": la IA elige, SOLO entre las de la lista, las que encajan según el "criterio" que escribas (máx. 2).
  - tipo "manual"  : el robot no la asigna nunca (la pones tú, o viene de data/rankings.json).
Nunca se crea una etiqueta en WordPress: si falta, avisa en el log para que la crees tú.
Formato de cada etiqueta:  {"nombre": "...", "categoria": "smartwatch|smartphone", "tipo": "precio|criterio|manual",
                            "criterio": "frase", "min": 0, "max": 200, "pagina": "auto|manual"}
  pagina "auto"  -> el robot crea y mantiene la página Top 10 de esa etiqueta (generar_paginas_etiqueta.py).
  pagina "manual"-> la página es tuya: el robot no la toca.
"""
import os
import re
import json

RUTA = os.path.join(os.environ.get("CARPETA_DATOS", "data"), "etiquetas.json")
MAX_POR_CRITERIO = 2


def cargar():
    if not os.path.exists(RUTA):
        return []
    try:
        with open(RUTA, "r", encoding="utf-8") as fh:
            return [e for e in json.load(fh) if isinstance(e, dict) and e.get("nombre")]
    except (json.JSONDecodeError, OSError) as err:
        print(f"⚠️ No se pudo leer {RUTA}: {err}")
        return []


def activo():
    return bool(cargar())


def a_numero(texto):
    m = re.search(r"\d[\d.,]*", str(texto or ""))
    if not m:
        return None
    n = m.group(0).rstrip(".,")
    if "," in n and "." in n:
        n = n.replace(".", "").replace(",", ".") if n.rfind(",") > n.rfind(".") else n.replace(",", "")
    elif "," in n:
        n = n.replace(",", ".")
    elif n.count(".") > 1 or (n.count(".") == 1 and len(n.split(".")[1]) == 3):
        n = n.replace(".", "")
    try:
        return float(n)
    except ValueError:
        return None


def por_precio(categoria, precio):
    """Nombres de las etiquetas de precio que corresponden. Vacío si el precio no se entiende."""
    valor = a_numero(precio)
    if not valor:
        return []
    out = []
    for e in cargar():
        if e.get("tipo") != "precio" or e.get("categoria", "").lower() != categoria.lower():
            continue
        minimo = a_numero(e.get("min")) or 0
        maximo = a_numero(e.get("max")) if str(e.get("max", "")).strip() else None
        if valor >= minimo and (maximo is None or valor < maximo):
            out.append(e["nombre"])
    return out


def por_criterio(categoria, ficha_texto, llamar_ia):
    """La IA elige entre las etiquetas 'criterio' de la categoría. llamar_ia(prompt) -> dict o None."""
    opciones = [e for e in cargar() if e.get("tipo") == "criterio" and e.get("categoria", "").lower() == categoria.lower()]
    if not opciones or not llamar_ia:
        return []
    lista = "\n".join(f'- "{e["nombre"]}": {e.get("criterio", "")}' for e in opciones)
    prompt = (
        "Eres el editor de una web de comparativas. Decide en qué etiquetas encaja este producto.\n"
        f"Etiquetas disponibles (elige SOLO de esta lista, como máximo {MAX_POR_CRITERIO}, y solo si el criterio se cumple "
        "con los datos que se te dan; ante la duda NO pongas la etiqueta; si ninguna encaja, lista vacía):\n"
        f"{lista}\n\nDATOS DEL PRODUCTO:\n{ficha_texto[:3500]}\n\n"
        'Responde SOLO con JSON: {"etiquetas": ["nombre exacto", ...]}'
    )
    try:
        datos = llamar_ia(prompt)
    except Exception as err:   # la IA nunca debe impedir publicar
        print(f"   ⚠️ No se pudo consultar la IA para las etiquetas: {err}")
        return []
    validas = {e["nombre"].strip().lower(): e["nombre"] for e in opciones}
    elegidas = []
    for n in (datos or {}).get("etiquetas", []) if isinstance(datos, dict) else []:
        nombre = validas.get(str(n).strip().lower())
        if nombre and nombre not in elegidas:
            elegidas.append(nombre)
    return elegidas[:MAX_POR_CRITERIO]


def nombres_para(categoria, precio, ficha_texto, llamar_ia):
    nombres = por_precio(categoria, precio) + por_criterio(categoria, ficha_texto, llamar_ia)
    if not nombres:
        print("   ⚠️ Este producto se queda SIN etiqueta (precio no legible y ningún criterio encaja). Revísalo a mano.")
    return nombres


def precio_de_contenido(contenido, precio_registro=""):
    """Precio de una entrada: memoria del robot -> 'Precio orientativo' -> 'Precio ...: N €' -> primer 'N €' del texto."""
    if a_numero(precio_registro):
        return str(precio_registro)
    texto = re.sub(r"<[^>]+>", " ", contenido or "")
    texto = texto.replace("&nbsp;", " ").replace("&euro;", "€")
    for patron in (r"Precio\s+orientativo\s*:?\s*(?:desde\s*)?(\d[\d.,]*\s*(?:€|EUR|euros)?)",
                   r"Precio[^\d€]{0,40}?(\d[\d.,]*\s*€)",
                   r"(\d[\d.,]*\s*€)",
                   r"(€\s*\d[\d.,]*)"):
        m = re.search(patron, texto, flags=re.I)
        if m and a_numero(m.group(1)):
            return m.group(1)
    return ""
