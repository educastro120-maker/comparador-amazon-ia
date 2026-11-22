"""
GENERAR RANKINGS (páginas Top 10 en borrador)
=============================================
Crea en WordPress, como BORRADOR, una PÁGINA por cada ranking definido en data/rankings.json:
  - Resumen rápido (tabla) + ficha corta de cada producto, con su botón de Amazon y el enlace a su entrada.
  - Introducción con palabras clave en negrita (la redacta Gemini una vez por página y se guarda en data/intros.json),
    fichas compactas en cuadrícula, fecha de los datos y avisos de afiliado y de precios.
  - El botón de Amazon usa SIEMPRE el enlace que tengas puesto en la entrada del producto; la imagen sale de la entrada
    (imagen destacada o primera imagen) y, si no hay, de la biblioteca de medios.
  - UNIFICAR="id1,id2" (o "todos") + UNIFICAR_MODO=prueba|si|restaurar: rehace con este mismo diseño las páginas que ya
    tenías (guarda antes una copia en data/copias_paginas/ y se puede restaurar).

Solo usa Gemini (1 llamada, una única vez por página) para la introducción; el resto lo monta con los datos que ya tiene.

Reglas de seguridad (para no estropear lo que ya tienes):
  - NO toca una página que ya existe (mismo título o mismo slug): la salta. Así no duplica tus páginas hechas a mano.
  - Solo crea la página cuando TODAS las entradas de sus productos ya existen en WordPress
    (para no enlazar a entradas que no existen). Si faltan, espera a la próxima ejecución.
  - Siempre en BORRADOR (cámbialo con ESTADO_PAGINAS=publish bajo tu responsabilidad).
  - Un ranking con "crear_pagina": false se ignora (por defecto, los que ya has creado a mano).
  - FORZAR_RANKINGS="id1,id2" (o "todos") genera un borrador aunque el ranking esté marcado como creado a mano;
    si la página ya existe como BORRADOR de este robot, la actualiza; si está publicada, nunca la toca.

LÍMITE: la elección y el orden de los 10 productos de cada ranking los defines tú en data/rankings.json.
El robot construye la página, enlaza y etiqueta; no decide qué producto es el mejor.
"""

import os
import re
import sys
import json
import html
import unicodedata
import urllib.parse
from datetime import datetime
import requests

WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER", "").strip()
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "").strip()
if not (WP_URL and WP_USER and WP_APP_PASSWORD):
    sys.exit("❌ Faltan WP_URL, WP_USER o WP_APP_PASSWORD (secretos de GitHub).")

AMAZON_TAG = os.environ.get("AMAZON_TAG", "topcomparad00-21")
CARPETA_DATOS = os.environ.get("CARPETA_DATOS", "data")
RUTA_RANKINGS = os.path.join(CARPETA_DATOS, "rankings.json")
RUTA_PUBLICADOS = os.path.join(CARPETA_DATOS, "publicados.json")
ESTADO_PAGINAS = os.environ.get("ESTADO_PAGINAS", "draft")
UNIFICAR = {x.strip() for x in os.environ.get("UNIFICAR", "").split(",") if x.strip()}
UNIFICAR_MODO = os.environ.get("UNIFICAR_MODO", "prueba").strip().lower()
CARPETA_COPIAS_PAG = os.path.join(CARPETA_DATOS, "copias_paginas")
FORZAR = {x.strip() for x in os.environ.get("FORZAR_RANKINGS", "").split(",") if x.strip()}
PREFIJOS_LINK_CORTO = ("https://link.amazon/", "https://amzn.to/", "https://amzn.eu/")
RUTA_INTROS = os.path.join(CARPETA_DATOS, "intros.json")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
INTRO_IA = os.environ.get("INTRO_IA", "si").strip().lower() != "no"
REGENERAR_INTROS = os.environ.get("REGENERAR_INTROS", "").strip().lower() in ("si", "1", "true")
MODELOS_INTRO = [m.strip() for m in os.environ.get("INTRO_MODELS", "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.8-flash").split(",") if m.strip()]
AVISO_ARRIBA = os.environ.get("AVISO_ARRIBA", "si").strip().lower() != "no"
FRASE_AFILIADO = ("Como afiliado de Amazon, obtengo ingresos por las compras adscritas que cumplen los requisitos aplicables, "
                  "sin que esto suponga ningún coste adicional para ti.")


def slugify(texto):
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def cargar_json(ruta, defecto):
    if not os.path.exists(ruta):
        return defecto
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as err:
        print(f"⚠️ No se pudo leer {ruta}: {err}")
        return defecto


esc = lambda t: html.escape(str(t if t is not None else ""), quote=True)


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


def precio_es(texto):
    n = a_numero(texto)
    if not n:
        return "Consultar"
    return (f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €").replace(",00 €", " €")


def enlace_amazon(miembro, reg):
    link = (reg or {}).get("link_afiliado", "")
    if link.startswith(PREFIJOS_LINK_CORTO):
        return link
    asin = (miembro.get("asin") or "").strip().upper()
    if re.match(r"^[A-Z0-9]{10}$", asin):
        return f"https://www.amazon.es/dp/{asin}?tag={AMAZON_TAG}"
    return link or f"https://www.amazon.es/s?k={urllib.parse.quote_plus(miembro['busqueda'])}&tag={AMAZON_TAG}"


def extraer_enlace_amazon(contenido):
    """Enlace de Amazon que hay en la entrada (el botón 'Ver precio...'): es el que tú has puesto, y manda sobre cualquier otro."""
    c = contenido or ""
    for m in re.finditer(r'<a\b[^>]*?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', c, re.S | re.I):
        href, texto = html.unescape(m.group(1)), re.sub(r"<[^>]+>", " ", m.group(2)).lower()
        if re.search(r"amzn\.|link\.amazon|amazon\.", href, re.I) and ("amazon" in texto or "precio" in texto):
            return href
    for m in re.finditer(r'href=["\']([^"\']+)["\']', c, re.I):
        href = html.unescape(m.group(1))
        if re.search(r"amzn\.(to|eu)|link\.amazon|amazon\.[a-z.]+/(dp|gp)/", href, re.I):
            return href
    return ""


def extraer_imagen(contenido):
    m = re.search(r'<img\b[^>]*?src=["\']([^"\']+)["\']', contenido or "", re.I)
    return html.unescape(m.group(1)) if m else ""


_cache_medios = {}


def imagen_de_biblioteca(nombre):
    """Último recurso: busca en la biblioteca de medios una imagen cuyo nombre contenga todas las palabras del modelo."""
    if nombre in _cache_medios:
        return _cache_medios[nombre]
    resultado = ""
    palabras = [p for p in slugify(nombre).split("-") if p]
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/media", params={"search": nombre, "per_page": 20, "media_type": "image",
                                                                  "_fields": "id,slug,source_url,title"},
                         auth=(WP_USER, WP_APP_PASSWORD), timeout=30)
        if r.status_code == 200:
            for med in r.json():
                texto = slugify(f"{med.get('slug', '')} {(med.get('title') or {}).get('rendered', '')}")
                if palabras and all(p in texto.split("-") for p in palabras):
                    resultado = med.get("source_url", "")
                    break
    except (requests.RequestException, ValueError):
        pass
    _cache_medios[nombre] = resultado
    return resultado


def recortar_frase(texto, limite=300):
    texto = " ".join(str(texto or "").split())
    if len(texto) <= limite:
        return texto
    frases = re.split(r"(?<=[.!?])\s+", texto)
    salida = ""
    for f in frases:
        if len(salida) + len(f) + 1 > limite:
            break
        salida = (salida + " " + f).strip()
    return salida or texto[:limite].rsplit(" ", 1)[0] + "…"


def listar_paginas():
    """Todas las páginas de WordPress (cualquier estado). Devuelve None si no se pudo leer (para no arriesgar duplicados)."""
    paginas, n = [], 1
    while n <= 20:
        try:
            r = requests.get(f"{WP_URL}/wp-json/wp/v2/pages",
                             params={"per_page": 100, "page": n, "status": "publish,draft,pending,private,future",
                                     "context": "edit", "_fields": "id,slug,status,title"},
                             auth=(WP_USER, WP_APP_PASSWORD), timeout=30)
        except requests.RequestException as err:
            print(f"❌ No se pudo leer la lista de páginas: {err}")
            return None
        if r.status_code == 400 and n > 1:
            break   # página fuera de rango
        if r.status_code != 200:
            print(f"❌ WordPress respondió {r.status_code} al listar páginas: {r.text[:200]}")
            return None
        lote = r.json()
        paginas += lote
        if len(lote) < 100:
            break
        n += 1
    return paginas


def datos_de_entradas(ids):
    """Estado, enlace, imagen y enlace de Amazon actuales de cada entrada (lo que hay ahora en WordPress, no en la memoria)."""
    info, medios = {}, {}
    ids = sorted(set(ids))
    for i in range(0, len(ids), 50):
        trozo = ids[i:i + 50]
        try:
            r = requests.get(f"{WP_URL}/wp-json/wp/v2/posts",
                             params={"include": ",".join(map(str, trozo)), "per_page": 100, "context": "edit",
                                     "status": "publish,draft,pending,private,future",
                                     "_fields": "id,link,status,featured_media,content"},
                             auth=(WP_USER, WP_APP_PASSWORD), timeout=60)
            if r.status_code == 200:
                for p in r.json():
                    c = (p.get("content") or {}).get("raw", "")
                    info[p["id"]] = {"link": p.get("link", ""), "status": p.get("status", ""), "amazon": extraer_enlace_amazon(c),
                                     "imagen": extraer_imagen(c), "destacada": p.get("featured_media") or 0}
        except (requests.RequestException, ValueError) as err:
            print(f"   ⚠️ No se pudo comprobar el estado de algunas entradas: {err}")
    ids_medios = sorted({v["destacada"] for v in info.values() if v["destacada"]})
    for i in range(0, len(ids_medios), 50):
        try:
            r = requests.get(f"{WP_URL}/wp-json/wp/v2/media", params={"include": ",".join(map(str, ids_medios[i:i + 50])), "per_page": 100,
                                                                      "_fields": "id,source_url"}, auth=(WP_USER, WP_APP_PASSWORD), timeout=30)
            if r.status_code == 200:
                medios.update({m["id"]: m.get("source_url", "") for m in r.json()})
        except (requests.RequestException, ValueError):
            pass
    for v in info.values():
        v["imagen"] = medios.get(v["destacada"]) or v["imagen"]   # la imagen destacada manda; si no, la primera de la entrada
    return info


def buscar_entrada(m):
    """Busca en WordPress la entrada de un producto cuando la que recordaba el robot ya no existe (p. ej. un duplicado borrado)."""
    marca, modelo = slugify(m["marca"]), slugify(m["modelo_corto"])
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/posts",
                         params={"search": f"{m['marca']} {m['modelo_corto']}", "per_page": 20, "status": "publish,draft,pending,private,future",
                                 "_fields": "id,link,status,title"}, auth=(WP_USER, WP_APP_PASSWORD), timeout=30)
        if r.status_code != 200:
            return None
        candidatas = []
        for p in r.json():
            t = slugify(html.unescape((p.get("title") or {}).get("rendered", "")))
            if marca in t and modelo in t:
                candidatas.append(p)
        candidatas.sort(key=lambda p: (p["status"] != "publish", p["id"]))
        return candidatas[0] if candidatas else None
    except (requests.RequestException, ValueError):
        return None


def reparar_registro(rankings, registro, guardar):
    """Si la entrada que el robot recordaba ya no existe, la sustituye por la entrada actual del mismo producto."""
    pares, fijadas = [], []
    for rk in rankings:
        for m in rk.get("miembros", []):
            clave = slugify(f"{m['marca']} {m['modelo_corto']}")
            reg = registro.get(clave)
            if isinstance(reg, dict) and reg.get("post_id"):
                if m.get("post_id") and reg["post_id"] != m["post_id"]:   # entrada fijada a mano en rankings.json
                    print(f"📌 {m['marca']} {m['modelo_corto']}: se usa la entrada {m['post_id']} (fijada en rankings.json).")
                    reg["post_id"], reg["url_post"] = m["post_id"], ""
                    fijadas.append(1)
                pares.append((m, reg))
    vivos = datos_de_entradas([reg["post_id"] for _, reg in pares])
    cambios = len(fijadas)
    for m, reg in pares:
        if reg["post_id"] in vivos:
            continue
        nombre = f"{m['marca']} {m['modelo_corto']}"
        n = buscar_entrada(m)
        if n:
            print(f"🔧 {nombre}: la entrada {reg['post_id']} ya no existe; se usa la entrada {n['id']}.")
            reg["post_id"], reg["url_post"] = n["id"], n.get("link", "")
            cambios += 1
        else:
            print(f"⚠️ {nombre}: la entrada {reg['post_id']} ya no existe y no encuentro otra con ese nombre.")
    if cambios and guardar:
        with open(RUTA_PUBLICADOS, "w", encoding="utf-8") as f:
            json.dump(registro, f, ensure_ascii=False, indent=1)
        print(f"💾 Memoria del robot actualizada ({cambios} entradas).")
    return cambios


def fila_de_miembro(n, m, reg, post):
    """Una fila del Top 10. Enlace de Amazon: el de la entrada > memoria > asin > búsqueda. Imagen: entrada > memoria > biblioteca."""
    nombre = f"{m['marca']} {m['modelo_corto']}"
    amazon = post.get("amazon") or enlace_amazon(m, reg)
    imagen = post.get("imagen") or reg.get("imagen", "") or m.get("imagen", "") or imagen_de_biblioteca(nombre)
    return {"n": n, "nombre": nombre, "rotulo": m.get("rotulo", ""), "motivo": m.get("motivo", ""), "precio": precio_es(m.get("precio")),
            "amazon": amazon, "imagen": imagen, "resumen": recortar_frase(reg.get("resumen", ""), 150),
            "analisis": post.get("link") or reg.get("url_post", "")}


def negritas(texto):
    """Escapa el texto y convierte **palabra** en negrita (lo único de formato que se admite)."""
    t = esc(texto)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)


def _intro_valida(t):
    return isinstance(t, str) and 250 <= len(t) <= 1100 and t.count("**") >= 6 and "\n\n" not in t.strip()


def _intro_con_ia(titulo, categoria, criterio):
    if not (GEMINI_API_KEY and INTRO_IA):
        return ""
    try:
        from google import genai
        from google.genai import types
        cliente = genai.Client(api_key=GEMINI_API_KEY, http_options={"timeout": 90000})
    except Exception as e:
        print(f"   ⚠️ Introducción: no se pudo iniciar Gemini ({type(e).__name__}).")
        return ""
    prompt = f"""Escribe el texto introductorio de una página web española llamada «{titulo}» (categoría: {categoria or 'tecnología'}) de un comparador con enlaces de afiliado de Amazon.
Criterio de la selección: {criterio or 'según características y precio'}.
Reglas:
- Un solo párrafo de 70 a 110 palabras, en español de España, tono cercano y claro.
- Marca entre 5 y 7 palabras clave o expresiones clave con **doble asterisco** (ej.: **autonomía**, **GPS**). Nada más de formato: sin listas, sin títulos, sin emojis.
- Explica para quién es útil la selección y qué puede comparar el lector (características y precios).
- NO digas que hemos probado, testeado o analizado los productos en persona. NO inventes cifras, modelos ni datos.
- No prometas «mejores ofertas» ni precios; basta con invitar a consultar el precio actualizado en Amazon.
Devuelve solo el párrafo."""
    for modelo in MODELOS_INTRO:
        try:
            r = cliente.models.generate_content(model=modelo, contents=prompt,
                                                config=types.GenerateContentConfig(temperature=0.6, max_output_tokens=1024))
            t = re.sub(r"\s+", " ", (r.text or "")).strip().strip('"«»')
            if _intro_valida(t):
                return t
            print(f"   ⚠️ Introducción con {modelo}: formato no válido, se prueba otro modelo.")
        except Exception as e:
            print(f"   ⚠️ Introducción con {modelo}: {type(e).__name__} -> {str(e)[:120]}")
    return ""


def texto_introduccion(rk):
    """Introducción con palabras clave en negrita. Se genera una vez por página y se guarda en data/intros.json."""
    clave = rk.get("slug") or slugify(rk.get("titulo", ""))
    guardadas = cargar_json(RUTA_INTROS, {})
    if clave in guardadas and not REGENERAR_INTROS:
        return guardadas[clave]
    titulo = rk.get("titulo", "")
    t = _intro_con_ia(titulo, rk.get("categoria", ""), rk.get("criterio", ""))
    if t:
        guardadas[clave] = t
        os.makedirs(CARPETA_DATOS, exist_ok=True)
        with open(RUTA_INTROS, "w", encoding="utf-8") as f:
            json.dump(guardadas, f, ensure_ascii=False, indent=1)
        print(f"   ✍️ Introducción generada para «{titulo}».")
        return t
    # Sin IA: se usa la que haya en rankings.json o una genérica (sin guardarla, para reintentar la próxima vez)
    if rk.get("intro"):
        return rk["intro"]
    tema = re.sub(r"\s*\(\d{4}\)\s*$", "", re.sub(r"^Top\s*\d+\s*", "", titulo, flags=re.I)).strip() or "esta categoría"
    return (f"Si buscas **{tema}**, aquí tienes nuestra selección. Puedes **comparar** de un vistazo sus características y su "
            f"**precio orientativo**, leer el análisis de cada producto y consultar el **precio actualizado en Amazon**.")


def construir_html(rk, filas):
    hoy = datetime.now().strftime("%d/%m/%Y")
    caja = "border:1px solid #e2e8f0;border-radius:12px;padding:18px;margin:0 0 18px 0;background:#fff;"
    boton = ("background-color:#ffa41c;color:#111;text-decoration:none;font-weight:bold;padding:10px 18px;border-radius:8px;"
             "border:1px solid #ff8f00;display:inline-block;")
    h = ['<div style="max-width:1100px;margin:0 auto;font-family:system-ui,-apple-system,sans-serif;color:#1e293b;">']
    h.append(f'<p style="font-size:1.05em;line-height:1.7;">{negritas(texto_introduccion(rk))}</p>')
    if AVISO_ARRIBA:
        h.append(f'<p style="font-size:.8em;color:#64748b;line-height:1.5;margin:0 0 6px;">Esta página contiene enlaces de afiliado de Amazon.es. {esc(FRASE_AFILIADO)}</p>')

    # Resumen rápido
    h.append('<h2 style="margin-top:28px;">Resumen rápido</h2>')
    h.append('<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:.95em;">')
    h.append('<tr style="background:#0f172a;color:#fff;"><th style="padding:8px;text-align:left;">#</th>'
             '<th style="padding:8px;text-align:left;">Producto</th><th style="padding:8px;text-align:left;">Destacado</th>'
             '<th style="padding:8px;text-align:right;">Precio orientativo</th><th style="padding:8px;"></th></tr>')
    for f in filas:
        destacado = (f'<strong>{esc(f["rotulo"])}</strong><br>' if f.get("rotulo") else "") + esc(f.get("motivo", ""))
        h.append(f'<tr style="border-bottom:1px solid #e2e8f0;"><td style="padding:8px;font-weight:bold;">{f["n"]}</td>'
                 f'<td style="padding:8px;"><a href="#puesto-{f["n"]}">{esc(f["nombre"])}</a></td>'
                 f'<td style="padding:8px;">{destacado}</td>'
                 f'<td style="padding:8px;text-align:right;white-space:nowrap;">{esc(f["precio"])}</td>'
                 f'<td style="padding:8px;text-align:center;"><a href="{esc(f["amazon"])}" target="_blank" '
                 f'rel="sponsored nofollow noopener" style="font-weight:bold;">Ver en Amazon</a></td></tr>')
    h.append("</table></div>")

    # Fichas compactas: cuadrícula con varias por línea
    h.append('<h2 style="margin-top:28px;">Análisis de cada producto</h2>')
    h.append('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px;align-items:stretch;">')
    boton_s = ("background-color:#ffa41c;color:#111;text-decoration:none;font-weight:bold;padding:7px 12px;border-radius:8px;"
               "border:1px solid #ff8f00;display:inline-block;font-size:.85em;")
    for f in filas:
        img = ""
        if f.get("imagen"):
            img = (f'<div style="text-align:center;"><img src="{esc(f["imagen"])}" alt="{esc(f["nombre"])}" loading="lazy" '
                   f'referrerpolicy="no-referrer" style="height:110px;max-width:100%;object-fit:contain;"></div>')
            if f.get("analisis"):
                img = f'<a href="{esc(f["analisis"])}" title="Leer el análisis de {esc(f["nombre"])}" style="text-decoration:none;">{img}</a>'
        rot = (f'<span style="background:#ff9900;color:#fff;font-weight:bold;padding:2px 8px;border-radius:10px;font-size:.7em;'
               f'margin-left:6px;white-space:nowrap;">{esc(f["rotulo"])}</span>') if f.get("rotulo") else ""
        nombre_h = (f'<a href="{esc(f["analisis"])}" style="color:inherit;text-decoration:none;">{esc(f["nombre"])}</a>'
                    if f.get("analisis") else esc(f["nombre"]))
        resumen = f'<p style="margin:0;font-size:.82em;line-height:1.45;color:#475569;">{esc(f["resumen"])}</p>' if f.get("resumen") else ""
        analisis = (f'<a href="{esc(f["analisis"])}" style="font-size:.82em;display:block;margin-top:6px;">Leer el análisis →</a>') if f.get("analisis") else ""
        h.append(f'<div id="puesto-{f["n"]}" style="border:1px solid #e2e8f0;border-radius:10px;padding:12px;background:#fff;'
                 f'display:flex;flex-direction:column;gap:6px;">{img}'
                 f'<h3 style="margin:0;font-size:1em;line-height:1.3;">{f["n"]}. {nombre_h}{rot}</h3>'
                 f'<p style="margin:0;font-size:.85em;font-weight:600;color:#334155;">{esc(f.get("motivo", ""))}</p>{resumen}'
                 f'<div style="margin-top:auto;padding-top:6px;"><div style="margin-bottom:6px;"><span style="color:#64748b;font-size:.78em;">Precio orientativo:</span> '
                 f'<strong style="color:#b12704;">{esc(f["precio"])}</strong></div>'
                 f'<a href="{esc(f["amazon"])}" target="_blank" rel="sponsored nofollow noopener" style="{boton_s}">Ver precio en Amazon 🛒</a>{analisis}</div></div>')
    h.append("</div>")

    h.append(f'<p style="font-size:.85em;color:#64748b;line-height:1.6;margin-top:18px;">Los precios son orientativos a fecha de {esc(rk.get("datos_de", hoy))} y '
             f'pueden variar: consulta siempre el precio actual en Amazon. Los botones de Amazon son enlaces de afiliado. {esc(FRASE_AFILIADO)}</p></div>')
    return "".join(h)


def unificar(rankings, registro, paginas):
    """Rehace con el diseño actual las páginas que ya existen (las tuyas incluidas). Copia de seguridad y restauración incluidas."""
    por_slug = {p["slug"]: p for p in paginas}
    por_titulo = {slugify((p.get("title") or {}).get("raw", "")): p for p in paginas}
    por_id = {p["id"]: p for p in paginas}
    objetivos = rankings if "todos" in UNIFICAR else [r for r in rankings if r["id"] in UNIFICAR]
    if not objetivos:
        ids = ", ".join(r["id"] for r in rankings)
        print(f"ℹ️ Ningún ranking coincide con UNIFICAR. Los ids son: {ids}")
        return 1
    print(f"{'🧪 MODO PRUEBA (no se toca nada)' if UNIFICAR_MODO != 'si' and UNIFICAR_MODO != 'restaurar' else '✏️ MODO ' + UNIFICAR_MODO.upper()}")
    sin_pagina = False
    for rk in objetivos:
        pagina = (por_id.get(rk.get("pagina_id")) or por_slug.get(rk.get("slug", "")) or por_titulo.get(slugify(rk["titulo"]))
                  or por_titulo.get(slugify(rk.get("etiqueta", ""))))
        if not pagina:
            sin_pagina = True
            print(f"⚠️ {rk['titulo']}: no encuentro su página. Añade en data/rankings.json el campo \"pagina_id\": <número de la página> "
                  f"(lo ves en la barra del navegador al editarla: post=NNN).")
            continue
        pid = pagina["id"]
        ruta = os.path.join(CARPETA_COPIAS_PAG, f"{pid}.html")
        if UNIFICAR_MODO == "restaurar":
            if not os.path.exists(ruta):
                print(f"⚠️ {rk['titulo']}: no hay copia de seguridad de la página {pid}.")
                continue
            r = requests.post(f"{WP_URL}/wp-json/wp/v2/pages/{pid}", json={"content": open(ruta, encoding="utf-8").read()},
                              auth=(WP_USER, WP_APP_PASSWORD), timeout=60)
            print(f"{'↩️ Restaurada' if r.status_code == 200 else '❌ Error ' + str(r.status_code)}: {rk['titulo']} (página {pid})")
            continue
        ids, faltan = [], []
        for m in rk.get("miembros", []):
            reg = registro.get(slugify(f"{m['marca']} {m['modelo_corto']}"))
            if isinstance(reg, dict) and reg.get("post_id"):
                ids.append(reg["post_id"])
            else:
                faltan.append(f"{m['marca']} {m['modelo_corto']}")
        info = datos_de_entradas(ids)
        filas = []
        for m in rk.get("miembros", []):
            reg = registro.get(slugify(f"{m['marca']} {m['modelo_corto']}"))
            if isinstance(reg, dict) and reg.get("post_id"):
                filas.append(fila_de_miembro(len(filas) + 1, m, reg, info.get(reg["post_id"], {})))
        if not filas:
            print(f"⚠️ {rk['titulo']}: ningún producto del ranking tiene entrada en la memoria del robot. No se toca.")
            continue
        sin_img = [f["nombre"] for f in filas if not f["imagen"]]
        generica = [f["nombre"] for f in filas if "amazon.es/s?" in f["amazon"]]
        print(f"📄 {rk['titulo']} → página {pid} ({pagina['status']}): {len(filas)} productos"
              + (f" | sin entrada (no aparecen): {', '.join(faltan)}" if faltan else "")
              + (f" | SIN IMAGEN: {', '.join(sin_img)}" if sin_img else "")
              + (f" | enlace genérico de búsqueda: {', '.join(generica)}" if generica else ""))
        if UNIFICAR_MODO != "si":
            continue
        os.makedirs(CARPETA_COPIAS_PAG, exist_ok=True)
        if not os.path.exists(ruta):
            r0 = requests.get(f"{WP_URL}/wp-json/wp/v2/pages/{pid}", params={"context": "edit", "_fields": "content"},
                              auth=(WP_USER, WP_APP_PASSWORD), timeout=30)
            if r0.status_code != 200:
                print("   ❌ No se pudo guardar la copia de seguridad: no se toca esta página.")
                continue
            open(ruta, "w", encoding="utf-8").write((r0.json().get("content") or {}).get("raw", ""))
        r = requests.post(f"{WP_URL}/wp-json/wp/v2/pages/{pid}", json={"content": construir_html(rk, filas)},
                          auth=(WP_USER, WP_APP_PASSWORD), timeout=60)
        print(f"   {'✅ Página rehecha (copia guardada en data/copias_paginas/)' if r.status_code == 200 else '❌ WordPress respondió ' + str(r.status_code)}")
    if sin_pagina:
        print("\nPáginas de tu WordPress (id · estado · título):")
        for p in paginas:
            print(f"   {p['id']} · {p['status']} · {(p.get('title') or {}).get('raw', '')}")
    if UNIFICAR_MODO == "prueba":
        print("\n🧪 PRUEBA: no se ha modificado nada. Repite con modo 'si' para aplicar.")
    return 0


def main():
    rankings = cargar_json(RUTA_RANKINGS, [])
    registro = cargar_json(RUTA_PUBLICADOS, {})
    if not rankings:
        print(f"ℹ️ No hay rankings en {RUTA_RANKINGS}. No hay nada que generar.")
        return 0
    paginas = listar_paginas()
    if paginas is None:
        print("🛑 Sin la lista de páginas no se crea nada (para no duplicar). Se reintentará en la próxima ejecución.")
        return 1
    reparar_registro(rankings, registro, guardar=(UNIFICAR_MODO == "si" or not UNIFICAR))
    if UNIFICAR:
        return unificar(rankings, registro, paginas)
    por_slug = {p["slug"]: p for p in paginas}
    por_titulo = {slugify((p.get("title") or {}).get("raw", "")): p for p in paginas}
    creadas, actualizadas, errores = 0, 0, 0

    for rk in rankings:
        rid, titulo = rk["id"], rk["titulo"]
        forzado = rid in FORZAR or "todos" in FORZAR
        if rk.get("crear_pagina", True) is False and not forzado:
            print(f"⏭️ {titulo}: página gestionada a mano (crear_pagina=false).")
            continue
        existente = por_slug.get(rk["slug"]) or por_titulo.get(slugify(titulo))
        if existente and not (forzado and existente["status"] == "draft"):
            print(f"⏭️ {titulo}: ya existe una página ({existente['status']}, ID {existente['id']}). No se toca.")
            continue

        miembros = rk.get("miembros", [])
        faltan, ids = [], []
        for m in miembros:
            reg = registro.get(slugify(f"{m['marca']} {m['modelo_corto']}"))
            if isinstance(reg, dict) and reg.get("post_id"):
                ids.append(reg["post_id"])
            else:
                faltan.append(f"{m['marca']} {m['modelo_corto']}")
        if faltan:
            print(f"⏳ {titulo}: esperando {len(faltan)} entradas todavía sin publicar ({', '.join(faltan[:4])}{'…' if len(faltan) > 4 else ''}).")
            continue

        info = datos_de_entradas(ids)
        filas, no_publicadas = [], []
        for n, m in enumerate(miembros, 1):
            reg = registro[slugify(f"{m['marca']} {m['modelo_corto']}")]
            post = info.get(reg["post_id"], {})
            if post.get("status") and post["status"] != "publish":
                no_publicadas.append(f"{m['marca']} {m['modelo_corto']}")
            filas.append(fila_de_miembro(n, m, reg, post))
        contenido = construir_html(rk, filas)
        payload = {"title": titulo, "content": contenido, "status": ESTADO_PAGINAS, "slug": rk["slug"]}
        try:
            if existente:
                r = requests.post(f"{WP_URL}/wp-json/wp/v2/pages/{existente['id']}", json={"content": contenido, "title": titulo},
                                  auth=(WP_USER, WP_APP_PASSWORD), timeout=60)
                ok, accion, pid = r.status_code == 200, "actualizado", existente["id"]
            else:
                r = requests.post(f"{WP_URL}/wp-json/wp/v2/pages", json=payload, auth=(WP_USER, WP_APP_PASSWORD), timeout=60)
                ok, accion = r.status_code == 201, "creado"
                pid = r.json().get("id") if ok else None
        except requests.RequestException as err:
            print(f"❌ {titulo}: error de conexión: {err}")
            errores += 1
            continue
        if not ok:
            print(f"❌ {titulo}: WordPress respondió {r.status_code}: {r.text[:250]}")
            errores += 1
            continue
        creadas += accion == "creado"
        actualizadas += accion == "actualizado"
        print(f"✅ Borrador {accion}: {titulo} → {WP_URL}/wp-admin/post.php?post={pid}&action=edit")
        if no_publicadas:
            print(f"   ⚠️ Estas entradas siguen sin publicar; publícalas antes de publicar la página: {', '.join(no_publicadas)}")

    print(f"\n📊 Páginas creadas: {creadas} | actualizadas: {actualizadas} | errores: {errores}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
