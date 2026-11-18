"""
AÑADIR VÍDEOS DE YOUTUBE
========================
Busca en YouTube (API oficial, gratuita) un vídeo de análisis o comparativa de cada producto y lo INSERTA en su
entrada de WordPress con el reproductor oficial (versión youtube-nocookie.com), con crédito al canal.

Reglas de seguridad:
  - Solo toca entradas en BORRADOR (VIDEOS_SOLO_BORRADORES=si, por defecto): tú revisas el vídeo antes de publicar.
  - Si la entrada ya tiene un vídeo de YouTube (puesto por ti o por el robot), NO se toca.
  - Si borras o cambias el vídeo a mano, el robot NO lo vuelve a poner (queda anotado en data/publicados.json).
  - Solo elige vídeos públicos y que se pueden incrustar, de 3 a 30 minutos, con el nombre del modelo en el título.
  - No descarga ni copia nada: solo incrusta el reproductor oficial de YouTube.

MODO (variable VIDEOS_MODO): "prueba" muestra qué vídeo elegiría sin tocar nada; "si" lo inserta.

LÍMITES:
  - Elegir "el mejor vídeo" es una estimación (coincidencia del título, visualizaciones, antigüedad, palabras como
    "análisis" o "review"). Puede equivocarse: por eso va en borrador y se revisa.
  - Necesita que el usuario de WordPress sea Administrador (con otros roles WordPress puede eliminar el iframe).
  - Cuota gratuita de YouTube: en torno a 100 búsquedas al día. Por defecto se hacen 10 por ejecución.
"""

import os
import re
import sys
import json
import math
import html
import unicodedata
from datetime import date, datetime, timezone
import requests

WP_URL = os.environ.get("WP_URL", "").rstrip("/")
WP_USER = os.environ.get("WP_USER", "").strip()
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "").strip()
YT_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
if not YT_KEY:
    print("ℹ️ No hay YOUTUBE_API_KEY (secreto de GitHub): se omite la inserción de vídeos.")
    sys.exit(0)
if not (WP_URL and WP_USER and WP_APP_PASSWORD):
    sys.exit("❌ Faltan WP_URL, WP_USER o WP_APP_PASSWORD (secretos de GitHub).")

YT_BASE = os.environ.get("YOUTUBE_API_BASE", "https://www.googleapis.com/youtube/v3")
CARPETA_DATOS = os.environ.get("CARPETA_DATOS", "data")
RUTA_PUBLICADOS = os.path.join(CARPETA_DATOS, "publicados.json")
MODO_PRUEBA = os.environ.get("VIDEOS_MODO", "si").strip().lower() == "prueba"
SOLO_BORRADORES = os.environ.get("VIDEOS_SOLO_BORRADORES", "si").strip().lower() != "no"
MAX_POR_EJECUCION = int(os.environ.get("YOUTUBE_MAX_POR_EJECUCION", "10"))
MIN_VISUALIZACIONES = int(os.environ.get("VIDEO_MIN_VISUALIZACIONES", "1000"))
MIN_MINUTOS, MAX_MINUTOS = 3, 30
REINTENTO_DIAS = 30
PALABRAS_VARIANTE = {"pro", "plus", "ultra", "max", "lite", "classic", "fe", "mini", "se", "air", "neo", "turbo", "edge", "fold", "flip", "gt", "active"}
PALABRAS_BUENAS = ("análisis", "analisis", "review", "reseña", "opinión", "opinion", "a fondo", "prueba", "test", "comparativa", " vs ")
PALABRAS_MALAS = ("#shorts", "shorts", "unboxing", "reacción", "reaccion", "rumor", "filtración", "filtracion", "leak")


class SinCuota(Exception):
    pass


class ErrorTemporal(Exception):
    """Fallo de red o de YouTube: no se anota como 'sin vídeo' para reintentarlo en la próxima ejecución."""


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


def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2)


def _tokens(texto):
    t = str(texto).lower().replace("+", " plus ")
    t = re.sub(r"(\d)\s*(mm|gb|tb|mah)\b", r"\1\2", t)
    return set(slugify(t).split("-")) - {""}


IGNORABLES = {"lte", "5g", "4g", "wifi", "bluetooth", "esim", "gps", "nfc"}


def _esencial(tokens):
    """Quita lo que casi nunca aparece en el título de un vídeo (LTE, 5G, tamaños como 47mm, 256gb...)."""
    ess = {t for t in tokens if t not in IGNORABLES and not re.fullmatch(r"\d+(mm|gb|tb|mah)", t)}
    return ess or tokens


def titulo_coincide(marca, modelo, titulo_video):
    t = _tokens(titulo_video)
    # el nombre del modelo puede aparecer sin la marca en el título (por ejemplo "Galaxy A57 review")
    for conjunto in (_esencial(_tokens(f"{marca} {modelo}")), _esencial(_tokens(modelo))):
        if conjunto and conjunto <= t and not ((t - conjunto) & PALABRAS_VARIANTE):
            return True
    return False


def modelo_para_buscar(modelo):
    """Texto de búsqueda sin sufijos que no suelen aparecer en los vídeos."""
    m = re.sub(r"\b\d+\s?(mm|gb|tb)\b", "", modelo, flags=re.I)
    m = re.sub(r"\b(LTE|5G|4G|WiFi|eSIM)\b", "", m, flags=re.I)
    return re.sub(r"\s+", " ", m).strip() or modelo


def minutos_iso(duracion):
    m = re.fullmatch(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duracion or "")
    if not m:
        return 0
    h, mi, s = (int(x or 0) for x in m.groups())
    return h * 60 + mi + s / 60


def yt_get(ruta, params):
    try:
        r = requests.get(f"{YT_BASE}/{ruta}", params={**params, "key": YT_KEY}, timeout=30)
    except requests.RequestException as err:
        print(f"   ⚠️ Error de conexión con YouTube: {err}")
        return None
    if r.status_code in (400, 403):
        try:
            motivo = r.json()["error"]["errors"][0]["reason"]
        except Exception:
            motivo = r.text[:150]
        if motivo in ("quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded"):
            raise SinCuota("cuota diaria de YouTube agotada")
        raise SinCuota(f"YouTube rechazó la petición ({r.status_code}: {motivo}). Revisa la clave y que la API 'YouTube Data API v3' esté activada")
    if r.status_code != 200:
        print(f"   ⚠️ YouTube respondió {r.status_code}: {r.text[:150]}")
        return None
    return r.json()


def elegir_video(marca, modelo):
    """Devuelve el mejor vídeo candidato (dict) o None."""
    q = f"{marca} {modelo_para_buscar(modelo)} análisis review en español"
    res = yt_get("search", {"part": "snippet", "type": "video", "q": q, "maxResults": 10, "relevanceLanguage": "es",
                            "regionCode": "ES", "videoEmbeddable": "true", "safeSearch": "moderate", "order": "relevance"})
    if res is None:
        raise ErrorTemporal()
    ids = [i["id"]["videoId"] for i in res.get("items", []) if i.get("id", {}).get("videoId")]
    if not ids:
        return None
    det = yt_get("videos", {"part": "snippet,contentDetails,statistics,status", "id": ",".join(ids)})
    if det is None:
        raise ErrorTemporal()
    mejores = []
    ahora = datetime.now(timezone.utc)
    for v in det.get("items", []):
        sn, st, cd, ss = v.get("snippet", {}), v.get("statistics", {}), v.get("contentDetails", {}), v.get("status", {})
        titulo = sn.get("title", "")
        if not ss.get("embeddable") or ss.get("privacyStatus") != "public":
            continue
        if sn.get("liveBroadcastContent", "none") != "none":
            continue
        minutos = minutos_iso(cd.get("duration", ""))
        if not (MIN_MINUTOS <= minutos <= MAX_MINUTOS):
            continue
        if not titulo_coincide(marca, modelo, titulo):
            continue
        tl = titulo.lower()
        if any(p in tl for p in PALABRAS_MALAS):
            continue
        vistas = int(st.get("viewCount", 0) or 0)
        if vistas < MIN_VISUALIZACIONES:
            continue
        puntos = math.log10(vistas + 1)
        if any(p in f" {tl} " for p in PALABRAS_BUENAS):
            puntos += 1.0
        try:
            publicado = datetime.fromisoformat(sn.get("publishedAt", "").replace("Z", "+00:00"))
            meses = (ahora - publicado).days / 30
            puntos += 0.7 if meses <= 12 else (0.3 if meses <= 24 else 0)
        except ValueError:
            pass
        mejores.append((puntos, {"id": v["id"], "titulo": titulo, "canal": sn.get("channelTitle", ""),
                                 "vistas": vistas, "minutos": round(minutos, 1)}))
    if not mejores:
        return None
    mejores.sort(key=lambda x: x[0], reverse=True)
    return mejores[0][1]


def bloque_video(video, marca, modelo):
    vid = video["id"]
    nombre = html.escape(f"{marca} {modelo}")
    canal = html.escape(video["canal"])
    titulo = html.escape(video["titulo"])
    return (f'<!-- tc-video:{vid} -->\n'
            f'<div class="tc-video" style="max-width:800px;margin:0 auto 28px;">'
            f'<h2 style="margin:0 0 12px;">Vídeo: análisis de {nombre}</h2>'
            f'<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:12px;">'
            f'<iframe src="https://www.youtube-nocookie.com/embed/{vid}" title="{titulo}" loading="lazy" '
            f'style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" '
            f'allow="accelerometer; encrypted-media; gyroscope; picture-in-picture" allowfullscreen '
            f'referrerpolicy="strict-origin-when-cross-origin"></iframe></div>'
            f'<p style="font-size:.85em;color:#64748b;margin:8px 0 0;">Vídeo de «{canal}» en YouTube. '
            f'<a href="https://www.youtube.com/watch?v={vid}" target="_blank" rel="noopener nofollow">Ver en YouTube</a>. '
            f'Contenido de terceros, ajeno a esta web.</p></div>\n'
            f'<!-- /tc-video -->\n')


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


def main():
    registro = cargar_json(RUTA_PUBLICADOS, {})
    hoy = date.today()
    if MODO_PRUEBA:
        print("🧪 MODO PRUEBA: se muestra qué vídeo se elegiría, pero NO se toca ninguna entrada.\n")
    hechos, sin_video, saltados, revisadas = 0, 0, 0, 0

    # Las entradas más recientes primero: así las que acabas de crear no esperan detrás de las antiguas
    candidatos = [(pid, r) for pid, r in registro.items() if isinstance(r, dict) and r.get("post_id") and r.get("marca")][::-1]
    try:
        for pid, r in candidatos:
            if hechos + sin_video >= MAX_POR_EJECUCION:
                break
            if r.get("video_id") or r.get("video_estado") == "manual":
                continue
            if r.get("video_estado") == "sin_resultado":
                try:
                    if (hoy - date.fromisoformat(r.get("video_intento", "2000-01-01"))).days < REINTENTO_DIAS:
                        continue
                except ValueError:
                    pass
            post = leer_entrada(r["post_id"])
            if not post:
                continue
            if SOLO_BORRADORES and post.get("status") != "draft":
                saltados += 1
                continue
            contenido = (post.get("content") or {}).get("raw", "")
            if re.search(r"youtube(-nocookie)?\.com/embed|youtu\.be/|tc-video", contenido):
                print(f"⏭️ {r['marca']} {r['modelo']}: ya tiene un vídeo de YouTube. No se toca.")
                r["video_estado"] = "manual"
                if not MODO_PRUEBA:
                    guardar_json(RUTA_PUBLICADOS, registro)
                continue

            revisadas += 1
            print(f"\n🎬 {r['marca']} {r['modelo']} (entrada {r['post_id']})")
            try:
                video = elegir_video(r["marca"], r["modelo"])
            except ErrorTemporal:
                print("   ⚠️ Error temporal con YouTube: se reintentará en la próxima ejecución.")
                continue
            if not video:
                print("   ⚠️ No se encontró ningún vídeo que cumpla los filtros.")
                sin_video += 1
                r["video_estado"], r["video_intento"] = "sin_resultado", hoy.isoformat()
                if not MODO_PRUEBA:
                    guardar_json(RUTA_PUBLICADOS, registro)
                continue
            print(f"   ✅ Elegido: «{video['titulo'][:90]}» — {video['canal']} ({video['vistas']:,} visualizaciones, {video['minutos']} min)"
                  f"\n      https://www.youtube.com/watch?v={video['id']}")
            if MODO_PRUEBA:
                hechos += 1
                continue

            nuevo = bloque_video(video, r["marca"], r["modelo"]) + contenido
            try:
                u = requests.post(f"{WP_URL}/wp-json/wp/v2/posts/{r['post_id']}", json={"content": nuevo},
                                  auth=(WP_USER, WP_APP_PASSWORD), timeout=60)
            except requests.RequestException as err:
                print(f"   ❌ Error de conexión al guardar: {err}")
                continue
            if u.status_code != 200:
                print(f"   ❌ WordPress respondió {u.status_code}: {u.text[:200]}")
                continue
            comprobar = leer_entrada(r["post_id"])
            if not comprobar or video["id"] not in (comprobar.get("content") or {}).get("raw", ""):
                print("   ❌ WordPress eliminó el vídeo al guardar (el usuario no tiene permiso para iframes). "
                      "Usa un usuario Administrador. Se detiene la inserción de vídeos.")
                raise SinCuota("WordPress no permite iframes con este usuario")
            r.update({"video_id": video["id"], "video_titulo": video["titulo"], "video_canal": video["canal"],
                      "video_fecha": hoy.isoformat(), "video_estado": "auto"})
            guardar_json(RUTA_PUBLICADOS, registro)
            hechos += 1
            print("   📝 Vídeo insertado en el borrador.")
    except SinCuota as err:
        print(f"\n🛑 Se detiene la inserción de vídeos: {err}.")

    print(f"\n📊 Vídeos {'elegidos (prueba)' if MODO_PRUEBA else 'insertados'}: {hechos} | sin vídeo adecuado: {sin_video} "
          f"| entradas ya publicadas omitidas: {saltados}")


if __name__ == "__main__":
    main()
