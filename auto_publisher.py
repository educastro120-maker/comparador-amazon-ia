import os
import sys
import re
import csv
import html
import json
import time
import unicodedata
from datetime import datetime
import requests
import urllib.parse
from google import genai
from google.genai import types

# ==========================================
# 1. LECTURA SEGURA DE CREDENCIALES
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
WP_URL = os.environ.get("WP_URL", "").rstrip('/')
WP_USER = os.environ.get("WP_USER", "").strip()
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "").strip()

AMAZON_TAG = "topcomparad00-21"

if not GEMINI_API_KEY:
    raise ValueError("❌ ERROR CRÍTICO: La variable de entorno GEMINI_API_KEY está vacía en GitHub Secrets.")

# Timeout de 120 segundos (antes 35): generar una ficha detallada puede tardar más de 35 s y se cortaba
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'timeout': int(os.environ.get('GEMINI_TIMEOUT_MS', '120000'))}
)

# ==========================================
# 2. CATÁLOGO MULTI-CATEGORÍA
# ==========================================
productos_catalogo = [



]


# ==========================================
# 3. AJUSTES, MEMORIA DE LO PUBLICADO Y PROVEEDORES DE IA (NUEVO)
# ==========================================
# Cuántos productos NUEVOS se publican como máximo en cada ejecución. Es la clave para trabajar con
# cuotas gratuitas: el catálogo se completa poco a poco, día a día, sin agotar el límite diario.
MAX_NUEVOS_POR_EJECUCION = int(os.environ.get("MAX_NUEVOS", "4"))
PAUSA_ENTRE_PRODUCTOS = int(os.environ.get("PAUSA_ENTRE_PRODUCTOS", "15"))

# Carpeta del repositorio donde se guarda la "memoria" del programa
CARPETA_DATOS = os.environ.get("CARPETA_DATOS", "data")
RUTA_PUBLICADOS = os.path.join(CARPETA_DATOS, "publicados.json")        # qué productos ya están publicados
RUTA_COLA = os.path.join(CARPETA_DATOS, "cola_catalogo.json")           # productos pendientes (la rellena descubrir_catalogo.py)
CATEGORIA_FILTRO = os.environ.get("SOLO_CATEGORIA", "").strip().lower()   # "", "smartwatch" o "smartphone": publica solo esa categoría
RUTA_ENLACES = os.path.join(CARPETA_DATOS, "enlaces_manual.csv")        # TÚ rellenas aquí el enlace corto y la imagen de cada producto
RUTA_FALLOS = os.path.join(CARPETA_DATOS, "fallos.json")                # cuántas veces ha fallado cada producto
MAX_FALLOS_POR_PRODUCTO = 3   # tras 3 fallos seguidos se aparta el producto para que no bloquee a los demás
RUTA_RANKINGS = os.path.join(CARPETA_DATOS, "rankings.json")            # definición de las páginas Top 10 (etiquetas y miembros)
ESTADO_ENTRADAS = os.environ.get("ESTADO_ENTRADAS", "publish")          # "publish" = publicar; "draft" = guardar como borrador para revisar
MAX_SINCRONIZACIONES = int(os.environ.get("MAX_SINCRONIZACIONES", "25"))  # entradas ya publicadas a las que se añade etiqueta por ejecución

# Categorías para las que este archivo tiene prompt y tabla propios. Otras (monitores, TV...) se
# saltan con un aviso, porque saldrían con secciones que no tienen sentido.
CATEGORIAS_SOPORTADAS = {"smartphone", "smartwatch"}
CAMPOS_OBLIGATORIOS = ("categoria", "marca", "modelo_corto", "busqueda", "titulo", "especificaciones", "precio")

# Proveedores de IA, por orden. Si Gemini agota su cuota, el programa pasa a Groq (gratuito) si has
# creado el secreto GROQ_API_KEY. Los nombres de modelo se pueden cambiar sin tocar el código con las
# variables GEMINI_MODELS (separados por comas) y GROQ_MODEL. Compruébalos en Google AI Studio.
PROVEEDORES = [p.strip().lower() for p in os.environ.get("PROVEEDORES", "gemini,groq").split(",") if p.strip()]
MODELOS_GEMINI = [m.strip() for m in os.environ.get("GEMINI_MODELS", "gemini-3.8-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite").split(",") if m.strip()]
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# Regla que se antepone a TUS prompts (no los modifica): evita que la IA se invente cifras
REGLA_VERACIDAD = (
    "REGLAS DE VERACIDAD (prioridad máxima): usa como fuente principal los datos de 'Especificaciones base'. "
    "Puedes completar con tu conocimiento solo si estás SEGURO de que corresponde al modelo exacto; si dudas, "
    "omite esa línea. No inventes cifras, fechas, precios ni versiones. Responde SOLO con el JSON pedido.\n\n"
)

PREFIJOS_LINK_CORTO = ("https://link.amazon/", "https://amzn.to/", "https://amzn.eu/")
RE_ASIN = re.compile(r"^[A-Z0-9]{10}$")

# Estado interno de la ejecución (no tocar)
_estado = {"gemini_agotado": False, "groq_agotado": False, "modelos_descartados": set()}


def slugify(texto):
    """'Fitbit Versa 4' -> 'fitbit-versa-4'. Sirve como identificador único de cada producto."""
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def slug_producto(producto):
    return slugify(f"{producto['marca']} {producto['modelo_corto']}")


def construir_link_afiliado(producto):
    """1) enlace corto de SiteStripe (https://link.amazon/...), 2) ASIN válido, 3) búsqueda con tu tag."""
    link = (producto.get("link_afiliado") or "").strip()
    if link.startswith(PREFIJOS_LINK_CORTO):
        return link
    asin = (producto.get("asin") or "").strip().upper()
    if RE_ASIN.match(asin):
        return f"https://www.amazon.es/dp/{asin}?tag={AMAZON_TAG}"
    query_encoded = urllib.parse.quote_plus(producto["busqueda"])
    return f"https://www.amazon.es/s?k={query_encoded}&tag={AMAZON_TAG}"


# ---------- Memoria: qué está ya publicado ----------
def cargar_json(ruta, defecto):
    if not os.path.exists(ruta):
        return defecto
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as err:
        print(f"⚠️ No se pudo leer {ruta} ({err}). Se usa un valor vacío.")
        return defecto


def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2)


def registrar_publicado(pid, producto, url_post, affiliate_link, post_id=None, datos_ia=None):
    """Anota el producto en data/publicados.json: evita duplicados y alimenta las páginas Top 10."""
    registro = cargar_json(RUTA_PUBLICADOS, {})
    previo = registro.get(pid) if isinstance(registro.get(pid), dict) else {}
    datos_ia = datos_ia or {}
    registro[pid] = {
        **previo,
        "categoria": producto.get("categoria", ""),
        "marca": producto["marca"],
        "modelo": producto["modelo_corto"],
        "titulo": producto["titulo"],
        "url_post": url_post or previo.get("url_post", ""),
        "post_id": post_id or previo.get("post_id"),
        "link_afiliado": affiliate_link,
        "tiene_link_corto": affiliate_link.startswith(PREFIJOS_LINK_CORTO),
        "precio": producto.get("precio", ""),
        "imagen": (producto.get("imagen") or "").strip(),
        "tiene_imagen": bool((producto.get("imagen") or "").strip()),
        "resumen": str(datos_ia.get("resumen_ejecutivo", "") or previo.get("resumen", ""))[:400],
        "badge": str(datos_ia.get("badge", "") or previo.get("badge", "")),
        "puntuacion": datos_ia.get("puntuacion", previo.get("puntuacion")),
        "fecha": previo.get("fecha") or datetime.now().strftime("%Y-%m-%d"),
    }
    guardar_json(RUTA_PUBLICADOS, registro)


_wp = {"completo": False, "ids": set()}   # ¿se leyó bien la lista de entradas de WordPress? y los IDs que existen


def titulos_publicados_en_wp():
    """
    Lee los títulos de las entradas que YA existen en WordPress (una vez por ejecución) para reconocer
    productos publicados antes de que existiera la memoria y no duplicarlos. Devuelve {titulo_slug: {link, id}}.
    """
    titulos = {}
    _wp["completo"], _wp["ids"] = False, set()
    try:
        pagina = 1
        while pagina <= 20:
            res = requests.get(
                f"{WP_URL}/wp-json/wp/v2/posts",
                params={"per_page": 100, "page": pagina, "context": "edit",
                        "status": "publish,draft,pending,private", "_fields": "id,title,link"},
                auth=(WP_USER, WP_APP_PASSWORD), timeout=30)
            if res.status_code != 200:
                break
            lote = res.json()
            if not lote:
                _wp["completo"] = True
                break
            for p in lote:
                _wp["ids"].add(p.get("id"))
                t = (p.get("title") or {}).get("raw") or ""
                titulos[slugify(t)] = {"link": p.get("link", ""), "id": p.get("id"), "titulo": t}
            if len(lote) < 100:
                _wp["completo"] = True
                break
            pagina += 1
    except (requests.RequestException, ValueError) as err:
        print(f"   ⚠️ No se pudieron leer las entradas existentes de WordPress: {err}")
    return titulos


PALABRAS_VARIANTE = {"pro", "plus", "ultra", "max", "lite", "classic", "fe", "mini", "se", "air", "neo", "turbo", "edge", "fold", "flip", "gt", "active"}
RUTA_YA_CREADOS = os.path.join(CARPETA_DATOS, "ya_creados.txt")   # TÚ: lista de productos que ya tienen entrada (uno por línea)


def _tokens(texto):
    """Palabras normalizadas de un nombre: '40 mm' y '40mm' cuentan igual, 'Pro+' se lee 'pro plus'."""
    t = str(texto).lower().replace("+", " plus ")
    t = re.sub(r"(\d)\s*(mm|gb|tb|mah)\b", r"\1\2", t)
    return set(slugify(t).split("-")) - {""}


def _coincide(buscado, texto):
    """Todas las palabras del modelo están en el texto y el texto no añade otra variante (Pro, Ultra, Classic...)."""
    if not buscado or not buscado <= texto:
        return False
    return not ((texto - buscado) & PALABRAS_VARIANTE)


def leer_ya_creados():
    """data/ya_creados.txt: un producto por línea ('Marca Modelo'). Las líneas con # se ignoran."""
    if not os.path.exists(RUTA_YA_CREADOS):
        return []
    with open(RUTA_YA_CREADOS, "r", encoding="utf-8") as fh:
        return [l.split("#")[0].strip() for l in fh if l.split("#")[0].strip()]


def _nombre_en_titulo(titulo):
    """Solo la parte del título que nombra el producto (antes de ' - ', ' – ' o ':'), sin 'Análisis y Opinión:'.
    Así 'Apple Watch Ultra 4 - ... 3.000 nits' no se confunde con el Ultra 3."""
    t = re.sub(r"^\s*an[aá]lisis y opini[oó]n\s*:\s*", "", str(titulo), flags=re.I)
    return re.split(r"\s[-–—|]\s|:\s", t)[0]


def buscar_post_existente(producto, titulos_wp):
    """Busca en WordPress la entrada de este producto: 1) título exacto, 2) por parecido (marca + modelo)."""
    exacto = titulos_wp.get(slugify(f"Análisis y Opinión: {producto['titulo']}"))
    if exacto:
        return exacto, "exacto"
    buscado = _tokens(f"{producto['marca']} {producto['modelo_corto']}")
    candidatos = [i for i in titulos_wp.values() if _coincide(buscado, _tokens(_nombre_en_titulo(i.get("titulo", ""))))]
    if len(candidatos) == 1:
        return candidatos[0], "parecido"
    if len(candidatos) > 1:
        print(f"   ⚠️ {producto['marca']} {producto['modelo_corto']}: varias entradas parecidas, se usa la primera ({candidatos[0].get('titulo','')[:70]}).")
        return candidatos[0], "parecido"
    return None, ""


def olvidar_publicado(pid):
    reg = cargar_json(RUTA_PUBLICADOS, {})
    if pid in reg:
        del reg[pid]
        guardar_json(RUTA_PUBLICADOS, reg)


def producto_ya_publicado(pid, producto, registro, titulos_wp):
    """True si el producto está en la memoria, en tu lista data/ya_creados.txt o ya existe su entrada en WordPress."""
    reg = registro.get(pid)
    if isinstance(reg, dict) and reg.get("post_id") and _wp["completo"] and reg["post_id"] not in _wp["ids"]:
        # La entrada que recordábamos ya no existe en WordPress (la borraste). Se olvida y se vuelve a evaluar.
        print(f"♻️ {producto['marca']} {producto['modelo_corto']}: su entrada (ID {reg['post_id']}) ya no existe en WordPress. Se revisa de nuevo.")
        olvidar_publicado(pid)
        registro.pop(pid, None)
    elif pid in registro:
        return True
    info, modo = buscar_post_existente(producto, titulos_wp)
    if info:
        if modo == "parecido":
            print(f"🔎 Ya existe entrada para {producto['marca']} {producto['modelo_corto']} (por parecido): «{info.get('titulo','')[:80]}». No se crea otra.")
        registrar_publicado(pid, producto, info["link"], construir_link_afiliado(producto), post_id=info["id"])
        registro[pid] = True
        return True
    buscado = _tokens(f"{producto['marca']} {producto['modelo_corto']}")
    for linea in leer_ya_creados():
        if pid == slugify(linea) or _coincide(_tokens(linea), buscado) and _coincide(buscado, _tokens(linea)):
            print(f"📋 {producto['marca']} {producto['modelo_corto']}: está en data/ya_creados.txt. No se crea otra entrada.")
            registrar_publicado(pid, producto, "", construir_link_afiliado(producto))
            registro[pid] = True
            return True
    return False

# ---------- Rankings (páginas Top 10), etiquetas y sincronización ----------
_cache = {"rankings": None, "etiquetas": {}}


def cargar_rankings():
    if _cache["rankings"] is None:
        _cache["rankings"] = cargar_json(RUTA_RANKINGS, [])
    return _cache["rankings"]


def ids_miembros(ranking):
    return {slugify(f"{m['marca']} {m['modelo_corto']}") for m in ranking.get("miembros", [])}


def rankings_de_producto(pid):
    """Rankings (páginas Top 10) en los que aparece este producto."""
    return [r for r in cargar_rankings() if pid in ids_miembros(r)]


def obtener_o_crear_etiqueta(nombre):
    """Busca la etiqueta en WordPress y, si no existe, la crea. No hace falta crearlas a mano."""
    if nombre in _cache["etiquetas"]:
        return _cache["etiquetas"][nombre]
    endpoint = f"{WP_URL}/wp-json/wp/v2/tags"
    etiqueta_id = None
    try:
        res = requests.get(endpoint, params={"search": nombre, "per_page": 100}, auth=(WP_USER, WP_APP_PASSWORD), timeout=15)
        if res.status_code == 200:
            for t in res.json():
                if html.unescape(t.get("name", "")).strip().lower() == nombre.strip().lower():
                    etiqueta_id = t["id"]
                    break
        if etiqueta_id is None:
            res = requests.post(endpoint, json={"name": nombre}, auth=(WP_USER, WP_APP_PASSWORD), timeout=15)
            if res.status_code == 201:
                etiqueta_id = res.json()["id"]
            elif res.status_code == 400 and "term_exists" in res.text:
                etiqueta_id = res.json().get("data", {}).get("term_id")   # ya existía: se reutiliza
            else:
                print(f"   ⚠️ No se pudo crear la etiqueta '{nombre}' ({res.status_code}). ¿El usuario de WordPress es Administrador o Editor?")
    except (requests.RequestException, ValueError, KeyError) as err:
        print(f"   ⚠️ Advertencia al gestionar la etiqueta '{nombre}': {err}")
    _cache["etiquetas"][nombre] = etiqueta_id
    return etiqueta_id


def etiquetas_para_producto(pid):
    ids = [obtener_o_crear_etiqueta(r["etiqueta"]) for r in rankings_de_producto(pid) if r.get("etiqueta")]
    return [i for i in ids if i]


def sincronizar_taxonomias():
    """
    Añade las etiquetas de ranking a entradas YA publicadas (por ejemplo, publicadas antes de definir el ranking).
    Hace como máximo MAX_SINCRONIZACIONES por ejecución para no sobrecargar WordPress.
    """
    registro = cargar_json(RUTA_PUBLICADOS, {})
    rankings = cargar_rankings()
    hechas = 0
    for pid, r in registro.items():
        if not isinstance(r, dict) or not r.get("post_id"):
            continue
        faltan = [rk for rk in rankings if rk.get("etiqueta") and pid in ids_miembros(rk)
                  and rk["id"] not in r.get("rankings_sincronizados", [])]
        if not faltan:
            continue
        if hechas >= MAX_SINCRONIZACIONES:
            break
        try:
            res = requests.get(f"{WP_URL}/wp-json/wp/v2/posts/{r['post_id']}", params={"context": "edit", "_fields": "tags"},
                               auth=(WP_USER, WP_APP_PASSWORD), timeout=20)
            if res.status_code != 200:
                print(f"   ⚠️ No se pudo leer la entrada {r['post_id']} de {r.get('marca', '')} {r.get('modelo', '')} ({res.status_code}).")
                continue
            actuales = res.json().get("tags", [])
            nuevas_ids = [i for i in (obtener_o_crear_etiqueta(rk["etiqueta"]) for rk in faltan) if i]
            union = sorted(set(actuales) | set(nuevas_ids))
            if union != sorted(actuales):
                upd = requests.post(f"{WP_URL}/wp-json/wp/v2/posts/{r['post_id']}", json={"tags": union},
                                    auth=(WP_USER, WP_APP_PASSWORD), timeout=30)
                if upd.status_code != 200:
                    print(f"   ⚠️ No se pudo etiquetar la entrada {r['post_id']} ({upd.status_code}).")
                    continue
            r["rankings_sincronizados"] = sorted(set(r.get("rankings_sincronizados", [])) | {rk["id"] for rk in faltan})
            hechas += 1
            print(f"   🏷️ Etiquetada: {r.get('marca', '')} {r.get('modelo', '')}")
        except (requests.RequestException, ValueError) as err:
            print(f"   ⚠️ Error sincronizando la entrada {r.get('post_id')}: {err}")
    if hechas:
        guardar_json(RUTA_PUBLICADOS, registro)
    return hechas


def actualizar_registro_desde_catalogo(pid, item):
    """Si pones el enlace corto o la imagen en el catálogo, se copian a la memoria (las usan las páginas Top 10)."""
    registro = cargar_json(RUTA_PUBLICADOS, {})
    r = registro.get(pid)
    if not isinstance(r, dict):
        return
    cambio = False
    nuevo_link = construir_link_afiliado(item)
    if nuevo_link.startswith(PREFIJOS_LINK_CORTO) and r.get("link_afiliado") != nuevo_link:
        r["link_afiliado"], r["tiene_link_corto"], cambio = nuevo_link, True, True
    img = (item.get("imagen") or "").strip()
    if img and r.get("imagen") != img:
        r["imagen"], r["tiene_imagen"], cambio = img, True, True
    if cambio:
        guardar_json(RUTA_PUBLICADOS, registro)


# ---------- IA: Gemini con respaldo en Groq ----------
def _json_desde_texto(texto):
    """Extrae el primer objeto JSON de un texto (por si llega con ``` o con texto alrededor)."""
    texto = (texto or "").strip()
    a, b = texto.find("{"), texto.rfind("}")
    if a == -1 or b == -1:
        raise ValueError("la respuesta no contiene JSON")
    return json.loads(texto[a:b + 1])


def _es_cuota_diaria(txt):
    t = txt.lower()
    return any(k in t for k in ("perday", "per day", "requests per day", "(rpd)", "(tpd)", "tokens per day"))


def llamar_gemini(prompt):
    if _estado["gemini_agotado"]:
        return None
    for modelo in MODELOS_GEMINI:
        if modelo in _estado["modelos_descartados"]:
            continue
        for intento in range(1, 3):
            try:
                print(f"   🤖 Llamando a {modelo} (intento {intento})...")
                response = client.models.generate_content(
                    model=modelo, contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.3,
                        max_output_tokens=8192,   # antes 4096: una ficha detallada se cortaba a medias
                    ))
                if response and response.text:
                    return _json_desde_texto(response.text)
                print("   ⚠️ Respuesta vacía (puede ser por el límite de tokens).")
            except Exception as e:
                txt = str(e)
                print(f"   ⚠️ Fallo con {modelo} (intento {intento}): {type(e).__name__} -> {txt[:300]}")
                if "404" in txt or "NOT_FOUND" in txt:
                    print(f"   🚫 El modelo {modelo} no existe o está retirado. Se descarta en esta ejecución.")
                    _estado["modelos_descartados"].add(modelo)
                    break
                if "429" in txt or "RESOURCE_EXHAUSTED" in txt:
                    if _es_cuota_diaria(txt):
                        print(f"   🛑 Cuota DIARIA agotada para {modelo}. No se reintenta.")
                        _estado["modelos_descartados"].add(modelo)
                        break
                    print("   ⏳ Límite por minuto: esperando 62 segundos...")
                    time.sleep(62)
                else:
                    time.sleep(4)
    if all(m in _estado["modelos_descartados"] for m in MODELOS_GEMINI):
        _estado["gemini_agotado"] = True
    return None


def llamar_groq(prompt):
    """Respaldo gratuito: Groq (formato compatible con OpenAI). Requiere el secreto GROQ_API_KEY."""
    if not GROQ_API_KEY or _estado["groq_agotado"]:
        return None
    for intento in range(1, 4):
        try:
            print(f"   🤖 Llamando a Groq {GROQ_MODEL} (intento {intento})...")
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.3, "max_tokens": 6000, "response_format": {"type": "json_object"}},
                timeout=120)
            if r.status_code == 200:
                return _json_desde_texto(r.json()["choices"][0]["message"]["content"])
            print(f"   ⚠️ Groq respondió {r.status_code}: {r.text[:300]}")
            if r.status_code == 429:
                if _es_cuota_diaria(r.text):
                    print("   🛑 Cuota diaria de Groq agotada.")
                    _estado["groq_agotado"] = True
                    return None
                try:
                    espera = int(float(r.headers.get("retry-after", "30"))) + 2
                except ValueError:
                    espera = 32
                time.sleep(min(espera, 70))
            else:
                time.sleep(4)
        except Exception as e:
            print(f"   ⚠️ Error llamando a Groq (intento {intento}): {type(e).__name__} -> {str(e)[:200]}")
            time.sleep(4)
    return None


def ia_agotada():
    """True si ya no queda ningún proveedor de IA utilizable en esta ejecución."""
    gemini_ok = ("gemini" in PROVEEDORES) and not _estado["gemini_agotado"]
    groq_ok = ("groq" in PROVEEDORES) and bool(GROQ_API_KEY) and not _estado["groq_agotado"]
    return not (gemini_ok or groq_ok)


def llamar_gemini_con_respaldo(prompt):
    """Mantiene el nombre original: prueba cada proveedor por orden y devuelve el JSON de la ficha."""
    prompt_final = REGLA_VERACIDAD + prompt
    for proveedor in PROVEEDORES:
        datos = llamar_gemini(prompt_final) if proveedor == "gemini" else llamar_groq(prompt_final) if proveedor == "groq" else None
        if isinstance(datos, dict) and datos:
            return datos
    return None


def formatear_item_negrita(texto):
    """Si un item tiene formato 'Etiqueta: Valor', pone la etiqueta en negrita automáticamente."""
    if ":" in texto:
        partes = texto.split(":", 1)
        return f"<strong>{partes[0].strip()}:</strong> {partes[1].strip()}"
    return texto


def render_bullets(items):
    """Convierte una lista de strings en elementos de lista HTML con viñetas y etiquetas en negrita."""
    if isinstance(items, list):
        return "".join([f"<li style='margin-bottom: 5px;'>{formatear_item_negrita(item)}</li>" for item in items])
    return f"<li>{formatear_item_negrita(str(items))}</li>"


def obtener_o_crear_categoria(nombre_cat_input):
    """Busca la categoría en WordPress por su nombre (ej: 'Smartphones'). Si no existe, la crea."""
    nombre_categoria = nombre_cat_input.capitalize()
    if nombre_categoria.lower() == 'smartphone':
        nombre_categoria = 'Smartphones'
    elif nombre_categoria.lower() == 'smartwatch':
        nombre_categoria = 'Smartwatches'

    cat_endpoint = f"{WP_URL}/wp-json/wp/v2/categories"
    
    try:
        res = requests.get(cat_endpoint, params={"search": nombre_categoria}, auth=(WP_USER, WP_APP_PASSWORD), timeout=15)
        if res.status_code == 200:
            categorias = res.json()
            for cat in categorias:
                if cat['name'].lower() == nombre_categoria.lower():
                    return cat['id']
        
        payload_cat = {"name": nombre_categoria}
        res_crear = requests.post(cat_endpoint, json=payload_cat, auth=(WP_USER, WP_APP_PASSWORD), timeout=15)
        if res_crear.status_code == 201:
            return res_crear.json()['id']
    except Exception as e:
        print(f"   ⚠️ Advertencia al gestionar categoría en WordPress: {e}")
    
    return None


def procesar_y_publicar(producto):
    """Devuelve "publicado", "saltado" (ya existía) o False (fallo)."""
    pid = slug_producto(producto)
    affiliate_link = construir_link_afiliado(producto)   # NUEVO: usa tu enlace corto si lo has puesto
    
    categoria_str = producto.get('categoria', 'smartwatch').lower()
    imagen_url = producto.get('imagen', '').strip()
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")

    # --- PROMPTS EXHAUSTIVOS PARA FICHA TÉCNICA DETALLADA ---
    if categoria_str == 'smartphone':
        prompt = f"""
        Actúa como un analista experto en hardware móvil, SEO técnico y CRO para una web comparadora de productos de Amazon.
        Analiza en máxima profundidad este smartphone basándote en los datos aportados y tu conocimiento técnico del modelo exacto:
        - Marca y Modelo: {producto['marca']} {producto['modelo_corto']}
        - Título: {producto['titulo']}
        - Especificaciones base: {producto['especificaciones']}
        - Precio: {producto['precio']}

        REGLAS ESTRICTAS DE CONTENIDO (MUY IMPORTANTE):
        1. No hagas resúmenes cortos. Queremos una Ficha Técnica Detallada y exhaustiva donde cada categoría de "specs" tenga entre 5 y 8 viñetas individuales.
        2. Usa SIEMPRE el formato "Característica: Dato técnico exacto" en cada viñeta (ej. "Panel: LTPO AMOLED de 6,8 pulgadas", "Tasa de refresco: 1-120 Hz adaptativos", etc.). Nunca dejes datos genéricos si se conocen las especificaciones reales del modelo.
        3. El "resumen_ejecutivo" debe ser un párrafo rico, experto y persuasivo de unas 90-120 palabras.
        4. Incluye exactamente 6 Pros detallados y 4 Contras detallados, todos con formato "Título corto: Explicación detallada".

        Devuelve ÚNICAMENTE un objeto JSON válido con esta estructura exacta:
        {{
            "badge": "ETIQUETA CORTA EN MAYÚSCULAS (ej: REFERENCIA EN FOTOGRAFÍA MÓVIL)",
            "resumen_ejecutivo": "Párrafo extenso, técnico y persuasivo de 90-120 palabras.",
            "specs": {{
                "pantalla": [
                    "Panel: ...",
                    "Tamaño: ...",
                    "Resolución: ...",
                    "Tasa de refresco: ...",
                    "Brillo máximo: ...",
                    "Protección: ..."
                ],
                "rendimiento": [
                    "Procesador: ...",
                    "Arquitectura / GPU: ...",
                    "Memoria RAM: ...",
                    "Sistema operativo: ...",
                    "Inteligencia Artificial: ...",
                    "Refrigeración: ..."
                ],
                "camaras": [
                    "Sensor principal: ...",
                    "Teleobjetivo(s): ...",
                    "Ultra gran angular: ...",
                    "Cámara frontal: ...",
                    "Grabación de vídeo: ...",
                    "Óptica / Procesado: ..."
                ],
                "bateria": [
                    "Capacidad: ...",
                    "Carga rápida por cable: ...",
                    "Carga inalámbrica: ...",
                    "Carga inversa: ...",
                    "Autonomía estimada: ..."
                ],
                "almacenamiento": [
                    "Capacidad interna: ...",
                    "Tecnología de memoria: ...",
                    "Ampliación microSD: ...",
                    "Versiones disponibles: ..."
                ],
                "conectividad": [
                    "Redes móviles: ...",
                    "Wi-Fi: ...",
                    "Bluetooth: ...",
                    "NFC: ...",
                    "Navegación / GPS: ...",
                    "Puerto y audio: ...",
                    "Resistencia y construcción: ..."
                ]
            }},
            "pros": [
                "Ventaja 1: Explicación detallada...",
                "Ventaja 2: Explicación detallada...",
                "Ventaja 3: Explicación detallada...",
                "Ventaja 4: Explicación detallada...",
                "Ventaja 5: Explicación detallada...",
                "Ventaja 6: Explicación detallada..."
            ],
            "contras": [
                "Desventaja 1: Explicación detallada...",
                "Desventaja 2: Explicación detallada...",
                "Desventaja 3: Explicación detallada...",
                "Desventaja 4: Explicación detallada..."
            ],
            "puntuacion": 9.4
        }}
        """
    else:
        prompt = f"""
        Actúa como un analista experto en wearables, deporte, SEO técnico y CRO para una web comparadora de productos de Amazon.
        Analiza en máxima profundidad este smartwatch basándote en los datos aportados y tu conocimiento técnico del modelo exacto:
        - Marca y Modelo: {producto['marca']} {producto['modelo_corto']}
        - Título: {producto['titulo']}
        - Especificaciones base: {producto['especificaciones']}
        - Precio: {producto['precio']}

        REGLAS ESTRICTAS DE CONTENIDO (MUY IMPORTANTE):
        1. Queremos una Ficha Técnica Detallada y exhaustiva donde cada categoría de "specs" tenga entre 5 y 8 viñetas individuales.
        2. Usa SIEMPRE el formato "Característica: Dato técnico exacto" en cada viñeta (ej. "Panel: AMOLED", "Tamaño: 1.4 pulgadas", "Resolución: 454x454 píxeles", "Autonomía reloj: Hasta 16 días", etc.).
        3. El "resumen_ejecutivo" debe ser un párrafo rico, experto y persuasivo de unas 90-120 palabras.
        4. Incluye exactamente 6 Pros detallados y 4 Contras detallados, todos con formato "Título corto: Explicación detallada".

        Devuelve ÚNICAMENTE un objeto JSON válido con esta estructura exacta:
        {{
            "badge": "ETIQUETA CORTA EN MAYÚSCULAS (ej: REFERENCIA MULTIDEPORTE PREMIUM)",
            "resumen_ejecutivo": "Párrafo extenso, técnico y persuasivo de 90-120 palabras.",
            "specs": {{
                "pantalla": [
                    "Panel: ...",
                    "Tamaño: ...",
                    "Resolución: ...",
                    "Protección: ...",
                    "Siempre activa: ...",
                    "Control: ..."
                ],
                "bateria": [
                    "Autonomía reloj: ...",
                    "Autonomía GPS: ...",
                    "Carga solar / rápida: ...",
                    "Modo ahorro: ...",
                    "Tipo de carga: ..."
                ],
                "conectividad": [
                    "Wi-Fi: ...",
                    "NFC: ...",
                    "GNSS: ...",
                    "Almacenamiento: ...",
                    "Audio: ...",
                    "Llamadas: ...",
                    "Mapas: ..."
                ],
                "sensores": [
                    "Frecuencia cardíaca: ...",
                    "Oxígeno en sangre: ...",
                    "ECG: ...",
                    "Temperatura: ...",
                    "Altímetro: ...",
                    "Profundidad: ...",
                    "Otros: ..."
                ],
                "deportes": [
                    "Perfiles: ...",
                    "Buceo / Agua: ...",
                    "Entrenamiento: ...",
                    "Navegación: ...",
                    "Salud: ..."
                ],
                "construccion": [
                    "Caja: ...",
                    "Bisel: ...",
                    "Fondo: ...",
                    "Correa: ...",
                    "Resistencia agua: ...",
                    "Dimensiones: ...",
                    "Peso: ...",
                    "Sistema operativo: ..."
                ]
            }},
            "pros": [
                "Ventaja 1: Explicación detallada...",
                "Ventaja 2: Explicación detallada...",
                "Ventaja 3: Explicación detallada...",
                "Ventaja 4: Explicación detallada...",
                "Ventaja 5: Explicación detallada...",
                "Ventaja 6: Explicación detallada..."
            ],
            "contras": [
                "Desventaja 1: Explicación detallada...",
                "Desventaja 2: Explicación detallada...",
                "Desventaja 3: Explicación detallada...",
                "Desventaja 4: Explicación detallada..."
            ],
            "puntuacion": 9.3
        }}
        """

    print(f"   🔍 Analizando en profundidad ({categoria_str.upper()}): {producto['modelo_corto']}...")
    datos_ia = llamar_gemini_con_respaldo(prompt)

    if not datos_ia:
        print(f"❌ ABORTANDO PUBLICACIÓN de '{producto['modelo_corto']}': Gemini no devolvió datos válidos.")
        return False

    s = datos_ia.get('specs', {})

    # --- CONSTRUCCIÓN DE FILAS DE LA TABLA ---
    if categoria_str == 'smartphone':
        spec_rows = [
            ("📺 Pantalla", s.get('pantalla', [])),
            ("⚡ Rendimiento", s.get('rendimiento', [])),
            ("📸 Cámaras", s.get('camaras', [])),
            ("🔋 Batería", s.get('bateria', [])),
            ("💾 Almacenamiento", s.get('almacenamiento', [])),
            ("🌐 Conectividad", s.get('conectividad', []))
        ]
    else:
        spec_rows = [
            ("📺 Pantalla", s.get('pantalla', [])),
            ("🔋 Batería", s.get('bateria', [])),
            ("🌐 Conectividad", s.get('conectividad', [])),
            ("💓 Sensores", s.get('sensores', [])),
            ("🏃‍♂️ Deportes", s.get('deportes', [])),
            ("🛡️ Construcción", s.get('construccion', []))
        ]

    html_rows_str = ""
    for idx, (label, values) in enumerate(spec_rows):
        is_first = (idx == 0)
        is_last = (idx == len(spec_rows) - 1)
        td_top_left = " border-top-left-radius: 6px;" if is_first else ""
        td_bottom_left = " border-bottom-left-radius: 6px;" if is_last else ""
        border_bottom = " border-bottom: 1px solid #e2e8f0;" if not is_last else ""
        
        html_rows_str += f"""
          <tr style="border: none;{border_bottom}">
            <td style="padding: 12px 14px; font-weight: bold; width: 28%; vertical-align: top; border: none; background-color: #f1f5f9;{td_top_left}{td_bottom_left}">{label}</td>
            <td style="padding: 12px 14px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.55;">
                {render_bullets(values)}
              </ul>
            </td>
          </tr>
        """

    bloque_imagen = ""
    if imagen_url:
        bloque_imagen = f"""
        <div style="text-align: center; margin-bottom: 20px;">
          <img src="{imagen_url}" alt="{producto['titulo']}" style="max-height: 280px; width: auto; object-fit: contain; border-radius: 8px;" />
        </div>
        """

    # --- HTML DE LA ENTRADA ---
    html_content = f"""
    <div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 24px; background-color: #ffffff; max-width: 780px; margin: 20px auto; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
      
      {bloque_imagen}

      <div style="background-color: #ff9900; color: #fff; font-weight: bold; display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 0.85em; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px;">
        🔥 {datos_ia.get('badge', 'DESTACADO')}
      </div>

      <h2 style="margin-top: 0; color: #111; font-size: 1.6em; line-height: 1.3;">{producto['titulo']}</h2>
      
      <p style="font-size: 1.08em; color: #334155; line-height: 1.65;">
        {datos_ia.get('resumen_ejecutivo', '')}
      </p>

      <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 18px; margin: 24px 0;">
        <h3 style="color: #0f172a; margin-top: 0; font-size: 1.15em; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; margin-bottom: 12px;">⚙️ Ficha Técnica Detallada</h3>
        
        <table style="width: 100%; border-collapse: collapse; border: none; font-size: 0.95em; color: #1e293b;">
          {html_rows_str}
        </table>
      </div>

      <div style="display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 280px; background-color: #f0fdf4; padding: 18px; border-radius: 8px; border-left: 4px solid #22c55e;">
          <h4 style="color: #15803d; margin-top: 0; font-size: 1.1em;">✅ Lo Mejor (Pros)</h4>
          <ul style="padding-left: 18px; color: #166534; margin-bottom: 0; line-height: 1.55;">
            {render_bullets(datos_ia.get('pros', []))}
          </ul>
        </div>
        
        <div style="flex: 1; min-width: 280px; background-color: #fef2f2; padding: 18px; border-radius: 8px; border-left: 4px solid #ef4444;">
          <h4 style="color: #b91c1c; margin-top: 0; font-size: 1.1em;">❌ A mejorar (Contras)</h4>
          <ul style="padding-left: 18px; color: #991b1b; margin-bottom: 0; line-height: 1.55;">
            {render_bullets(datos_ia.get('contras', []))}
          </ul>
        </div>
      </div>

      <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
        <p style="font-size: 1.3em; font-weight: bold; color: #111; margin-bottom: 6px;">
          Precio orientativo: <span style="color: #b12704;">{producto['precio']}</span> | Puntuación: ⭐ <strong>{datos_ia.get('puntuacion', 9.0)}/10</strong>
        </p>
        <p style="font-size: 0.85em; color: #64748b; margin-top: 0; margin-bottom: 18px;">
          Precio de referencia a fecha {fecha_hoy}; puede variar. Consulta el precio actual en Amazon.
        </p>
        <a href="{affiliate_link}" target="_blank" rel="sponsored nofollow" style="background-color: #ffa41c; color: #111; text-decoration: none; font-size: 1.2em; font-weight: bold; padding: 16px 32px; border-radius: 8px; border: 1px solid #ff8f00; display: inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
          Ver precio actualizado en Amazon 🛒
        </a>
      </div>
    </div>
    """

    categoria_id = obtener_o_crear_categoria(categoria_str)
    etiquetas_ids = etiquetas_para_producto(pid)   # NUEVO: etiquetas de los Top 10 en los que aparece

    meta_payload = {
        "top_marca": producto['marca'],
        "top_modelo": producto['modelo_corto'],
        "top_busqueda": producto['busqueda'],
        "producto_categoria": categoria_str
    }

    if categoria_str == 'smartphone':
        meta_payload.update({
            "spec_pantalla": str(s.get('pantalla', [])),
            "spec_rendimiento": str(s.get('rendimiento', [])),
            "spec_camaras": str(s.get('camaras', [])),
            "spec_bateria": str(s.get('bateria', [])),
            "spec_almacenamiento": str(s.get('almacenamiento', [])),
            "spec_conectiv": str(s.get('conectividad', []))
        })
    else:
        meta_payload.update({
            "spec_pantalla": str(s.get('pantalla', [])),
            "spec_bateria": str(s.get('bateria', [])),
            "spec_conectiv": str(s.get('conectividad', [])),
            "spec_sensores": str(s.get('sensores', [])),
            "spec_deportes": str(s.get('deportes', [])),
            "spec_cuerpo": str(s.get('construccion', []))
        })

    wp_endpoint = f"{WP_URL}/wp-json/wp/v2/posts"
    payload = {
        "title": f"Análisis y Opinión: {producto['titulo']}",
        "content": html_content,
        "status": ESTADO_ENTRADAS,
        "slug": f"analisis-{pid}",
        "meta": meta_payload
    }

    if categoria_id:
        payload["categories"] = [categoria_id]
    if etiquetas_ids:
        payload["tags"] = etiquetas_ids

    try:
        res = requests.post(wp_endpoint, json=payload, auth=(WP_USER, WP_APP_PASSWORD), timeout=30)
        if res.status_code == 201:
            print(f"✅ ¡Publicación detallada creada exitosamente para {producto['titulo']} (Categoría ID: {categoria_id})!")
            try:
                info = res.json()
                url_post, post_id = info.get("link", ""), info.get("id")
            except ValueError:
                url_post, post_id = "", None
            registrar_publicado(pid, producto, url_post, affiliate_link, post_id, datos_ia)   # NUEVO: la memoria evita duplicados
            return "publicado"
        else:
            print(f"❌ Error al publicar en WordPress ({res.status_code}): {res.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Error de tiempo de espera (Timeout) al conectar con WordPress para {producto['titulo']}.")
        return False
    except Exception as e:
        print(f"❌ Error crítico de red al publicar en WordPress: {e}")
        return False


CABECERA_ENLACES = ["id", "categoria", "marca", "modelo", "url_post", "link_afiliado", "imagen"]


def leer_enlaces_manual():
    """Lee data/enlaces_manual.csv (acepta ';' o ','). Devuelve {id: {"link_afiliado": ..., "imagen": ...}}."""
    if not os.path.exists(RUTA_ENLACES):
        return {}
    try:
        with open(RUTA_ENLACES, "r", encoding="utf-8-sig", newline="") as fh:
            texto = fh.read()
    except OSError as err:
        print(f"⚠️ No se pudo leer {RUTA_ENLACES}: {err}")
        return {}
    primera = texto.splitlines()[0] if texto.strip() else ""
    delim = ";" if primera.count(";") >= primera.count(",") else ","
    datos = {}
    for fila in csv.DictReader(texto.splitlines(), delimiter=delim):
        pid = (fila.get("id") or "").strip()
        if not pid:
            continue
        link = (fila.get("link_afiliado") or "").strip()
        img = (fila.get("imagen") or "").strip()
        if link and not link.startswith(PREFIJOS_LINK_CORTO):
            print(f"⚠️ {pid}: el enlace '{link}' no es un enlace corto de Amazon (debe empezar por {' o '.join(PREFIJOS_LINK_CORTO)}). Se ignora.")
            link = ""
        if img and not img.lower().startswith(("http://", "https://")):
            print(f"⚠️ {pid}: la imagen '{img}' no es una URL (debe empezar por https://). Se ignora.")
            img = ""
        datos[pid] = {"link_afiliado": link, "imagen": img}
    return datos


def aplicar_enlaces_manual(registro):
    """Copia al registro los enlaces e imágenes que hayas rellenado en el CSV. Devuelve cuántos productos cambian."""
    manual = leer_enlaces_manual()
    reg = cargar_json(RUTA_PUBLICADOS, {})
    cambios = 0
    for pid, m in manual.items():
        r = reg.get(pid)
        if not isinstance(r, dict):
            continue
        cambio = False
        if m["link_afiliado"] and r.get("link_afiliado") != m["link_afiliado"]:
            r["link_afiliado"], r["tiene_link_corto"], cambio = m["link_afiliado"], True, True
        if m["imagen"] and r.get("imagen") != m["imagen"]:
            r["imagen"], r["tiene_imagen"], cambio = m["imagen"], True, True
        cambios += cambio
    if cambios:
        guardar_json(RUTA_PUBLICADOS, reg)
    return cambios


def aplicar_enlaces_a_item(item, pid, manual):
    """Antes de publicar un producto nuevo, usa el enlace/imagen del CSV si ya los has rellenado."""
    m = manual.get(pid)
    if m:
        if m["link_afiliado"] and not (item.get("link_afiliado") or "").strip():
            item["link_afiliado"] = m["link_afiliado"]
        if m["imagen"] and not (item.get("imagen") or "").strip():
            item["imagen"] = m["imagen"]


def escribir_enlaces_manual(registro):
    """
    Reescribe data/enlaces_manual.csv con una fila por producto publicado, conservando lo que ya hayas rellenado.
    Los que aún no tienen enlace corto o imagen aparecen primero. Devuelve cuántos faltan.
    """
    manual = leer_enlaces_manual()
    filas = []
    for pid, r in registro.items():
        if not isinstance(r, dict):
            continue
        link = manual.get(pid, {}).get("link_afiliado") or (r.get("link_afiliado") if r.get("tiene_link_corto") else "")
        img = manual.get(pid, {}).get("imagen") or r.get("imagen", "")
        filas.append([pid, r.get("categoria", ""), r.get("marca", ""), r.get("modelo", ""), r.get("url_post", ""), link or "", img or ""])
    filas.sort(key=lambda f: (bool(f[5]) and bool(f[6]), f[1], f[2], f[3]))
    os.makedirs(CARPETA_DATOS, exist_ok=True)
    with open(RUTA_ENLACES, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(CABECERA_ENLACES)
        w.writerows(filas)
    return sum(1 for f in filas if not (f[5] and f[6]))


def registrar_miembros_existentes(titulos_wp):
    """
    Los productos de tus Top 10 que ya tienen entrada en WordPress (publicados con versiones anteriores) se anotan
    en la memoria con su ID, para poder etiquetarlos y enlazarlos desde la página Top 10 sin volver a generarlos.
    """
    reg = cargar_json(RUTA_PUBLICADOS, {})
    añadidos = 0
    for rk in cargar_rankings():
        for m in rk.get("miembros", []):
            pid = slugify(f"{m['marca']} {m['modelo_corto']}")
            r = reg.get(pid)
            if isinstance(r, dict) and r.get("post_id"):
                continue
            info, _ = buscar_post_existente({"marca": m["marca"], "modelo_corto": m["modelo_corto"], "titulo": m.get("titulo", "")}, titulos_wp)
            if not info:
                continue
            producto = {"categoria": rk.get("categoria", ""), "marca": m["marca"], "modelo_corto": m["modelo_corto"],
                        "titulo": m.get("titulo", ""), "precio": m.get("precio", ""), "busqueda": m.get("busqueda", ""),
                        "imagen": (r or {}).get("imagen", "") if isinstance(r, dict) else ""}
            enlace = (r.get("link_afiliado") if isinstance(r, dict) else "") or construir_link_afiliado(
                {"busqueda": m.get("busqueda") or m["modelo_corto"], "asin": m.get("asin", ""), "link_afiliado": m.get("link_afiliado", "")})
            registrar_publicado(pid, producto, info["link"], enlace, post_id=info["id"])
            añadidos += 1
    return añadidos


def main():
    registro = cargar_json(RUTA_PUBLICADOS, {})
    cola = cargar_json(RUTA_COLA, [])
    titulos_wp = titulos_publicados_en_wp()

    # Productos de tus Top 10 que ya estaban publicados antes de existir la memoria
    reconocidos = registrar_miembros_existentes(titulos_wp)
    if reconocidos:
        print(f"🔗 Entradas ya existentes reconocidas para tus Top 10: {reconocidos}")
    registro = cargar_json(RUTA_PUBLICADOS, {})
    # Enlaces cortos e imágenes que hayas rellenado en data/enlaces_manual.csv
    enlaces_aplicados = aplicar_enlaces_manual(registro)
    if enlaces_aplicados:
        print(f"🖇️ Enlaces/imágenes del CSV aplicados a {enlaces_aplicados} productos.")
    manual = leer_enlaces_manual()

    # Candidatos: 1) lo escrito a mano en este archivo, 2) los productos de tus Top 10, 3) la cola automática
    candidatos = [("archivo", it) for it in productos_catalogo]
    # NUEVO: los productos de data/rankings.json (tus Top 10). Se publican antes que los descubiertos al azar.
    candidatos += [("ranking", {**m, "categoria": rk.get("categoria", "")}) for rk in cargar_rankings() for m in rk.get("miembros", [])]
    candidatos += [("cola", it) for it in cola if it.get("estado", "pendiente") == "pendiente"]

    pendientes, ya_publicados, descartados, vistos = [], 0, 0, set()
    for origen, it in candidatos:
        faltan = [c for c in CAMPOS_OBLIGATORIOS if not str(it.get(c, "")).strip()]
        if faltan:
            print(f"⚠️ Se descarta un producto por faltarle campos: {', '.join(faltan)}")
            descartados += 1
            continue
        if it["categoria"].lower() not in CATEGORIAS_SOPORTADAS:
            print(f"⚠️ {it['modelo_corto']}: la categoría '{it['categoria']}' aún no tiene prompt en este script. Se deja pendiente.")
            descartados += 1
            continue
        if CATEGORIA_FILTRO and CATEGORIA_FILTRO != "todas" and it["categoria"].lower() != CATEGORIA_FILTRO:
            continue   # fuera del filtro de esta ejecución: se deja para otra
        pid = slug_producto(it)
        if pid in vistos:   # el mismo producto en el archivo y en la cola: solo se cuenta una vez
            continue
        vistos.add(pid)
        if producto_ya_publicado(pid, it, registro, titulos_wp):
            ya_publicados += 1
            actualizar_registro_desde_catalogo(pid, it)
            if origen == "cola":
                it["estado"] = "publicado"
            continue
        pendientes.append((origen, it, pid))
    if cola:
        guardar_json(RUTA_COLA, cola)

    # NUEVO: añade las etiquetas de los Top 10 a entradas ya publicadas que aún no las tienen
    sincronizadas = sincronizar_taxonomias()
    if sincronizadas:
        print(f"🏷️ Entradas ya publicadas etiquetadas en esta ejecución: {sincronizadas}")

    # Los productos que ya han fallado van al final, y los que han fallado demasiadas veces se apartan
    fallos = cargar_json(RUTA_FALLOS, {})
    apartados = [(o, i, p) for o, i, p in pendientes if fallos.get(p, 0) >= MAX_FALLOS_POR_PRODUCTO]
    for _, i, p in apartados:
        print(f"⛔ {i['marca']} {i['modelo_corto']} se aparta tras {fallos[p]} fallos seguidos (revisa sus datos o bórralo de la cola).")
    pendientes = sorted([x for x in pendientes if fallos.get(x[2], 0) < MAX_FALLOS_POR_PRODUCTO], key=lambda x: fallos.get(x[2], 0))

    print(f"🚀 Catálogo total: {len(candidatos)} | ya publicados: {ya_publicados} | pendientes: {len(pendientes)} | "
          f"descartados: {descartados} | límite por ejecución: {MAX_NUEVOS_POR_EJECUCION}")

    nuevos, fallidos, intentos = 0, [], 0
    for origen, item, pid in pendientes:
        if intentos >= MAX_NUEVOS_POR_EJECUCION:
            break
        if ia_agotada():
            print("🛑 No queda ningún proveedor de IA con cuota disponible. Se detiene la ejecución; mañana se continúa donde se dejó.")
            break
        intentos += 1
        print(f"\n[{intentos}/{min(MAX_NUEVOS_POR_EJECUCION, len(pendientes))}] Procesando: {item['marca']} {item['modelo_corto']}")
        aplicar_enlaces_a_item(item, pid, manual)
        resultado = procesar_y_publicar(item)
        if resultado == "publicado":
            nuevos += 1
            if pid in fallos:
                del fallos[pid]
                guardar_json(RUTA_FALLOS, fallos)
            if origen == "cola":
                item["estado"] = "publicado"
                item["publicado_el"] = datetime.now().strftime("%Y-%m-%d")
                guardar_json(RUTA_COLA, cola)
        elif resultado == "saltado":
            intentos -= 1   # no ha gastado IA: no cuenta para el límite
        else:
            fallidos.append(item["modelo_corto"])
            fallos[pid] = fallos.get(pid, 0) + 1
            guardar_json(RUTA_FALLOS, fallos)
        if intentos < MAX_NUEVOS_POR_EJECUCION:
            print(f"⏳ Esperando {PAUSA_ENTRE_PRODUCTOS} segundos para no saturar los límites por minuto...")
            time.sleep(PAUSA_ENTRE_PRODUCTOS)

    registro = cargar_json(RUTA_PUBLICADOS, {})
    sin_enlace_o_imagen = escribir_enlaces_manual(registro)
    quedan = max(0, len(pendientes) - nuevos - len(fallidos))

    print("\n==============================")
    print(f"📊 Nuevos publicados: {nuevos} | Fallidos: {len(fallidos)} | Pendientes para próximas ejecuciones: {quedan}")
    print(f"📝 Productos sin enlace corto o sin imagen (rellénalos en {RUTA_ENLACES}): {sin_enlace_o_imagen}")
    if fallidos:
        print("❌ Con problemas:")
        for f in fallidos:
            print(f"   - {f}")
        sys.exit(1)   # ANTES solo fallaba si no se publicaba NINGUNO: por eso GitHub salía en verde con fallos parciales


if __name__ == "__main__":
    main()
