"""
RETOCAR ENTRADAS EXISTENTES (por lotes)
=======================================
Mantenimiento de entradas YA creadas, borradores o publicadas, poco a poco:
  - "titulo": quita el título repetido (el <h2> con el nombre del producto) que estaba dentro del cuadro gris.
  - "video" : busca un vídeo de YouTube y lo inserta DEBAJO del botón de Amazon.

Cómo trabaja:
  - Procesa un LOTE de entradas por ejecución (10 por defecto), y se acuerda de las que ya retocó,
    así que ejecutarlo varias veces recorre todas sin repetir.
  - Se puede limitar a los productos de un Top 10 (RANKING = id del ranking en data/rankings.json) y/o a una categoría.
  - Antes de cambiar una entrada guarda una COPIA del contenido original en data/copias/<ID>.html
    (WordPress también guarda sus propias revisiones). Con RETOCAR_MODO=restaurar se puede deshacer.
  - MODO "prueba": muestra qué cambiaría en cada entrada sin tocar nada (y sin marcarlas como hechas).

Seguridad:
  - Solo quita el <h2> si su texto contiene la marca y el modelo del producto y está al comienzo de la entrada
    (no toca títulos de sección escritos por ti).
  - Si la entrada ya tiene un vídeo de YouTube (tuyo o del robot), no añade otro.
  - Si WordPress elimina el iframe del vídeo al guardar (usuario sin permisos), se detiene el añadido de vídeos.

VARIABLES: RETOCAR_MODO (prueba|si|restaurar), LOTE, RANKING, CATEGORIA, ACCIONES ("titulo,video"),
           ESTADOS ("draft,publish"), RESTAURAR_IDS ("123,456" o "todos"), YOUTUBE_API_KEY (para vídeos).
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
RUTA_RANKINGS = os.path.join(CARPETA_DATOS, "rankings.json")
CARPETA_COPIAS = os.path.join(CARPETA_DATOS, "copias")
MODO = os.environ.get("RETOCAR_MODO", "prueba").strip().lower()
LOTE = int(os.environ.get("LOTE", "10") or 10)
RANKING = os.environ.get("RANKING", "").strip()
CATEGORIA = os.environ.get("CATEGORIA", "").strip().lower()
ACCIONES = {a.strip().lower() for a in os.environ.get("ACCIONES", "titulo,video").split(",") if a.strip()}
ESTADOS = {e.strip().lower() for e in os.environ.get("ESTADOS", "draft,publish").split(",") if e.strip()}
RESTAURAR_IDS = {x.strip().lower() for x in os.environ.get("RESTAURAR_IDS", "").split(",") if x.strip()}
PRUEBA = MODO != "si"

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


def leer_entrada(post_id):
    try:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/posts/{post_id}", params={"context": "edit", "_fields": "id,status,content"},
                         auth=(WP_USER, WP_APP_PASSWORD), timeout=30)
    except requests.RequestException as err:
        print(f"   ⚠️ No se pudo leer la entrada {post_id}: {err}")
        return None
    if r.status_code != 200:
        print(f"   ⚠️ No se pudo leer la entrada {post_id} ({r.status_code}).")
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


def quitar_titulo_duplicado(contenido, marca, modelo):
    """Quita el primer <h2> del comienzo de la entrada cuyo texto nombra el producto. Devuelve (nuevo, quitado)."""
    buscado = tokens(f"{marca} {modelo}")
    for m in re.finditer(r"<h2\b[^>]*>(.*?)</h2>", contenido[:5000], re.S | re.I):
        texto = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        if texto.lower().startswith(("vídeo", "video")):
            continue
        if buscado and buscado <= tokens(texto):
            antes = contenido[:m.start()].rstrip(" \t")
            despues = contenido[m.end():].lstrip(" \t")
            return antes + despues, True
    return contenido, False


def restaurar(registro):
    pendientes = {str(r.get("post_id")): (pid, r) for pid, r in registro.items() if isinstance(r, dict) and r.get("post_id")}
    objetivos = list(pendientes) if "todos" in RESTAURAR_IDS else [i for i in RESTAURAR_IDS if i in pendientes]
    if not objetivos:
        print("ℹ️ Indica RESTAURAR_IDS (IDs de entrada separados por comas, o 'todos').")
        return
    n = 0
    for post_id in objetivos:
        ruta = ruta_copia(post_id)
        if not os.path.exists(ruta):
            continue
        pid, r = pendientes[post_id]
        with open(ruta, "r", encoding="utf-8") as fh:
            original = fh.read()
        print(f"↩️ Restaurando la entrada {post_id} ({r.get('marca', '')} {r.get('modelo', '')})")
        if guardar_entrada(post_id, original):
            for k in ("retocado", "retoque_acciones", "video_id", "video_titulo", "video_canal", "video_fecha", "video_estado", "video_posicion"):
                r.pop(k, None)
            n += 1
    guardar_json(RUTA_PUBLICADOS, registro)
    print(f"\n📊 Entradas restauradas: {n}")


def main():
    registro = cargar_json(RUTA_PUBLICADOS, {})
    if MODO == "restaurar":
        return restaurar(registro)

    rankings = cargar_json(RUTA_RANKINGS, [])
    miembros = None
    if RANKING and RANKING.lower() != "todos":
        rk = next((x for x in rankings if x.get("id") == RANKING), None)
        if not rk:
            sys.exit(f"❌ No existe el ranking '{RANKING}' en data/rankings.json. Ids disponibles: {', '.join(x.get('id', '') for x in rankings)}")
        miembros = {slugify(f"{m['marca']} {m['modelo_corto']}") for m in rk.get("miembros", [])}

    candidatos = []
    for pid, r in registro.items():
        if not (isinstance(r, dict) and r.get("post_id") and r.get("marca")):
            continue
        if r.get("retocado"):
            continue
        if miembros is not None and pid not in miembros:
            continue
        if CATEGORIA and str(r.get("categoria", "")).lower() != CATEGORIA:
            continue
        candidatos.append((pid, r))

    print(f"{'🧪 MODO PRUEBA (no se toca nada)' if PRUEBA else '✏️ MODO REAL'} | acciones: {', '.join(sorted(ACCIONES))} | "
          f"estados: {', '.join(sorted(ESTADOS))} | lote: {LOTE} | ranking: {RANKING or 'todos'} | pendientes de retocar: {len(candidatos)}\n")

    procesadas, modificadas, sin_cambios, omitidas = 0, 0, 0, 0
    hoy = date.today().isoformat()
    video_activo = av is not None
    try:
        for pid, r in candidatos:
            if procesadas >= LOTE:
                break
            post = leer_entrada(r["post_id"])
            if not post:
                continue
            if post.get("status") not in ESTADOS:
                omitidas += 1
                continue
            procesadas += 1
            original = (post.get("content") or {}).get("raw", "")
            nuevo, cambios = original, []
            print(f"📄 {r['marca']} {r['modelo']} (entrada {r['post_id']}, {post.get('status')})")

            if "titulo" in ACCIONES:
                nuevo, quitado = quitar_titulo_duplicado(nuevo, r["marca"], r["modelo"])
                if quitado:
                    cambios.append("título duplicado quitado")

            video = None
            reintentar = False   # si YouTube falló, la entrada no se da por terminada y se reintenta en otro lote
            if video_activo and not r.get("video_id") and r.get("video_estado") != "manual":
                if re.search(r"youtube(-nocookie)?\.com/embed|youtu\.be/|tc-video", nuevo):
                    print("   ⏭️ Ya tiene un vídeo de YouTube: no se añade otro.")
                    r["video_estado"] = "manual"
                else:
                    error_temporal = False
                    try:
                        video = av.elegir_video(r["marca"], r["modelo"])
                    except av.ErrorTemporal:
                        error_temporal = reintentar = True
                        print("   ⚠️ Error temporal con YouTube: el vídeo se intentará en otra ejecución.")
                    if video:
                        nuevo = nuevo.rstrip() + "\n" + av.bloque_video(video, r["marca"], r["modelo"])
                        cambios.append(f"vídeo «{video['titulo'][:60]}» de {video['canal']}")
                    elif not error_temporal:
                        print("   ⚠️ Sin vídeo adecuado.")
                        if not PRUEBA:
                            r["video_estado"], r["video_intento"] = "sin_resultado", hoy

            if not cambios:
                print("   — Sin cambios necesarios.")
                sin_cambios += 1
                if not PRUEBA and not reintentar:
                    r["retocado"], r["retoque_acciones"] = hoy, []
                    guardar_json(RUTA_PUBLICADOS, registro)
                continue

            print("   ✅ " + " + ".join(cambios))
            if PRUEBA:
                modificadas += 1
                continue

            os.makedirs(CARPETA_COPIAS, exist_ok=True)
            if not os.path.exists(ruta_copia(r["post_id"])):
                with open(ruta_copia(r["post_id"]), "w", encoding="utf-8") as fh:
                    fh.write(original)
            if not guardar_entrada(r["post_id"], nuevo):
                continue
            if video:
                comprobar = leer_entrada(r["post_id"])
                if not comprobar or video["id"] not in (comprobar.get("content") or {}).get("raw", ""):
                    print("   ❌ WordPress eliminó el vídeo al guardar (hace falta un usuario Administrador). No se añaden más vídeos.")
                    video_activo = False
                else:
                    r.update({"video_id": video["id"], "video_titulo": video["titulo"], "video_canal": video["canal"],
                              "video_fecha": hoy, "video_estado": "auto", "video_posicion": "final"})
            if not reintentar:
                r["retocado"], r["retoque_acciones"] = hoy, [c.split(" ")[0] for c in cambios]
            modificadas += 1
            guardar_json(RUTA_PUBLICADOS, registro)
    except Exception as err:   # cuota de YouTube u otro corte: se guarda lo hecho
        if av is not None and isinstance(err, av.SinCuota):
            print(f"\n🛑 Se detiene: {err}.")
        else:
            raise
    finally:
        if not PRUEBA:
            guardar_json(RUTA_PUBLICADOS, registro)

    quedan = len(candidatos) - procesadas - omitidas if not PRUEBA else len(candidatos)
    print(f"\n📊 Entradas revisadas: {procesadas} | con cambios{' (previstos)' if PRUEBA else ''}: {modificadas} | sin cambios: {sin_cambios} "
          f"| omitidas por estado: {omitidas} | quedan por retocar: {max(quedan, 0)}")
    if PRUEBA:
        print("🧪 Prueba terminada: no se ha modificado nada. Repite con modo 'si' para aplicar este lote.")


if __name__ == "__main__":
    main()
