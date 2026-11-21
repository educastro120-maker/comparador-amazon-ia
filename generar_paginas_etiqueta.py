"""
PÁGINAS TOP 10 POR ETIQUETA (automáticas)
=========================================
Para cada etiqueta de data/etiquetas.json con "pagina": "auto":
  - Si hay al menos 1 entrada con esa etiqueta, crea la página "Top 10 ..." como BORRADOR (así ves de un vistazo cuáles
    siguen incompletas: el borrador indica cuántos productos faltan).
  - Cada ejecución actualiza ese borrador con los productos que ya tienen la etiqueta (máx. 10, por puntuación).
  - Cuando hay 10 entradas PUBLICADAS con la etiqueta, la página se PUBLICA (PUBLICAR_AL_COMPLETAR=no para dejarla en borrador).
  - Una vez publicada por el robot no se vuelve a tocar. Una página que ya existe con ese título o ese slug y que NO es de
    este robot (la hiciste tú) tampoco se toca.
Sin IA ni gasto de cuota. Reutiliza el diseño de generar_rankings.py.
"""
import os, re, sys, html
import requests

import generar_rankings as gr
import etiquetado

PUBLICAR = os.environ.get("PUBLICAR_AL_COMPLETAR", "si").strip().lower() != "no"
MINIMO = int(os.environ.get("TOP_N", "10"))
WP, AUTH = gr.WP_URL, (gr.WP_USER, gr.WP_APP_PASSWORD)
MARCA = "<!-- tc-top:{} -->"


def paginar(ruta, params):
    out, n = [], 1
    while n <= 40:
        r = requests.get(f"{WP}/wp-json/wp/v2/{ruta}", params={"per_page": 100, "page": n, **params}, auth=AUTH, timeout=60)
        if r.status_code == 400 and n > 1:
            break
        if r.status_code != 200:
            return None
        out += r.json()
        if len(r.json()) < 100:
            break
        n += 1
    return out


def nombre_desde_titulo(titulo):
    t = re.sub(r"^\s*an[aá]lisis y opini[oó]n\s*:\s*", "", html.unescape(titulo), flags=re.I)
    t = re.split(r"\s[-–—|:]\s|\s*[,(]\s*", t)[0]
    t = re.split(r"\s+(?:smartwatch|reloj|smartphone|m[oó]vil|tel[eé]fono|pulsera|con|para)\b", t, flags=re.I)[0]
    return " ".join(t.split()[:6]).strip()


def fila_de_post(p, reg):
    c = (p.get("content") or {}).get("raw", "")
    titulo = html.unescape((p.get("title") or {}).get("raw", ""))
    nombre = f"{reg['marca']} {reg['modelo']}".strip() if reg else nombre_desde_titulo(titulo)
    m = re.search(r"Precio orientativo:\s*(?:<[^>]+>\s*)*([^<|]+)", c)
    precio = (reg or {}).get("precio") or (m.group(1) if m else "")
    m = re.search(r'href="([^"]+)"[^>]*>\s*Ver precio actualizado en Amazon', c)
    amazon = (reg or {}).get("link_afiliado") or (m.group(1) if m else "")
    m = re.search(r'<img[^>]+src="([^"]+)"', c)
    puntos = (reg or {}).get("puntuacion")
    if puntos is None:
        m2 = re.search(r"Puntuaci[oó]n:\s*(?:<[^>]+>\s*)*⭐\s*(?:<[^>]+>\s*)*([\d.,]+)", c)
        puntos = gr.a_numero(m2.group(1)) if m2 else 0
    try:
        puntos = float(puntos or 0)
    except (TypeError, ValueError):
        puntos = 0
    return {"nombre": nombre, "precio": gr.precio_es(precio), "amazon": amazon, "imagen": (reg or {}).get("imagen") or (m.group(1) if m else ""),
            "resumen": gr.recortar_frase((reg or {}).get("resumen", "")), "analisis": p.get("link", ""), "puntos": puntos,
            "status": p.get("status", ""), "motivo": (reg or {}).get("badge", "")}


def main():
    etiquetas = [e for e in etiquetado.cargar() if e.get("pagina") == "auto"]
    if not etiquetas:
        print("ℹ️ No hay etiquetas con pagina=auto en data/etiquetas.json.")
        return 0
    paginas = gr.listar_paginas()
    tags = paginar("tags", {"_fields": "id,name"})
    posts = paginar("posts", {"status": "publish,draft,pending,private,future", "context": "edit", "_fields": "id,title,status,tags,link,content"})
    if paginas is None or tags is None or posts is None:
        print("🛑 No se pudo leer WordPress: no se crea nada (para no duplicar).")
        return 1
    registro = gr.cargar_json(gr.RUTA_PUBLICADOS, {})
    por_post = {r["post_id"]: r for r in registro.values() if isinstance(r, dict) and r.get("post_id")}
    id_tag = {html.unescape(t["name"]).strip().lower(): t["id"] for t in tags}
    por_slug = {p["slug"]: p for p in paginas}
    por_titulo = {gr.slugify((p.get("title") or {}).get("raw", "")): p for p in paginas}
    errores = 0

    for e in etiquetas:
        nombre = e["nombre"]
        tid = id_tag.get(nombre.strip().lower())
        if not tid:
            print(f"⚠️ {nombre}: la etiqueta no existe en WordPress (créala con ese nombre exacto).")
            continue
        filas = [fila_de_post(p, por_post.get(p["id"])) for p in posts if tid in p.get("tags", [])]
        titulo = e.get("titulo_pagina") or nombre
        slug = gr.slugify(titulo)
        existente = por_slug.get(slug) or por_titulo.get(slug)
        if not filas:
            print(f"— {nombre}: todavía no hay productos con esta etiqueta.")
            continue
        suyo = bool(existente) and MARCA.format(slug) in (existente.get("content") or {}).get("raw", "")
        if existente and not suyo:
            # el listado de páginas no trae el contenido: se lee para saber si es de este robot
            r = requests.get(f"{WP}/wp-json/wp/v2/pages/{existente['id']}", params={"context": "edit", "_fields": "content"}, auth=AUTH, timeout=30)
            suyo = r.status_code == 200 and MARCA.format(slug) in (r.json().get("content") or {}).get("raw", "")
        if existente and not suyo:
            print(f"⏭️ {titulo}: ya existe una página tuya ({existente['status']}, ID {existente['id']}). No se toca.")
            continue
        if existente and existente["status"] == "publish":
            print(f"⏭️ {titulo}: ya publicada por el robot. No se vuelve a tocar.")
            continue

        filas.sort(key=lambda f: (-f["puntos"], f["nombre"]))
        top = filas[:MINIMO]
        for n, f in enumerate(top, 1):
            f["n"] = n
            f["amazon"] = f["amazon"] or f"https://www.amazon.es/s?k={requests.utils.quote(f['nombre'])}&tag={gr.AMAZON_TAG}"
        publicadas = sum(1 for f in top if f["status"] == "publish")
        completa = len(top) >= MINIMO and publicadas >= MINIMO
        rk = {"intro": e.get("intro") or f"Estos son los productos de nuestra selección «{nombre}». Los analizamos uno a uno y te dejamos el enlace a Amazon.",
              "criterio": e.get("criterio") or "Selección según las características y el precio de cada producto.",
              "datos_de": gr.datetime.now().strftime("%d/%m/%Y")}
        contenido = MARCA.format(slug) + gr.construir_html(rk, top)
        estado = "publish" if (completa and PUBLICAR) else "draft"
        try:
            if existente:
                r = requests.post(f"{WP}/wp-json/wp/v2/pages/{existente['id']}", json={"content": contenido, "status": estado}, auth=AUTH, timeout=60)
                ok, accion = r.status_code == 200, "actualizada"
            else:
                r = requests.post(f"{WP}/wp-json/wp/v2/pages", json={"title": titulo, "content": contenido, "status": estado, "slug": slug}, auth=AUTH, timeout=60)
                ok, accion = r.status_code == 201, "creada"
        except requests.RequestException as err:
            print(f"❌ {titulo}: {err}")
            errores += 1
            continue
        if not ok:
            print(f"❌ {titulo}: WordPress respondió {r.status_code}: {r.text[:200]}")
            errores += 1
            continue
        faltan = max(MINIMO - len(top), 0)
        sin_publicar = len(top) - publicadas
        print(f"✅ {titulo}: página {accion} como {'PUBLICADA' if estado == 'publish' else 'borrador'} "
              f"({len(top)}/{MINIMO} productos{f'; faltan {faltan}' if faltan else ''}{f'; {sin_publicar} entradas aún sin publicar' if sin_publicar else ''}).")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
