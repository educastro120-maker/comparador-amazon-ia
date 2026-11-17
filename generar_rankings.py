"""
GENERAR RANKINGS (páginas Top 10 en borrador)
=============================================
Crea en WordPress, como BORRADOR, una PÁGINA por cada ranking definido en data/rankings.json:
  - Resumen rápido (tabla) + ficha corta de cada producto, con su botón de Amazon y el enlace a su entrada.
  - Sección "Cómo hemos elegido", fecha de los datos y avisos de afiliado y de precios.

NO usa ninguna IA ni gasta cuota: monta la página con los datos que ya tiene.

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
FORZAR = {x.strip() for x in os.environ.get("FORZAR_RANKINGS", "").split(",") if x.strip()}
PREFIJOS_LINK_CORTO = ("https://link.amazon/", "https://amzn.to/", "https://amzn.eu/")
NOTA_METODOLOGIA = os.environ.get(
    "NOTA_METODOLOGIA",
    "Las cifras proceden de las fichas de los fabricantes y de pruebas publicadas por medios especializados; "
    "no hemos probado personalmente estos productos. Si detectas un dato incorrecto, avísanos.")


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
    """Enlace actual y estado de cada entrada (el enlace de un borrador cambia al publicarse)."""
    info = {}
    ids = sorted(set(ids))
    for i in range(0, len(ids), 50):
        trozo = ids[i:i + 50]
        try:
            r = requests.get(f"{WP_URL}/wp-json/wp/v2/posts",
                             params={"include": ",".join(map(str, trozo)), "per_page": 100,
                                     "status": "publish,draft,pending,private,future", "_fields": "id,link,status"},
                             auth=(WP_USER, WP_APP_PASSWORD), timeout=30)
            if r.status_code == 200:
                for p in r.json():
                    info[p["id"]] = {"link": p.get("link", ""), "status": p.get("status", "")}
        except (requests.RequestException, ValueError) as err:
            print(f"   ⚠️ No se pudo comprobar el estado de algunas entradas: {err}")
    return info


def construir_html(rk, filas):
    hoy = datetime.now().strftime("%d/%m/%Y")
    caja = "border:1px solid #e2e8f0;border-radius:12px;padding:18px;margin:0 0 18px 0;background:#fff;"
    boton = ("background-color:#ffa41c;color:#111;text-decoration:none;font-weight:bold;padding:10px 18px;border-radius:8px;"
             "border:1px solid #ff8f00;display:inline-block;")
    h = ['<div style="max-width:900px;margin:0 auto;font-family:system-ui,-apple-system,sans-serif;color:#1e293b;">']
    if rk.get("lema"):
        h.append(f'<p style="font-size:1.2em;font-weight:bold;color:#b45309;margin:0 0 10px;">{esc(rk["lema"])}</p>')
    h.append(f'<p style="font-size:1.05em;line-height:1.7;">{esc(rk.get("intro", ""))}</p>')

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

    # Cómo hemos elegido
    h.append('<h2 style="margin-top:28px;">Cómo hemos elegido</h2>')
    h.append(f'<p style="line-height:1.7;">{esc(rk.get("criterio", ""))}</p>')
    h.append(f'<p style="line-height:1.7;color:#475569;">{esc(NOTA_METODOLOGIA)}</p>')
    h.append(f'<p style="color:#64748b;font-size:.9em;">Datos recopilados: {esc(rk.get("datos_de", ""))}. Página generada el {hoy}.</p>')

    # Fichas
    h.append('<h2 style="margin-top:28px;">Análisis de cada producto</h2>')
    for f in filas:
        img = ""
        if f.get("imagen"):
            img = (f'<div style="text-align:center;margin-bottom:12px;"><img src="{esc(f["imagen"])}" alt="{esc(f["nombre"])}" '
                   f'loading="lazy" referrerpolicy="no-referrer" style="max-height:200px;max-width:100%;object-fit:contain;"></div>')
        rot = (f'<span style="background:#ff9900;color:#fff;font-weight:bold;padding:3px 10px;border-radius:12px;font-size:.8em;'
               f'margin-left:8px;">{esc(f["rotulo"])}</span>') if f.get("rotulo") else ""
        resumen = f'<p style="line-height:1.6;">{esc(f["resumen"])}</p>' if f.get("resumen") else ""
        analisis = (f'<a href="{esc(f["analisis"])}" style="margin-left:14px;">Leer el análisis completo →</a>') if f.get("analisis") else ""
        h.append(f'<div id="puesto-{f["n"]}" style="{caja}">{img}'
                 f'<h3 style="margin:0 0 6px;">{f["n"]}. {esc(f["nombre"])}{rot}</h3>'
                 f'<p style="margin:0 0 8px;font-weight:600;color:#334155;">{esc(f.get("motivo", ""))}</p>{resumen}'
                 f'<p style="margin:10px 0;"><span style="color:#64748b;font-size:.85em;">Precio orientativo:</span> '
                 f'<strong style="color:#b12704;">{esc(f["precio"])}</strong></p>'
                 f'<a href="{esc(f["amazon"])}" target="_blank" rel="sponsored nofollow noopener" style="{boton}">Ver precio en Amazon 🛒</a>{analisis}</div>')

    h.append(f'<p style="font-size:.85em;color:#64748b;line-height:1.6;">Los precios son orientativos a fecha de {esc(rk.get("datos_de", hoy))} y '
             'pueden variar: consulta siempre el precio actual en Amazon. Los botones de Amazon son enlaces de afiliado: como afiliado de Amazon '
             'obtengo ingresos por las compras adscritas, sin coste extra para ti.</p></div>')
    return "".join(h)


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
            filas.append({"n": n, "nombre": f"{m['marca']} {m['modelo_corto']}", "rotulo": m.get("rotulo", ""),
                          "motivo": m.get("motivo", ""), "precio": precio_es(m.get("precio")), "amazon": enlace_amazon(m, reg),
                          "imagen": reg.get("imagen", "") or m.get("imagen", ""), "resumen": recortar_frase(reg.get("resumen", "")),
                          "analisis": post.get("link") or reg.get("url_post", "")})
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
