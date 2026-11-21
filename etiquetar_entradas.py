"""
ETIQUETAR ENTRADAS YA CREADAS (con tu lista de etiquetas)
=========================================================
Pone categoría-etiquetas a las entradas que NO tienen ninguna de tus etiquetas (por ejemplo las que salen "Sin etiquetas").
Usa data/etiquetas.json: precio -> por reglas; criterio -> la IA elige solo entre tus etiquetas.
Nunca quita etiquetas que ya tengan y nunca crea etiquetas nuevas.
  ETIQUETAR_MODO = prueba (por defecto, no toca nada) | si
  LOTE           = número o "todas" (cada llamada a la IA usa cuota gratuita: con muchas entradas, tanda a tanda)
  IDS            = IDs de entrada separados por comas (opcional)
"""
import os, re, sys, html, json
import requests

import auto_publisher as ap   # reutiliza la IA con respaldo y la lectura de etiquetas
import etiquetado

MODO = os.environ.get("ETIQUETAR_MODO", "prueba").strip().lower()
PRUEBA = MODO != "si"
_l = os.environ.get("LOTE", "todas").strip().lower()
LOTE = int(_l) if _l.isdigit() and int(_l) > 0 else 10**9
IDS = {int(x) for x in os.environ.get("IDS", "").replace(";", ",").split(",") if x.strip().isdigit()}
WP, AUTH = ap.WP_URL, (ap.WP_USER, ap.WP_APP_PASSWORD)


def get(ruta, params):
    return requests.get(f"{WP}/wp-json/wp/v2/{ruta}", params=params, auth=AUTH, timeout=60)


def todos(ruta, campos, extra=None):
    out, n = [], 1
    while n <= 40:
        r = get(ruta, {"per_page": 100, "page": n, "_fields": campos, **(extra or {})})
        if r.status_code == 400 and n > 1:
            break
        if r.status_code != 200:
            return None
        out += r.json()
        if len(r.json()) < 100:
            break
        n += 1
    return out


def texto_limpio(contenido):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", contenido, flags=re.S | re.I)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", t)).split())


def main():
    lista = etiquetado.cargar()
    if not lista:
        sys.exit("❌ No hay data/etiquetas.json. Créalo (hay una plantilla) y vuelve a lanzar.")
    nombres_lista = {e["nombre"].strip().lower() for e in lista}
    tags = todos("tags", "id,name")
    cats = todos("categories", "id,name")
    posts = todos("posts", "id,title,status,categories,tags,content", {"status": "publish,draft,pending,private,future", "context": "edit"})
    if tags is None or cats is None or posts is None:
        sys.exit("❌ No se pudo leer WordPress. No se hace nada.")
    id_tag = {html.unescape(t["name"]).strip().lower(): t["id"] for t in tags}
    mios = {id_tag[n] for n in nombres_lista if n in id_tag}
    for e in lista:
        if e["nombre"].strip().lower() not in id_tag:
            print(f"⚠️ La etiqueta «{e['nombre']}» no existe en WordPress: créala con ese nombre exacto para que se pueda usar.")
    nombre_cat = {c["id"]: html.unescape(c["name"]).lower() for c in cats}

    pendientes = []
    for p in posts:
        if IDS and p["id"] not in IDS:
            continue
        cat = next((c for c in ("smartwatch", "smartphone") if any(c in nombre_cat.get(i, "") for i in p["categories"])), None)
        if not cat or (set(p["tags"]) & mios and not IDS):
            continue
        pendientes.append((p, cat))
    print(f"{'🧪 MODO PRUEBA' if PRUEBA else '✏️ MODO REAL'} | entradas sin ninguna de tus etiquetas: {len(pendientes)}\n")

    hechas = 0
    for p, cat in pendientes:
        if hechas >= LOTE or (not PRUEBA and ap.ia_agotada()):
            break
        contenido = (p.get("content") or {}).get("raw", "")
        titulo = html.unescape((p.get("title") or {}).get("raw", ""))
        m = re.search(r"Precio orientativo:\s*(?:<[^>]+>\s*)*([^<|]+)", contenido)
        precio = m.group(1) if m else ""
        nombres = etiquetado.nombres_para(cat, precio, f"{titulo}. {texto_limpio(contenido)}", ap.llamar_gemini_con_respaldo)
        ids = [id_tag[n.strip().lower()] for n in nombres if n.strip().lower() in id_tag]
        print(f"📄 {titulo[:70]} (entrada {p['id']}) → {', '.join(nombres) or '(ninguna)'}")
        hechas += 1
        if PRUEBA or not ids:
            continue
        r = requests.post(f"{WP}/wp-json/wp/v2/posts/{p['id']}", json={"tags": sorted(set(p["tags"]) | set(ids))}, auth=AUTH, timeout=60)
        if r.status_code != 200:
            print(f"   ❌ WordPress respondió {r.status_code}")
    print(f"\n📊 Entradas revisadas: {hechas} de {len(pendientes)}" + ("  (PRUEBA: repite con modo 'si')" if PRUEBA else ""))


if __name__ == "__main__":
    main()
