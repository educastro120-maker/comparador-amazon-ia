"""
RETOCAR ENTRADAS EXISTENTES (por lotes)
=======================================
Mantenimiento de entradas YA creadas en WordPress, borradores o publicadas, poco a poco:
  - "titulo": quita el título repetido (el <h2> con el nombre del producto) que estaba dentro del cuadro gris.
  - "video" : busca un vídeo de YouTube y lo inserta DEBAJO del botón de Amazon.

DE DÓNDE SALEN LAS ENTRADAS (importante)
  El programa lee TODAS las entradas de tu WordPress que parezcan fichas de producto (las que el robot creó y también
  las que hiciste a mano con el mismo formato), no solo las de data/publicados.json. Una entrada cuenta como ficha si:
  está en la memoria del robot, o su título empieza por "Análisis y Opinión", o contiene "Ficha Técnica".

CÓMO ELEGIR QUÉ RETOCAR (todo opcional; si no pones nada, procesa todas de 10 en 10)
  - IDS       : IDs de entrada de WordPress separados por comas (los ves en la barra del navegador al editar:
                ...post.php?post=1234&action=edit). Se retocan aunque ya se hubieran retocado antes.
  - RANKING   : id de un Top 10 de data/rankings.json (por ejemplo smartwatches-mejor-bateria). Selecciona las entradas
                de sus productos Y las que tengan la etiqueta de ese Top 10, aunque la etiqueta esté duplicada.
  - CATEGORIA : smartwatch o smartphone.
  - ESTADOS   : draft, publish o draft,publish.
  - LOTE      : cuántas entradas por ejecución (número, o 'todas' para no limitar). Recuerda las ya retocadas y sigue con las siguientes.

SEGURIDAD
  - MODO "prueba" (por defecto): muestra qué cambiaría en cada entrada sin tocar nada.
  - Antes de cambiar una entrada guarda una COPIA del original en data/copias/<ID>.html (y WordPress guarda sus revisiones).
    Con RETOCAR_MODO=restaurar y RESTAURAR_IDS=123,456 (o todos) se deshace.
  - Solo quita el <h2> si su texto contiene el nombre del producto y está al comienzo de la entrada.
  - Si la entrada ya tiene un vídeo de YouTube, no añade otro.
  - Si WordPress elimina el iframe del vídeo al guardar (usuario sin permisos), se detiene el añadido de vídeos.

LÍMITE: para entradas que NO están en la memoria del robot, el nombre del producto se deduce del título de la entrada
(las primeras palabras, antes de un guion, coma o palabras como "Smartwatch"). Si el nombre sale mal, el vídeo elegido
puede no ser el correcto: por eso conviene revisarlo.
"""

import os
import re
import sys
import json
import html
import unicodedata
from datetime import date
import requests

WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER", "").strip()
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "").strip()
if not (WP_URL and WP_USER and WP_APP_PASSWORD):
    sys.exit("❌ Faltan WP_URL, WP_USER o WP_APP_PASSWORD (secretos de GitHub).")

CARPETA_DATOS = os.environ.get("CARPETA_DATOS", "data")
RUTA_PUBLICADOS = os.path.join(CARPETA_DATOS, "publicados.json")
RUTA_RETOCADAS = os.path.join(CARPETA_DATOS, "retocadas.json")   # estado de las entradas que no están en publicados.json
RUTA_RANKINGS = os.path.join(CARPETA_DATOS, "rankings.json")
CARPETA_COPIAS = os.path.join(CARPETA_DATOS, "copias")
MODO = os.environ.get("RETOCAR_MODO", "prueba").strip().lower()
_lote = os.environ.get("LOTE", "10").strip().lower()
LOTE = int(_lote) if _lote.isdigit() and int(_lote) > 0 else 10**9   # "todas", "0" o vacío = sin límite
RANKING = os.environ.get("RANKING", "").strip()
CATEGORIA = os.environ.get("CATEGORIA", "").strip().lower()
ACCIONES = {a.strip().lower() for a in os.environ.get("ACCIONES", "titulo,video").split(",") if a.strip()}
ESTADOS = {e.strip().lower() for e in (os.environ.get("ESTADOS", "") or "draft,publish").split(",") if e.strip()}
IDS = [x.strip() for x in os.environ.get("IDS", "").replace(";", ",").split(",") if x.strip()]
RESTAURAR_IDS = {x.strip().lower() for x in os.environ.get("RESTAURAR_IDS", "").split(",") if x.strip()}
PRUEBA = MODO != "si"
ESTADOS_WP = "publish,draft,pending,private,future"

# Los vídeos se reutilizan del programa anadir_videos.py (misma elección y mismo bloque HTML).
av = None
if "video" in ACCIONES and MODO != "restaurar":
    os.environ["VIDEO_POSICION"] = "final"
    try:
        import anadir_videos as av   # noqa: E402
    except SystemExit:
        av = None
        print("ℹ️ Sin YOUTUBE_API_KEY: se omite la parte de vídeos.")
    except ImportError as err:
        print(f"⚠️ No se pudo cargar anadir_videos.py ({err}): se omite la parte de vídeos.")
        av = None


def slugify(texto):
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def tokens(texto):
    t = str(texto).lower().replace("+", " plus ")
    t = re.sub(r"(\d)\s*(mm|gb|tb|mah)\b", r"\1\2", t)
    return set(slugify(t).split("-")) - {""}


def cargar_json(ruta, defecto):
    if not os.path.exists(ruta):
        return defecto
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as err:
        print(f"⚠️ No se pudo leer {ruta}: {err}")
        return defecto


def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2)


# ---------- WordPress ----------
def wp_get(ruta, params, timeout=90):
    try:
        return requests.get(f"{WP_URL}/wp-json/wp/v2/{ruta}", params=params, auth=(WP_USER, WP_APP_PASSWORD), timeout=timeout)
    except requests.RequestException as err:
        print(f"   ⚠️ Error de conexión con WordPress: {err}")
        return None


def listar_entradas():
    """Todas las entradas (cualquier estado) con título, estado, categorías, etiquetas y contenido. None si falla."""
    posts, n = [], 1
    while n <= 40:
        r = wp_get("posts", {"per_page": 100, "page": n, "status": ESTADOS_WP, "context": "edit", "orderby": "id", "order": "asc",
                             "_fields": "id,title,status,categories,tags,content"})
        if r is None:
            return None
        if r.status_code == 400 and n > 1:
            break   # página fuera de rango
        if r.status_code != 200:
            print(f"❌ WordPress respondió {r.status_code} al listar las entradas: {r.text[:200]}")
            return None
        lote = r.json()
        posts += lote
        if len(lote) < 100:
            break
        n += 1
    return posts


def listar_terminos(tipo):
    """{id: nombre} de categorías o etiquetas."""
    nombres, n = {}, 1
    while n <= 30:
        r = wp_get(tipo, {"per_page": 100, "page": n, "_fields": "id,name"}, timeout=30)
        if r is None or r.status_code != 200:
            break
        lote = r.json()
        for t in lote:
            nombres[t["id"]] = html.unescape(t.get("name", ""))
        if len(lote) < 100:
            break
        n += 1
    return nombres


def leer_entrada(post_id):
    r = wp_get(f"posts/{post_id}", {"context": "edit", "_fields": "id,status,content"}, timeout=30)
    if r is None or r.status_code != 200:
        print(f"   ⚠️ No se pudo leer la entrada {post_id}.")
        return None
    return r.json()


def guardar_entrada(post_id, contenido):
    try:
        u = requests.post(f"{WP_URL}/wp-json/wp/v2/posts/{post_id}", json={"content": contenido},
                          auth=(WP_USER, WP_APP_PASSWORD), timeout=60)
    except requests.RequestException as err:
        print(f"   ❌ Error de conexión al guardar: {err}")
        return False
    if u.status_code != 200:
        print(f"   ❌ WordPress respondió {u.status_code}: {u.text[:200]}")
        return False
    return True


def ruta_copia(post_id):
    return os.path.join(CARPETA_COPIAS, f"{post_id}.html")


# ---------- Lógica ----------
def nombre_desde_titulo(titulo):
    """Deduce 'Marca Modelo' del título de la entrada: 'Análisis y Opinión: Garmin Enduro 4 - Smartwatch…' -> 'Garmin Enduro 4'."""
    t = html.unescape(str(titulo))
    t = re.sub(r"^\s*an[aá]lisis y opini[oó]n\s*:\s*", "", t, flags=re.I)
    t = re.split(r"\s[-–—|:]\s|\s*[,(]\s*", t)[0]
    t = re.split(r"\s+(?:smartwatch|reloj|smartphone|m[oó]vil|tel[eé]fono|pulsera|con|para)\b", t, flags=re.I)[0]
    return " ".join(t.split()[:6]).strip()


def quitar_titulo_duplicado(contenido, nombre):
    """Quita el primer <h2> del comienzo de la entrada cuyo texto nombra el producto. Devuelve (nuevo, quitado)."""
    buscado = tokens(nombre)
    for m in re.finditer(r"<h2\b[^>]*>(.*?)</h2>", contenido[:5000], re.S | re.I):
        texto = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        if texto.lower().startswith(("vídeo", "video")):
            continue
        if buscado and buscado <= tokens(texto):
            antes = contenido[:m.start()].rstrip(" \t")
            despues = contenido[m.end():].lstrip(" \t")
            return antes + despues, True
    return contenido, False


def restaurar(registro, retocadas):
    if "todos" in RESTAURAR_IDS:
        ids = [f[:-5] for f in os.listdir(CARPETA_COPIAS) if f.endswith(".html")] if os.path.isdir(CARPETA_COPIAS) else []
    else:
        ids = [i for i in RESTAURAR_IDS if i.isdigit()]
    if not ids:
        print("ℹ️ Indica RESTAURAR_IDS (IDs de entrada separados por comas, o 'todos').")
        return
    n = 0
    for post_id in ids:
        if not os.path.exists(ruta_copia(post_id)):
            print(f"⚠️ No hay copia de seguridad de la entrada {post_id}.")
            continue
        with open(ruta_copia(post_id), "r", encoding="utf-8") as fh:
            original = fh.read()
        print(f"↩️ Restaurando la entrada {post_id}")
        if not guardar_entrada(post_id, original):
            continue
        for est in [r for r in registro.values() if isinstance(r, dict) and str(r.get("post_id")) == post_id] + [retocadas.get(post_id, {})]:
            for k in ("retocado", "retoque_acciones", "video_id", "video_titulo", "video_canal", "video_fecha",
                      "video_estado", "video_posicion", "video_intento"):
                est.pop(k, None)
        n += 1
    guardar_json(RUTA_PUBLICADOS, registro)
    guardar_json(RUTA_RETOCADAS, retocadas)
    print(f"\n📊 Entradas restauradas: {n}")


def main():
    registro = cargar_json(RUTA_PUBLICADOS, {})
    retocadas = cargar_json(RUTA_RETOCADAS, {})
    if MODO == "restaurar":
        return restaurar(registro, retocadas)

    # Filtro por Top 10: productos del ranking y/o entradas con su etiqueta
    miembros, etiqueta_rk = None, ""
    if RANKING and RANKING.lower() != "todos":
        rk = next((x for x in cargar_json(RUTA_RANKINGS, []) if x.get("id") == RANKING), None)
        if not rk:
            ids_rk = ", ".join(x.get("id", "") for x in cargar_json(RUTA_RANKINGS, []))
            sys.exit(f"❌ '{RANKING}' no es un id de Top 10. Los ids son los de data/rankings.json: {ids_rk}. "
                     f"Para elegir entradas concretas usa el campo de IDs de entrada.")
        miembros = {slugify(f"{m['marca']} {m['modelo_corto']}") for m in rk.get("miembros", [])}
        etiqueta_rk = html.unescape(rk.get("etiqueta", "")).strip().lower()

    posts = listar_entradas()
    if posts is None:
        sys.exit("❌ No se pudieron leer las entradas de WordPress. No se hace nada.")
    nombres_cat, nombres_tag = listar_terminos("categories"), listar_terminos("tags")
    por_post = {r["post_id"]: (pid, r) for pid, r in registro.items() if isinstance(r, dict) and r.get("post_id")}
    ids_explicitos = {int(x) for x in IDS if x.isdigit()}

    candidatos, no_producto, ya_retocadas, fuera_estado = [], 0, 0, 0
    for p in posts:
        pid_wp = p["id"]
        if ids_explicitos and pid_wp not in ids_explicitos:
            continue
        titulo = html.unescape(((p.get("title") or {}).get("raw") or "")).strip()
        contenido = (p.get("content") or {}).get("raw", "")
        reg = por_post.get(pid_wp)
        es_ficha = bool(reg) or titulo.lower().startswith("análisis y opinión") or "Ficha Técnica" in contenido
        if not es_ficha:
            no_producto += 1
            continue
        if p.get("status") not in ESTADOS:
            fuera_estado += 1
            continue
        est = reg[1] if reg else retocadas.setdefault(str(pid_wp), {})
        if est.get("retocado") and not ids_explicitos:
            ya_retocadas += 1
            continue
        cats = [nombres_cat.get(c, "").lower() for c in p.get("categories", [])]
        tags = [nombres_tag.get(t, "").strip().lower() for t in p.get("tags", [])]
        if CATEGORIA and not (any(CATEGORIA in c for c in cats) or (reg and str(reg[1].get("categoria", "")).lower() == CATEGORIA)):
            continue
        if miembros is not None and not ((reg and reg[0] in miembros) or (etiqueta_rk and etiqueta_rk in tags)):
            continue
        nombre = f"{reg[1].get('marca', '')} {reg[1].get('modelo', '')}".strip() if reg else nombre_desde_titulo(titulo)
        candidatos.append({"id": pid_wp, "status": p.get("status"), "contenido": contenido, "est": est, "nombre": nombre,
                           "marca": reg[1].get("marca", "") if reg else "", "modelo": reg[1].get("modelo", "") if reg else nombre,
                           "en_registro": bool(reg)})
    if ids_explicitos:
        candidatos.sort(key=lambda c: c["id"])

    print(f"{'🧪 MODO PRUEBA (no se toca nada)' if PRUEBA else '✏️ MODO REAL'} | acciones: {', '.join(sorted(ACCIONES))} | "
          f"estados: {', '.join(sorted(ESTADOS))} | lote: {'todas' if LOTE >= 10**9 else LOTE}")
    print(f"📚 Entradas en WordPress: {len(posts)} | no parecen fichas de producto: {no_producto} | fuera de los estados elegidos: {fuera_estado} "
          f"| ya retocadas: {ya_retocadas} | POR RETOCAR con tus filtros: {len(candidatos)}")
    if IDS:
        no_enc = [i for i in IDS if not i.isdigit() or int(i) not in {p['id'] for p in posts}]
        if no_enc:
            print(f"⚠️ IDs sin entrada en WordPress (¿son IDs de entrada? no confundir con el id de un Top 10): {', '.join(no_enc)}")
    print()
    if not candidatos:
        print("ℹ️ No hay entradas que retocar con estos filtros.")
        return

    procesadas, modificadas, sin_cambios = 0, 0, 0
    hoy = date.today().isoformat()
    video_activo = av is not None

    def guardar_estado():
        if not PRUEBA:
            guardar_json(RUTA_PUBLICADOS, registro)
            guardar_json(RUTA_RETOCADAS, {k: v for k, v in retocadas.items() if v})

    try:
        for c in candidatos:
            if procesadas >= LOTE:
                break
            procesadas += 1
            est, original, nombre = c["est"], c["contenido"], c["nombre"]
            nuevo, cambios = original, []
            print(f"📄 {nombre or '(sin nombre)'} (entrada {c['id']}, {c['status']})")

            if "titulo" in ACCIONES:
                nuevo, quitado = quitar_titulo_duplicado(nuevo, nombre)
                if quitado:
                    cambios.append("título duplicado quitado")

            video, reintentar = None, False   # si YouTube falla, la entrada no se da por terminada
            if video_activo and nombre and not est.get("video_id") and est.get("video_estado") != "manual":
                if re.search(r"youtube(-nocookie)?\.com/embed|youtu\.be/|tc-video", nuevo):
                    print("   ⏭️ Ya tiene un vídeo de YouTube: no se añade otro.")
                    est["video_estado"] = "manual"
                else:
                    error_temporal = False
                    try:
                        video = av.elegir_video(c["marca"], c["modelo"])
                    except av.ErrorTemporal:
                        error_temporal = reintentar = True
                        print("   ⚠️ Error temporal con YouTube: el vídeo se intentará en otra ejecución.")
                    if video:
                        nuevo = nuevo.rstrip() + "\n" + av.bloque_video(video, c["marca"], c["modelo"])
                        cambios.append(f"vídeo «{video['titulo'][:60]}» de {video['canal']}")
                    elif not error_temporal:
                        print("   ⚠️ Sin vídeo adecuado.")
                        if not PRUEBA:
                            est["video_estado"], est["video_intento"] = "sin_resultado", hoy

            if not cambios:
                print("   — Sin cambios necesarios.")
                sin_cambios += 1
                if not PRUEBA and not reintentar:
                    est["retocado"], est["retoque_acciones"] = hoy, []
                    guardar_estado()
                continue

            print("   ✅ " + " + ".join(cambios))
            if PRUEBA:
                modificadas += 1
                continue

            os.makedirs(CARPETA_COPIAS, exist_ok=True)
            if not os.path.exists(ruta_copia(c["id"])):
                with open(ruta_copia(c["id"]), "w", encoding="utf-8") as fh:
                    fh.write(original)
            if not guardar_entrada(c["id"], nuevo):
                continue
            if video:
                comprobar = leer_entrada(c["id"])
                if not comprobar or video["id"] not in (comprobar.get("content") or {}).get("raw", ""):
                    print("   ❌ WordPress eliminó el vídeo al guardar (hace falta un usuario Administrador). No se añaden más vídeos.")
                    video_activo = False
                else:
                    est.update({"video_id": video["id"], "video_titulo": video["titulo"], "video_canal": video["canal"],
                                "video_fecha": hoy, "video_estado": "auto", "video_posicion": "final"})
            if not reintentar:
                est["retocado"], est["retoque_acciones"] = hoy, [x.split(" ")[0] for x in cambios]
            modificadas += 1
            guardar_estado()
    except Exception as err:   # cuota de YouTube u otro corte: se guarda lo hecho
        if av is not None and isinstance(err, av.SinCuota):
            print(f"\n🛑 Se detiene: {err}.")
        else:
            raise
    finally:
        guardar_estado()

    quedan = len(candidatos) - procesadas
    print(f"\n📊 Entradas revisadas: {procesadas} | con cambios{' (previstos)' if PRUEBA else ''}: {modificadas} | sin cambios: {sin_cambios} "
          f"| quedan por retocar: {max(quedan, 0)}")
    if PRUEBA:
        print("🧪 ESTÁS EN MODO PRUEBA: no se ha modificado nada. Repite con modo 'si' para aplicar este lote.")


if __name__ == "__main__":
    main()
