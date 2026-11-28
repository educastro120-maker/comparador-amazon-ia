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


def fila_de_post(p, reg, medios=None):
    c = (p.get("content") or {}).get("raw", "")
    titulo = html.unescape((p.get("title") or {}).get("raw", ""))
    nombre = f"{reg['marca']} {reg['modelo']}".strip() if reg else nombre_desde_titulo(titulo)
    precio = etiquetado.precio_de_contenido(c, (reg or {}).get("precio", ""))
    amazon = gr.extraer_enlace_amazon(c) or (reg or {}).get("link_afiliado", "")   # manda el enlace que hay en la entrada
    imagen_entrada = (medios or {}).get(p.get("featured_media")) or gr.extraer_imagen(c)   # destacada > primera imagen de la entrada
    puntos = (reg or {}).get("puntuacion")
    if puntos is None:
        m2 = re.search(r"Puntuaci[oó]n:\s*(?:<[^>]+>\s*)*⭐\s*(?:<[^>]+>\s*)*([\d.,]+)", c)
        puntos = gr.a_numero(m2.group(1)) if m2 else 0
    try:
        puntos = float(puntos or 0)
    except (TypeError, ValueError):
        puntos = 0
    return {"nombre": nombre, "precio": gr.precio_es(precio), "amazon": amazon, "imagen": imagen_entrada or (reg or {}).get("imagen") or gr.imagen_de_biblioteca(nombre),
            "resumen": gr.recortar_frase((reg or {}).get("resumen", "") or gr.resumen_de_contenido(c), 150), "analisis": p.get("link", ""), "puntos": puntos,
            "status": p.get("status", ""), "fecha": p.get("date", ""), "motivo": (reg or {}).get("badge", "")}


def fecha_efectiva(p, reg):
    """Fecha para decidir si algo es novedad: la de lanzamiento (AAAA-MM) si se conoce; si no, la de la entrada."""
    fl = ((reg or {}).get("fecha_lanzamiento") or "").strip()
    if re.match(r"^\d{4}-\d{2}$", fl):
        return fl + "-15"
    return (p.get("date") or "")[:10]


def corte_novedad(meses):
    h = gr.datetime.now()
    m = h.year * 12 + h.month - 1 - meses
    return f"{m // 12:04d}-{m % 12 + 1:02d}-01"


def main():
    etiquetas = [e for e in etiquetado.cargar(con_paginas_extra=True) if e.get("pagina") == "auto"]
    if not etiquetas:
        print("ℹ️ No hay etiquetas con pagina=auto en data/etiquetas.json.")
        return 0
    paginas = gr.listar_paginas()
    tags = paginar("tags", {"_fields": "id,name"})
    posts = paginar("posts", {"status": "publish,draft,pending,private,future", "context": "edit", "_fields": "id,title,status,tags,link,content,featured_media,date"})
    if paginas is None or tags is None or posts is None:
        print("🛑 No se pudo leer WordPress: no se crea nada (para no duplicar).")
        return 1
    medios = {}
    ids_m = sorted({p.get("featured_media") for p in posts if p.get("featured_media")})
    for i in range(0, len(ids_m), 50):
        r = requests.get(f"{WP}/wp-json/wp/v2/media", params={"include": ",".join(map(str, ids_m[i:i + 50])), "per_page": 100, "_fields": "id,source_url"},
                         auth=AUTH, timeout=30)
        if r.status_code == 200:
            medios.update({m["id"]: m.get("source_url", "") for m in r.json()})
    registro = gr.cargar_json(gr.RUTA_PUBLICADOS, {})
    por_post = {r["post_id"]: r for r in registro.values() if isinstance(r, dict) and r.get("post_id")}
    id_tag = {html.unescape(t["name"]).strip().lower(): t["id"] for t in tags}
    por_slug = {p["slug"]: p for p in paginas}
    por_titulo = {gr.slugify((p.get("title") or {}).get("raw", "")): p for p in paginas}
    por_id = {p["id"]: p for p in paginas}
    errores = 0

    for e in etiquetas:
        nombre = e["nombre"]
        tid = id_tag.get(nombre.strip().lower())
        if not tid:
            tid = etiquetado.crear_etiqueta(WP, AUTH, nombre)
            if not tid:
                print(f"⚠️ {nombre}: la etiqueta no existe en WordPress y no se pudo crear (créala con ese nombre exacto).")
                continue
            id_tag[nombre.strip().lower()] = tid
            print(f"🏷️ Etiqueta creada en WordPress: «{nombre}».")
        meses_nov = int(e.get("novedad_meses") or 0)
        if meses_nov:   # página de novedades: entran los lanzados en los últimos N meses (etiquetados o no); salen al pasar ese plazo
            elegidos = []
            for p in posts:
                reg = por_post.get(p["id"])
                f = fecha_efectiva(p, reg)
                dentro = bool(f) and f >= corte_novedad(meses_nov)
                lanzamiento_ok = bool(reg and reg.get("fecha_lanzamiento")) and (not e.get("categoria") or (reg.get("categoria") or "") == e["categoria"])
                if dentro and (tid in p.get("tags", []) or lanzamiento_ok):
                    elegidos.append((p, reg, f))
            filas = []
            for p, reg, f in elegidos:
                fila = fila_de_post(p, reg, medios)
                fila["fecha"] = f
                filas.append(fila)
        else:
            filas = [fila_de_post(p, por_post.get(p["id"]), medios) for p in posts if tid in p.get("tags", [])]
        titulo = e.get("titulo_pagina") or nombre
        slug = gr.slugify(titulo)
        adoptada = por_id.get(e.get("pagina_id")) if e.get("pagina_id") else None   # página tuya que le encargas al robot
        if e.get("pagina_id") and not adoptada:
            print(f"⚠️ {nombre}: la página {e['pagina_id']} indicada en etiquetas.json no existe. Se ignora.")
        existente = adoptada or por_slug.get(slug) or por_titulo.get(slug)
        if not filas:
            print(f"— {nombre}: todavía no hay productos con esta etiqueta.")
            continue
        raw_existente = (existente.get("content") or {}).get("raw", "") if existente else ""
        if existente and MARCA.format(slug) not in raw_existente:
            # el listado de páginas no trae el contenido: se lee para saber si es de este robot
            r = requests.get(f"{WP}/wp-json/wp/v2/pages/{existente['id']}", params={"context": "edit", "_fields": "content"}, auth=AUTH, timeout=30)
            raw_existente = (r.json().get("content") or {}).get("raw", "") if r.status_code == 200 else ""
        suyo = bool(existente) and (bool(adoptada) or MARCA.format(slug) in raw_existente)
        if existente and not suyo:
            print(f"⏭️ {titulo}: ya existe una página tuya ({existente['status']}, ID {existente['id']}). No se toca.")
            continue
        rehacer_diseno = False
        if existente and existente["status"] == "publish" and e.get("actualizar"):
            rehacer_diseno = True   # página viva (p. ej. novedades): se rehace en cada ejecución
        elif existente and existente["status"] == "publish":
            if gr.MARCA_DISENO in raw_existente and gr.MARCA_INTRO_PROVISIONAL not in raw_existente:
                print(f"⏭️ {titulo}: ya publicada por el robot con el diseño actual. No se toca.")
                continue
            rehacer_diseno = True   # publicada con un diseño anterior: se rehace con el actual, sin despublicarla
            print(f"🎨 {titulo}: publicada con un diseño anterior o con la introducción provisional; se rehace.")

        if e.get("orden") == "recientes":   # más nuevas primero (por fecha de la entrada)
            filas.sort(key=lambda f: f["fecha"], reverse=True)
        else:
            filas.sort(key=lambda f: (-f["puntos"], f["nombre"]))
        minimo = int(e.get("minimo") or MINIMO)   # cuántas entradas publicadas hacen falta para publicar la página
        maximo = int(e.get("maximo") or MINIMO)   # "maximo": cuántos productos enseña la página (por defecto 10)
        top = filas[:maximo]
        for n, f in enumerate(top, 1):
            f["n"] = n
            f["amazon"] = f["amazon"] or f"https://www.amazon.es/s?k={requests.utils.quote(f['nombre'])}&tag={gr.AMAZON_TAG}"
        publicadas = sum(1 for f in top if f["status"] == "publish")
        completa = len(top) >= minimo and publicadas >= minimo
        rk = {"slug": slug, "titulo": titulo, "categoria": e.get("categoria", ""), "intro": e.get("intro") or f"Estos son los productos de nuestra selección «{nombre}». Los analizamos uno a uno y te dejamos el enlace a Amazon.",
              "criterio": e.get("criterio") or "Selección según las características y el precio de cada producto.",
              "datos_de": gr.datetime.now().strftime("%d/%m/%Y")}
        contenido = MARCA.format(slug) + gr.construir_html(rk, top)
        estado = "publish" if (rehacer_diseno or (completa and PUBLICAR)) else "draft"
        if existente and raw_existente and not os.path.exists(os.path.join(gr.CARPETA_COPIAS_PAG, f"{existente['id']}.html")):
            os.makedirs(gr.CARPETA_COPIAS_PAG, exist_ok=True)
            with open(os.path.join(gr.CARPETA_COPIAS_PAG, f"{existente['id']}.html"), "w", encoding="utf-8") as f:
                f.write(raw_existente)   # copia de seguridad de la página tal como estaba
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
        faltan = max(minimo - len(top), 0)
        sin_publicar = len(top) - publicadas
        print(f"✅ {titulo}: página {accion} como {'PUBLICADA' if estado == 'publish' else 'borrador'} "
              f"({len(top)}/{minimo if minimo != MINIMO else MINIMO} productos{f'; faltan {faltan}' if faltan else ''}{f'; {sin_publicar} entradas aún sin publicar' if sin_publicar else ''}).")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
