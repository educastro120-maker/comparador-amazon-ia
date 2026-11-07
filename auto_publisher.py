"""
AUTO PUBLISHER v8
=================
Qué hace este programa, de principio a fin:

  1. Para cada producto del catálogo, le pide a Gemini (con Google Search) que investigue la ficha técnica.
  2. Gemini devuelve DOS cosas en la misma ficha:
       a) Texto bonito (resumen, specs, pros, contras)  -> para el post de WordPress
       b) "filtros": datos NORMALIZADOS (números y valores cerrados) -> para el futuro Analizador
  3. Publica (o ACTUALIZA si ya existe) el post en WordPress.
  4. Guarda los productos en un archivo JSON POR CATEGORÍA (data/products-smartwatch.json,
     data/products-smartphone.json...), que será la "base de datos" que leerá tu
     comparador/Analizador en JavaScript.

NOVEDADES respecto a la versión anterior:
  - Bloque "filtros" estructurado (batería en número, tipo de pantalla en lista cerrada...)
  - Exporta un JSON por categoría: data/products-<categoria>.json
  - Ya no crea posts duplicados (busca el post por su slug y lo actualiza)
  - Salta los productos que ya están en su JSON (ahorra cuota de Gemini)
  - Enlace de afiliado directo por ASIN (si lo indicas), si no, enlace de búsqueda
  - Aviso de afiliado en la tarjeta y precio mostrado como "orientativo"
"""

import os
import sys
import re
import json
import time
import html
import datetime
import unicodedata
import requests
import urllib.parse
from pydantic import BaseModel
from google import genai
from google.genai import types

# ==========================================
# 1. LECTURA SEGURA DE CREDENCIALES
# ==========================================
# Las claves NUNCA se escriben en el código: se leen de los "Secrets" de GitHub.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WP_URL = (os.environ.get("WP_URL") or "").rstrip("/")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")

faltan = [n for n, v in {
    "GEMINI_API_KEY": GEMINI_API_KEY, "WP_URL": WP_URL,
    "WP_USER": WP_USER, "WP_APP_PASSWORD": WP_APP_PASSWORD,
}.items() if not v]
if faltan:
    sys.exit(f"❌ Faltan variables de entorno: {', '.join(faltan)}")

AMAZON_TAG = "topcomparad00-21"   # tu ID de afiliado de Amazon

# ==========================================
# 2. AJUSTES (puedes tocar estos valores)
# ==========================================
MODELO = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

MAX_INTENTOS_API = 3          # reintentos por llamada a la API (errores 429/500...)
MAX_RONDAS = 2                # veces que se repite la investigación si la ficha sale pobre
MIN_ITEMS_SECCION = 3         # mínimo de líneas por sección de la ficha técnica
MIN_ITEMS_TOTAL = 24          # mínimo total de líneas de especificaciones
PAUSA_ENTRE_PRODUCTOS = 4     # segundos entre productos (evita límites de cuota)

# Precio: Gemini NO ve el precio real de Amazon, solo precios de la web.
# Por eso por defecto se usa el precio del catálogo y se muestra como "orientativo".
# Si lo pones a True, usa el de Gemini cuando sea coherente (±40%) con el del catálogo.
USAR_PRECIO_EN_TIEMPO_REAL = False

# True: NO publica fichas pobres (el workflow termina en rojo para que lo veas)
SALTAR_SI_FICHA_POBRE = True

# UNA_LLAMADA=1 -> 1 petición a Gemini por producto (ideal para la capa gratuita)
UNA_LLAMADA = os.environ.get("UNA_LLAMADA", "0") == "1"

# REGENERAR=1 -> vuelve a generar TODOS los productos aunque ya estén guardados en su JSON
# (por defecto los que ya están se saltan, para no gastar cuota de Gemini)
REGENERAR = os.environ.get("REGENERAR", "0") == "1"

# Carpeta del repositorio donde se guardan los JSON. Se crea un archivo por categoría:
#   categoría "smartwatch" -> data/products-smartwatch.json
#   categoría "smartphone" -> data/products-smartphone.json
CARPETA_DATOS = os.environ.get("CARPETA_DATOS", "data")

client = genai.Client(api_key=GEMINI_API_KEY)

# Secciones de la ficha técnica (clave JSON, título visible)
SECCIONES = [
    ("pantalla", "📺 Pantalla"),
    ("bateria", "🔋 Batería"),
    ("conectividad", "🌐 Conectividad"),
    ("sensores", "💓 Sensores"),
    ("deportes", "🏃‍♂️ Deportes"),
    ("construccion", "🛡️ Construcción"),
]

# Valores permitidos para los filtros de lista cerrada.
# Gemini debe elegir uno de estos; si dice otra cosa, el programa lo convierte en "Otro".
# Esto es lo que permite que "LTPO AMOLED" y "Super AMOLED" cuenten como "AMOLED".
PANELES = ["AMOLED", "OLED", "LCD/TFT", "MIP", "E-Ink", "Otro"]
SISTEMAS = ["Wear OS", "watchOS", "Garmin OS", "HarmonyOS", "Zepp OS", "Fitbit OS", "Propio", "Otro"]

# Campos de filtro que son SÍ/NO
FILTROS_BOOL = ["gps", "gps_doble_frecuencia", "nfc", "lte_esim", "ecg", "spo2", "temperatura", "altimetro"]

# Rangos razonables para los números. Si Gemini devuelve algo fuera de rango
# (p. ej. 4000 días de batería) lo descartamos: es un error seguro.
RANGOS = {
    "pantalla_pulgadas": (0.8, 3.0),
    "bateria_dias_uso_normal": (0.2, 60),
    "bateria_horas_gps": (1, 500),
    "agua_atm": (1, 30),
    "peso_g": (10, 200),
    "perfiles_deporte": (1, 600),
    "anio_lanzamiento": (2015, 2030),
}


# ==========================================
# 3. ESQUEMA DE SALIDA (lo que Gemini debe devolver)
# ==========================================
class Specs(BaseModel):
    pantalla: list[str]
    bateria: list[str]
    conectividad: list[str]
    sensores: list[str]
    deportes: list[str]
    construccion: list[str]


class Filtros(BaseModel):
    """
    Datos NORMALIZADOS para el Analizador.
    Regla: en los números, 0 significa "no confirmado". Los SÍ/NO son true solo si está confirmado.
    """
    panel: str                       # uno de PANELES
    pantalla_pulgadas: float         # p. ej. 1.4
    bateria_dias_uso_normal: float   # días en uso normal (sin GPS continuo)
    bateria_horas_gps: float         # horas con GPS activo
    gps: bool
    gps_doble_frecuencia: bool
    nfc: bool                        # pagos contactless
    lte_esim: bool
    ecg: bool
    spo2: bool
    temperatura: bool
    altimetro: bool
    agua_atm: int                    # resistencia al agua en ATM (5 ATM = 50 m)
    peso_g: float
    sistema: str                     # uno de SISTEMAS
    perfiles_deporte: int
    anio_lanzamiento: int


class Ficha(BaseModel):
    badge: str
    resumen_ejecutivo: str
    specs: Specs
    filtros: Filtros
    pros: list[str]
    contras: list[str]
    puntuacion: float
    precio_actual_eur: str  # "" si no se ha encontrado


# ==========================================
# 4. CATÁLOGO DE PRODUCTOS
# ==========================================
# Campos nuevos:
#   "categoria": smartwatch, smartphone, monitor... (para el selector del Analizador)
#   "link_afiliado": el enlace corto que te da Amazon con SiteStripe (barra superior de Amazon
#           cuando estás logueado como afiliado -> "Obtener enlace" -> "Enlace corto").
#           Tiene el formato https://link.amazon/XXXXXXX (o https://amzn.to/XXXXXXX).
#           Amazon lo genera al azar, NO se puede calcular a partir del ASIN, por eso hay que
#           copiarlo a mano UNA vez por producto. Este es el enlace PREFERIDO.
#   "asin": (opcional, solo como plan B si no pones link_afiliado) código de 10 caracteres
#           del producto de Amazon (empieza por B0...). Se ve en la URL: amazon.es/dp/B0XXXXXXXX
#   "imagen": URL de la imagen. Si la dejas vacía "", el post se publica sin imagen.
#
# OJO: la imagen que tenías para el Versa 4 era de un Fitbit Charge 5 (otro modelo),
# por eso la he dejado vacía. Pon aquí una imagen correcta del Versa 4.
productos_catalogo = [
    {
        "categoria": "smartwatch",
        "marca": "Fitbit",
        "modelo_corto": "Versa 4",
        "busqueda": "Fitbit Versa 4",
        "link_afiliado": "https://link.amazon/B08PeAFV6",   # <- pega aquí tu enlace corto, p. ej. "https://link.amazon/XXXXXXX"
        "asin": "",
        "titulo": "Fitbit Versa 4 - Reloj Inteligente Delgado de Salud y Forma Física, GPS Integrado, Perfil Diálogo de Sueño, 6+ Días Batería",
        "especificaciones": "Formato ergonómico de bordes redondeados diseñado para máxima comodidad nocturna, GPS integrado, análisis continuo de estrés con sensor EDA, minutos en zona activa, integración con Google Maps y más de 6 días de batería.",
        "precio": "179.95€",
        "imagen": "",
    },
]


# ==========================================
# 5. UTILIDADES
# ==========================================
def slugify(texto):
    """'Fitbit Versa 4' -> 'fitbit-versa-4' (sin tildes ni símbolos). Sirve como identificador único."""
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def id_producto(producto):
    """Identificador único del producto, p. ej. 'fitbit-versa-4'. Se usa en products.json y en el slug."""
    return slugify(f"{producto['marca']} {producto['modelo_corto']}")


def render_item(texto):
    """'Etiqueta: valor' -> <strong>Etiqueta:</strong> valor (con HTML escapado)."""
    texto = str(texto).strip()
    if ": " in texto:
        etiqueta, valor = texto.split(": ", 1)
        if len(etiqueta) <= 45:
            return f"<strong>{html.escape(etiqueta)}:</strong> {html.escape(valor)}"
    return html.escape(texto)


def a_numero(texto):
    """Convierte '1.099,99€' / '799.00 €' / '799' en float. None si no se puede."""
    if not texto:
        return None
    m = re.search(r"\d[\d.,]*", str(texto))
    if not m:
        return None
    n = m.group(0).rstrip(".,")
    if "," in n and "." in n:
        if n.rfind(",") > n.rfind("."):
            n = n.replace(".", "").replace(",", ".")
        else:
            n = n.replace(",", "")
    elif "," in n:
        n = n.replace(",", ".")
    elif n.count(".") > 1 or (n.count(".") == 1 and len(n.split(".")[1]) == 3):
        n = n.replace(".", "")
    try:
        return float(n)
    except ValueError:
        return None


def resolver_precio(producto, precio_ia):
    """Decide qué precio mostrar: el del catálogo, o el de Gemini si está activado y es coherente."""
    base = producto["precio"]
    if not USAR_PRECIO_EN_TIEMPO_REAL:
        return base
    n_base, n_ia = a_numero(base), a_numero(precio_ia)
    if n_base and n_ia and 0.6 * n_base <= n_ia <= 1.4 * n_base:
        return f"{n_ia:.2f}€"
    return base


# Un ASIN válido tiene exactamente 10 caracteres (letras mayúsculas y números), p. ej. B0BDKXXXXX
RE_ASIN = re.compile(r"^[A-Z0-9]{10}$")
# Prefijos de los enlaces cortos oficiales de Amazon Afiliados
PREFIJOS_LINK_CORTO = ("https://link.amazon/", "https://amzn.to/", "https://amzn.eu/")


def construir_link_afiliado(producto):
    """
    Elige el enlace de afiliado, por orden de preferencia:
      1) "link_afiliado": tu enlace corto de SiteStripe (https://link.amazon/...). Se usa TAL CUAL:
         ya lleva tu ID de afiliado dentro, así que NO se le añade ningún "?tag=".
      2) "asin": enlace directo amazon.es/dp/ASIN?tag=... (solo si el ASIN tiene formato válido).
      3) Búsqueda en Amazon con tu tag (siempre funciona, pero convierte peor).
    """
    link = (producto.get("link_afiliado") or "").strip()
    if link:
        if link.startswith(PREFIJOS_LINK_CORTO):
            return link
        print(f"   ⚠️ link_afiliado '{link}' no parece un enlace corto de Amazon "
              f"(debe empezar por {' o '.join(PREFIJOS_LINK_CORTO)}). Se ignora.")

    asin = (producto.get("asin") or "").strip().upper()
    if asin:
        if RE_ASIN.match(asin):
            print("   ℹ️ Sin link_afiliado: se usa el enlace /dp/ASIN. Mejor pon tu enlace corto de SiteStripe.")
            return f"https://www.amazon.es/dp/{asin}?tag={AMAZON_TAG}"
        print(f"   ⚠️ ASIN '{asin}' no válido (debe tener 10 caracteres). Se ignora.")

    print("   ℹ️ Sin link_afiliado ni ASIN válido: se usa enlace de búsqueda (convierte peor).")
    q = urllib.parse.quote_plus(producto["busqueda"])
    return f"https://www.amazon.es/s?k={q}&tag={AMAZON_TAG}"


class QuotaAgotada(Exception):
    """Cuota diaria de la API agotada: reintentar no sirve de nada."""


def llamar_gemini(contents, config, etiqueta):
    """Llama a la API con reintentos. Si la cuota DIARIA se agota, aborta al instante."""
    for intento in range(1, MAX_INTENTOS_API + 1):
        try:
            r = client.models.generate_content(model=MODELO, contents=contents, config=config)
            if getattr(r, "text", None):
                return r
            print(f"   ⚠️ [{etiqueta}] respuesta vacía (intento {intento}/{MAX_INTENTOS_API})")
        except Exception as e:
            txt = str(e)
            if "429" in txt or "RESOURCE_EXHAUSTED" in txt:
                if "PerDay" in txt or "per day" in txt.lower():
                    raise QuotaAgotada(f"Cuota diaria agotada para el modelo {MODELO}.")
                m = re.search(r"retryDelay\D{0,6}(\d+)", txt)
                espera = min(int(m.group(1)) + 2, 70) if m else 30
                print(f"   ⏳ [{etiqueta}] límite por minuto; esperando {espera}s...")
                time.sleep(espera)
                continue
            print(f"   ⚠️ [{etiqueta}] error de API (intento {intento}/{MAX_INTENTOS_API}): {txt[:300]}")
        if intento < MAX_INTENTOS_API:
            time.sleep(6 * intento)
    return None


def fuentes_usadas(respuesta):
    """Devuelve las webs que Google Search ha usado (para el log y para guardarlas en products.json)."""
    try:
        chunks = respuesta.candidates[0].grounding_metadata.grounding_chunks or []
        return sorted({c.web.title for c in chunks if c.web and c.web.title})
    except Exception:
        return []


# ==========================================
# 6. FASE 1: INVESTIGACIÓN EN TIEMPO REAL (Google Search, texto libre)
# ==========================================
def investigar(producto):
    """Primera llamada: Gemini busca en internet y devuelve un informe en texto plano."""
    prompt = f"""
Eres un ingeniero de hardware y analista de wearables. Usa Google Search AHORA para localizar
la ficha técnica COMPLETA y ACTUAL del producto: "{producto['busqueda']}" ({producto['marca']}).

Prioriza fuentes en este orden: 1) web oficial del fabricante, 2) pruebas de laboratorio de
medios especializados (DC Rainmaker, Notebookcheck, GSMArena, Wareable, Xataka, etc.),
3) tiendas fiables. Haz varias búsquedas si hace falta (por ejemplo: "specs", "autonomía GPS",
"sensores", "dimensiones peso", "precio España").

Datos de referencia del catálogo (verifícalos y AMPLÍALOS, no te limites a ellos):
{producto['especificaciones']}

Devuelve un informe en texto plano con TODAS estas secciones y datos EXACTOS (cifras, unidades,
nombres de tecnologías, versiones, certificaciones):

PANTALLA: tipo de panel, tamaño en pulgadas, resolución, densidad (ppp), brillo máximo en nits,
  frecuencia de refresco, Always-On, tipo de cristal/protección, táctil/botones.
BATERÍA: capacidad (mAh) si existe, autonomía en modo reloj, autonomía con GPS (distintos modos),
  autonomía en modo ahorro/expedición, carga solar si aplica, tipo de carga, tiempo de carga.
CONECTIVIDAD: Bluetooth (versión), Wi-Fi, NFC/pagos, eSIM/LTE, GNSS (sistemas y doble frecuencia),
  satélite, ANT+, almacenamiento/música, altavoz/micrófono, mapas, llamadas.
SENSORES: frecuencia cardíaca óptica (generación), SpO2, ECG, temperatura, altímetro, barómetro,
  brújula, giroscopio, acelerómetro, profundidad, luz ambiental, métricas de salud y sueño.
DEPORTES: nº de perfiles/modos, buceo (profundidad y certificación), golf, running, ciclismo,
  natación, trail, esquí, métricas avanzadas de entrenamiento, navegación/rutas, alertas de seguridad.
CONSTRUCCIÓN: material de caja, bisel, fondo, correa, resistencia al agua (ATM/IP), certificaciones
  militares, dimensiones (mm), peso (g), botones/corona, colores o tallas, sistema operativo.
PRECIO: precio actual aproximado en euros en España y año de lanzamiento.
PUNTOS FUERTES Y DÉBILES REALES: según las pruebas y reseñas encontradas.

REGLAS: no inventes. Si un dato no aparece en las fuentes, escribe "NO CONFIRMADO" en lugar de
suponerlo. No mezcles datos de otras generaciones del mismo modelo (comprueba que es exactamente
"{producto['modelo_corto']}").
"""
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.1,   # temperatura baja = respuestas más fieles a las fuentes
    )
    r = llamar_gemini(prompt, config, "investigación")
    if not r:
        return None, []
    fuentes = fuentes_usadas(r)
    if fuentes:
        print(f"   🔎 Fuentes consultadas: {', '.join(fuentes[:8])}")
    else:
        print("   ⚠️ Gemini no devolvió fuentes de búsqueda (datos posiblemente de memoria)")
    return r.text, fuentes


# ==========================================
# 7. FASE 2: ESTRUCTURADO EN JSON (esquema forzado)
# ==========================================
def extraer_json(texto):
    """Extrae el primer objeto JSON de un texto (por si viene con ``` o explicaciones)."""
    texto = texto.strip()
    a, b = texto.find("{"), texto.rfind("}")
    if a == -1 or b == -1:
        raise json.JSONDecodeError("sin JSON", texto, 0)
    return json.loads(texto[a:b + 1])


# Solo se usa en el modo UNA_LLAMADA (Gemini no admite JSON forzado junto a Google Search)
ESQUEMA_TEXTO = """Responde ÚNICAMENTE con un objeto JSON válido (sin ``` ni texto extra) con estas claves:
{"badge": str, "resumen_ejecutivo": str,
 "specs": {"pantalla": [str], "bateria": [str], "conectividad": [str], "sensores": [str], "deportes": [str], "construccion": [str]},
 "filtros": {"panel": str, "pantalla_pulgadas": number, "bateria_dias_uso_normal": number, "bateria_horas_gps": number,
   "gps": bool, "gps_doble_frecuencia": bool, "nfc": bool, "lte_esim": bool, "ecg": bool, "spo2": bool,
   "temperatura": bool, "altimetro": bool, "agua_atm": int, "peso_g": number, "sistema": str,
   "perfiles_deporte": int, "anio_lanzamiento": int},
 "pros": [str], "contras": [str], "puntuacion": number, "precio_actual_eur": str}"""


def estructurar(producto, investigacion=None):
    """Segunda llamada: convierte el informe en la ficha estructurada (JSON)."""
    if investigacion:
        bloque_fuente = f"""=== INFORME DE INVESTIGACIÓN (fuente de verdad) ===
{investigacion}
=== FIN DEL INFORME ==="""
    else:
        bloque_fuente = f"""Usa Google Search AHORA para obtener la ficha técnica completa y ACTUAL de "{producto['busqueda']}"
(prioriza la web del fabricante y pruebas de laboratorio de medios especializados; comprueba que es
exactamente el modelo "{producto['modelo_corto']}" y no otra generación). Haz varias búsquedas si hace falta.
Si un dato no aparece en las fuentes, NO lo incluyas."""

    prompt = f"""
Eres redactor técnico de una web de comparativas de smartwatches en España.
Con el INFORME DE INVESTIGACIÓN de abajo, redacta la ficha del producto en español.

PRODUCTO: {producto['titulo']}
MARCA: {producto['marca']}  |  MODELO: {producto['modelo_corto']}

{bloque_fuente}

=== DATOS BASE DEL CATÁLOGO (complemento) ===
{producto['especificaciones']}
=== FIN ===

INSTRUCCIONES:

1. "badge": etiqueta comercial corta en MAYÚSCULAS (p. ej. "MEJOR RELOJ DE BUCEO", "REFERENCIA OUTDOOR").

2. "resumen_ejecutivo": 90-140 palabras, un único párrafo. Debe EMPEZAR con el nombre completo del
   producto ("{producto['titulo']} representa..." / "... se posiciona como...") y hablar de
   rendimiento, materiales, sensores/salud, ecosistema/energía y a quién va dirigido.
   Sin listas ni cifras repetidas de la ficha.

3. "specs": 6 secciones (pantalla, bateria, conectividad, sensores, deportes, construccion).
   - Cada sección tiene entre 5 y 8 líneas.
   - FORMATO OBLIGATORIO de cada línea: "Etiqueta: valor concreto con cifras y unidades".
   - Etiquetas cortas (1-4 palabras) y distintas dentro de la sección.
   - Datos concretos, exactos y con explicación breve útil entre paréntesis cuando aporte.
   - Si un dato figura como "NO CONFIRMADO" en el informe, NO lo incluyas (no rellenes con vaguedades).
   - PROHIBIDO poner el precio, la marca o el nombre del modelo como línea de especificación.
   - Cada dato va en su sección correcta (el precio no va nunca en batería).

   Ejemplo del nivel de detalle y formato esperado (de otro modelo, solo como guía de estilo):
   pantalla:
     "Panel: LTPO 2.0 AMOLED circular de 1,5 pulgadas."
     "Resolución: 466 × 466 píxeles (310 ppp)."
     "Brillo Máximo: 3.500 nits (ideal bajo el sol directo)."
     "Protección: Cristal de zafiro sintético de alta dureza."
   bateria:
     "Autonomía: 11-14 días en modo ahorro. Hasta 40 horas continuas con GPS."
     "Carga: Inalámbrica Qi; de 0 a 100% en aprox. 60-90 minutos."

4. "pros": 5 o 6 puntos. Formato "Título corto: explicación con datos reales (1-2 frases)".

5. "contras": 4 puntos, honestos y concretos (peso, ecosistema, autonomía real, precio, etc.),
   mismo formato "Título corto: explicación".

6. "puntuacion": número entre 7.5 y 9.8 con un decimal, coherente con los pros/contras y el precio.

7. "precio_actual_eur": precio actual en España en euros según el informe (ej. "799.00€"),
   o "" si no está confirmado.

8. "filtros": datos NORMALIZADOS para un buscador con filtros. Son solo valores, sin texto.
   REGLA GENERAL: no inventes. Números desconocidos = 0. Los campos true/false son true SOLO si
   el informe lo confirma; si no hay confirmación, false.
   - "panel": EXACTAMENTE uno de: {", ".join(PANELES)}.
       (LTPO AMOLED, Super AMOLED, etc. -> "AMOLED"; LCD, TFT, transflectivo -> "LCD/TFT";
        pantalla de memoria en píxel -> "MIP")
   - "pantalla_pulgadas": tamaño en pulgadas, p. ej. 1.4
   - "bateria_dias_uso_normal": días de autonomía en uso normal como reloj inteligente (sin GPS
       continuo). Usa el dato más representativo, no el del modo ahorro extremo. Si solo hay horas,
       convierte (24 h = 1 día).
   - "bateria_horas_gps": horas de autonomía con GPS activo en el modo de GPS estándar.
   - "gps", "gps_doble_frecuencia" (L1+L5), "nfc" (pagos contactless), "lte_esim",
     "ecg", "spo2", "temperatura" (sensor de temperatura de piel/cuerpo), "altimetro": true/false.
   - "agua_atm": resistencia al agua en ATM (5 ATM = 50 m). Si solo hay IP68, pon 1.
   - "peso_g": peso del reloj sin correa si se indica, si no, con correa.
   - "sistema": EXACTAMENTE uno de: {", ".join(SISTEMAS)}.
   - "perfiles_deporte": número de modos deportivos (0 si no se confirma).
   - "anio_lanzamiento": año de lanzamiento (0 si no se confirma).

Todo en español de España. No inventes ningún dato que no esté en las fuentes o en el catálogo.
"""
    if investigacion:
        # Modo 2 llamadas: JSON forzado con el esquema "Ficha" (más fiable)
        config = types.GenerateContentConfig(
            temperature=0.3,
            response_mime_type="application/json",
            response_schema=Ficha,
        )
    else:
        # Modo 1 llamada: búsqueda + JSON en texto (Gemini no admite JSON forzado junto a search)
        prompt += "\n" + ESQUEMA_TEXTO
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.2,
        )
    r = llamar_gemini(prompt, config, "estructurado" if investigacion else "búsqueda+ficha")
    if not r:
        return None, []
    fuentes = []
    if not investigacion:
        fuentes = fuentes_usadas(r)
        print(f"   🔎 Fuentes consultadas: {', '.join(fuentes[:8])}" if fuentes
              else "   ⚠️ Sin fuentes de búsqueda (datos posiblemente de memoria)")
    try:
        return extraer_json(r.text), fuentes
    except json.JSONDecodeError as err:
        print(f"   ⚠️ JSON inválido en fase de estructurado: {err}")
        return None, []


# ==========================================
# 8. LIMPIEZA Y VALIDACIÓN DE CALIDAD
# ==========================================
RE_BASURA = re.compile(r"^\s*(precio|price|coste|fabricante|marca|modelo)\b", re.I)
RE_VAGO = re.compile(r"no confirmado|no disponible|n/a|optimizad[ao] para", re.I)


def elegir_de_lista(valor, permitidos):
    """Devuelve el valor si está en la lista (sin distinguir mayúsculas); si no, 'Otro'."""
    v = str(valor or "").strip().lower()
    for p in permitidos:
        if p.lower() == v:
            return p
    return "Otro"


def sanear_filtros(f):
    """
    Deja los filtros listos para el Analizador:
      - números: si es 0, no numérico o está fuera de rango -> None (= "dato desconocido")
      - SÍ/NO: siempre true/false
      - panel y sistema: siempre un valor de la lista cerrada
    En el Analizador, un producto con None simplemente no aparecerá al filtrar por ese campo
    (mejor eso que mostrarlo con un dato inventado).
    """
    f = f or {}
    limpio = {
        "panel": elegir_de_lista(f.get("panel"), PANELES),
        "sistema": elegir_de_lista(f.get("sistema"), SISTEMAS),
    }
    for campo in FILTROS_BOOL:
        limpio[campo] = bool(f.get(campo, False))
    for campo, (minimo, maximo) in RANGOS.items():
        try:
            n = float(f.get(campo) or 0)
        except (TypeError, ValueError):
            n = 0
        if n and minimo <= n <= maximo:
            # los campos enteros se guardan como int; los demás con 1 decimal
            limpio[campo] = int(n) if campo in ("agua_atm", "perfiles_deporte", "anio_lanzamiento") else round(n, 1)
        else:
            limpio[campo] = None
    return limpio


def limpiar(datos):
    """Quita líneas basura (precio/marca como spec, datos vagos) y normaliza los filtros."""
    specs = datos.get("specs", {})
    for clave, _ in SECCIONES:
        limpias = []
        for it in specs.get(clave, []):
            it = str(it).strip()
            if it and not RE_BASURA.match(it) and not RE_VAGO.search(it):
                limpias.append(it)
        specs[clave] = limpias
    datos["specs"] = specs
    datos["pros"] = [str(p).strip() for p in datos.get("pros", []) if str(p).strip()]
    datos["contras"] = [str(c).strip() for c in datos.get("contras", []) if str(c).strip()]
    datos["filtros"] = sanear_filtros(datos.get("filtros"))
    return datos


def validar(datos):
    """Comprueba que la ficha tiene calidad suficiente. Devuelve (ok, motivo)."""
    specs = datos["specs"]
    total = 0
    for clave, titulo in SECCIONES:
        n = len(specs.get(clave, []))
        total += n
        if n < MIN_ITEMS_SECCION:
            return False, f"sección '{titulo}' con solo {n} líneas (mínimo {MIN_ITEMS_SECCION})"
    if total < MIN_ITEMS_TOTAL:
        return False, f"solo {total} líneas de especificaciones (mínimo {MIN_ITEMS_TOTAL})"
    if len(datos["pros"]) < 4 or len(datos["contras"]) < 3:
        return False, "pros/contras insuficientes"
    if len(datos.get("resumen_ejecutivo", "").split()) < 50:
        return False, "resumen demasiado corto"
    # Los filtros más importantes tienen que existir, si no el Analizador no sirve de nada
    f = datos["filtros"]
    if f["bateria_dias_uso_normal"] is None and f["bateria_horas_gps"] is None:
        return False, "filtros sin ningún dato de batería"
    if f["panel"] == "Otro" and f["pantalla_pulgadas"] is None:
        return False, "filtros sin datos de pantalla"
    return True, ""


def obtener_ficha(producto):
    """Investiga + estructura + valida, repitiendo hasta MAX_RONDAS veces. Devuelve (datos, fuentes)."""
    mejor = None
    for ronda in range(1, MAX_RONDAS + 1):
        print(f"   🔁 Ronda {ronda}/{MAX_RONDAS}")
        if UNA_LLAMADA:
            datos, fuentes = estructurar(producto)
        else:
            investigacion, fuentes_inv = investigar(producto)
            if not investigacion:
                continue
            datos, _ = estructurar(producto, investigacion)
            fuentes = fuentes_inv
        if not datos:
            continue
        datos = limpiar(datos)
        ok, motivo = validar(datos)
        if ok:
            return datos, fuentes
        print(f"   ⚠️ Ficha pobre: {motivo}")
        total = sum(len(datos["specs"][c]) for c, _ in SECCIONES)
        if mejor is None or total > mejor[0]:
            mejor = (total, datos, fuentes)
    if mejor and not SALTAR_SI_FICHA_POBRE:
        print("   ⚠️ Se usa la mejor ficha obtenida aunque sea incompleta.")
        return mejor[1], mejor[2]
    return None, []


# ==========================================
# 9. JSON POR CATEGORÍA: LA "BASE DE DATOS" PARA TU COMPARADOR / ANALIZADOR
# ==========================================
def ruta_json(categoria):
    """'smartwatch' -> data/products-smartwatch.json (un archivo por categoría)."""
    return os.path.join(CARPETA_DATOS, f"products-{slugify(categoria)}.json")


def cargar_productos_json(categoria):
    """Lee el JSON de esa categoría si existe; si no, devuelve una lista vacía."""
    ruta = ruta_json(categoria)
    if not os.path.exists(ruta):
        return []
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as err:
        print(f"⚠️ No se pudo leer {ruta} ({err}). Se empieza con una lista vacía.")
        return []


def guardar_productos_json(categoria, lista):
    """Guarda la lista completa de esa categoría (crea la carpeta si no existe)."""
    ruta = ruta_json(categoria)
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    lista = sorted(lista, key=lambda p: (p.get("marca", ""), p.get("modelo", "")))
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(lista, fh, ensure_ascii=False, indent=2)


def actualizar_json(entrada):
    """Añade el producto al JSON de su categoría, o reemplaza el que ya existe con el mismo id."""
    categoria = entrada["categoria"]
    lista = cargar_productos_json(categoria)
    lista = [p for p in lista if p.get("id") != entrada["id"]]
    lista.append(entrada)
    guardar_productos_json(categoria, lista)


# ==========================================
# 10. GENERACIÓN DEL HTML DEL POST
# ==========================================
def construir_html(producto, datos, precio, affiliate_link):
    s = datos["specs"]
    e = html.escape

    # Tabla de especificaciones: una fila por sección
    filas = []
    for clave, titulo in SECCIONES:
        lis = "".join(f"<li style='margin-bottom: 4px;'>{render_item(it)}</li>" for it in s[clave])
        filas.append(f"""
          <tr style="border: none; border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: bold; width: 30%; vertical-align: top; border: none; background-color: #f1f5f9;">{titulo}</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">{lis}</ul>
            </td>
          </tr>""")
    filas_html = "".join(filas)

    pros = "".join(f'<li style="margin-bottom: 6px;">{render_item(p)}</li>' for p in datos["pros"])
    contras = "".join(f'<li style="margin-bottom: 6px;">{render_item(c)}</li>' for c in datos["contras"])

    try:
        puntuacion = f"{float(datos['puntuacion']):.1f}"
    except (TypeError, ValueError):
        puntuacion = "9.0"

    # La imagen solo se pinta si el producto tiene una (evita imágenes rotas o equivocadas)
    imagen_html = ""
    if producto.get("imagen"):
        imagen_html = f"""
      <div style="text-align: center; margin-bottom: 20px;">
        <img src="{e(producto['imagen'])}" alt="{e(producto['titulo'])}" loading="lazy" style="max-height: 280px; width: auto; object-fit: contain; border-radius: 8px;" />
      </div>"""

    hoy = datetime.date.today().strftime("%d/%m/%Y")

    return f"""
    <div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 24px; background-color: #ffffff; max-width: 750px; margin: 20px auto; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
      {imagen_html}
      <div style="background-color: #ff9900; color: #fff; font-weight: bold; display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 0.85em; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px;">
        🔥 {e(datos['badge'])}
      </div>

      <h2 style="margin-top: 0; color: #111; font-size: 1.6em; line-height: 1.3;">{e(producto['titulo'])}</h2>

      <p style="font-size: 1.05em; color: #333; line-height: 1.7; text-align: justify;">
        {e(datos['resumen_ejecutivo'])}
      </p>

      <!-- Ficha Técnica Detallada -->
      <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin: 20px 0;">
        <h3 style="color: #0f172a; margin-top: 0; font-size: 1.1em; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; margin-bottom: 12px;">⚙️ Ficha Técnica Detallada</h3>
        <table style="width: 100%; border-collapse: collapse; border: none; font-size: 0.95em; color: #334155;">
          {filas_html}
        </table>
      </div>

      <div style="display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 250px; background-color: #f0fdf4; padding: 18px; border-radius: 8px; border-left: 4px solid #22c55e;">
          <h4 style="color: #15803d; margin-top: 0; font-size: 1.1em;">✅ Lo Mejor (Pros)</h4>
          <ul style="padding-left: 18px; color: #166534; margin-bottom: 0; line-height: 1.5;">{pros}</ul>
        </div>

        <div style="flex: 1; min-width: 250px; background-color: #fef2f2; padding: 18px; border-radius: 8px; border-left: 4px solid #ef4444;">
          <h4 style="color: #b91c1c; margin-top: 0; font-size: 1.1em;">❌ A mejorar (Contras)</h4>
          <ul style="padding-left: 18px; color: #991b1b; margin-bottom: 0; line-height: 1.5;">{contras}</ul>
        </div>
      </div>

      <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #f0f0f0;">
        <p style="font-size: 1.3em; font-weight: bold; color: #111; margin-bottom: 6px;">
          Precio orientativo: <span style="color: #b12704;">{e(precio)}</span> | Puntuación: ⭐ <strong>{puntuacion}/10</strong>
        </p>
        <p style="font-size: 0.8em; color: #64748b; margin: 0 0 15px 0;">
          Precio de referencia a fecha {hoy}; puede variar. Consulta el precio actual en Amazon.
        </p>
        <a href="{e(affiliate_link)}" target="_blank" rel="sponsored nofollow noopener" style="background-color: #ffa41c; color: #111; text-decoration: none; font-size: 1.2em; font-weight: bold; padding: 16px 32px; border-radius: 8px; border: 1px solid #ff8f00; display: inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
          Ver precio actualizado en Amazon 🛒
        </a>
        <p style="font-size: 0.75em; color: #94a3b8; margin: 14px 0 0 0;">
          Enlace de afiliado: como afiliado de Amazon obtengo ingresos por las compras adscritas, sin coste extra para ti.
        </p>
      </div>
    </div>
    """


# ==========================================
# 11. WORDPRESS: BUSCAR, CREAR Y ACTUALIZAR POSTS
# ==========================================
def buscar_post_por_slug(slug):
    """
    Pregunta a WordPress si ya existe un post con ese slug (la parte final de la URL).
    Devuelve el ID del post si existe, o None. Así evitamos crear duplicados.
    """
    try:
        res = requests.get(
            f"{WP_URL}/wp-json/wp/v2/posts",
            params={"slug": slug, "status": "publish,draft,pending,private"},
            auth=(WP_USER, WP_APP_PASSWORD),
            timeout=30,
        )
        if res.status_code == 200 and res.json():
            return res.json()[0]["id"]
    except (requests.RequestException, ValueError, KeyError, IndexError) as err:
        print(f"   ⚠️ No se pudo comprobar si el post ya existe: {err}")
    return None


def procesar_y_publicar(producto):
    """
    Devuelve: "publicado" | "saltado" | "error"
    """
    pid = id_producto(producto)
    print(f"\n🌐 Producto: {producto['titulo']}  [{pid}]")

    # COMPROBACIÓN AUTOMÁTICA DE DUPLICADOS:
    # miramos si el id ya existe en el JSON de su categoría. Si existe, no gastamos cuota de Gemini
    # (salvo que REGENERAR=1). No tienes que indicarlo tú: el script lo decide solo.
    if not REGENERAR and any(p.get("id") == pid for p in cargar_productos_json(producto["categoria"])):
        print(f"   ⏭️ Ya está en {ruta_json(producto['categoria'])}. Se salta (usa REGENERAR=1 para forzar).")
        return "saltado"

    affiliate_link = construir_link_afiliado(producto)

    # --- Paso 1: generar la ficha con Gemini ---
    datos, fuentes = obtener_ficha(producto)
    if not datos:
        print(f"❌ No se ha podido generar una ficha completa para {producto['titulo']}. NO se publica.")
        return "error"

    s = datos["specs"]
    total = sum(len(s[c]) for c, _ in SECCIONES)
    print(f"   ✅ Ficha completa: {total} líneas de especificaciones")

    precio = resolver_precio(producto, datos.get("precio_actual_eur", ""))
    html_content = construir_html(producto, datos, precio, affiliate_link)

    # --- Paso 2: publicar o actualizar en WordPress ---
    slug = f"analisis-{pid}"
    payload = {
        "title": f"Análisis y Opinión: {producto['titulo']}",
        "content": html_content,
        "status": "publish",
        # Estos campos "meta" se mantienen EXACTAMENTE como antes para no romper tu comparador actual.
        # (WordPress solo los guarda si están registrados con register_post_meta; ya lo tenías así.)
        "meta": {
            "top_marca": producto["marca"],
            "top_modelo": producto["modelo_corto"],
            "top_busqueda": producto["busqueda"],
            "spec_pantalla": str(s.get("pantalla", [])),
            "spec_bateria": str(s.get("bateria", [])),
            "spec_conectiv": str(s.get("conectividad", [])),
            "spec_sensores": str(s.get("sensores", [])),
            "spec_deportes": str(s.get("deportes", [])),
            "spec_cuerpo": str(s.get("construccion", [])),
        },
    }

    post_id = buscar_post_por_slug(slug)
    try:
        if post_id:
            # El post ya existe -> lo ACTUALIZAMOS (nada de duplicados)
            res = requests.post(f"{WP_URL}/wp-json/wp/v2/posts/{post_id}", json=payload,
                                auth=(WP_USER, WP_APP_PASSWORD), timeout=60)
            ok_codigo, accion = 200, "actualizada"
        else:
            # No existe -> lo CREAMOS con ese slug
            payload["slug"] = slug
            res = requests.post(f"{WP_URL}/wp-json/wp/v2/posts", json=payload,
                                auth=(WP_USER, WP_APP_PASSWORD), timeout=60)
            ok_codigo, accion = 201, "creada"
    except requests.RequestException as err:
        print(f"❌ Error de conexión con WordPress: {err}")
        return "error"

    if res.status_code != ok_codigo:
        print(f"❌ Error WordPress ({res.status_code}): {res.text[:300]}")
        return "error"

    url_post = res.json().get("link", "")
    print(f"🎉 Publicación {accion}: {producto['titulo']}")

    # --- Paso 3: guardar el producto en el JSON de su categoría ---
    entrada = {
        "id": pid,
        "categoria": producto["categoria"],
        "marca": producto["marca"],
        "modelo": producto["modelo_corto"],
        "titulo": producto["titulo"],
        "imagen": producto.get("imagen", ""),
        "url_post": url_post,
        "link_afiliado": affiliate_link,
        "precio_ref_eur": a_numero(precio),       # número, para poder ordenar/filtrar por precio
        "puntuacion": float(f"{float(datos.get('puntuacion', 0) or 0):.1f}"),
        "badge": datos["badge"],
        "filtros": datos["filtros"],              # <- lo que usará el Analizador
        "specs": datos["specs"],                  # <- por si el comparador quiere el texto de cada característica
        "fuentes": fuentes[:8],                   # <- para que puedas auditar de dónde salen los datos
        "actualizado": datetime.date.today().isoformat(),
    }
    actualizar_json(entrada)
    print(f"   💾 Guardado en {ruta_json(producto['categoria'])}")
    return "publicado"


# ==========================================
# 12. PROGRAMA PRINCIPAL
# ==========================================
if __name__ == "__main__":
    resultados = {"publicado": 0, "saltado": 0}
    fallidos = []

    for i, item in enumerate(productos_catalogo):
        try:
            estado = procesar_y_publicar(item)
            if estado == "error":
                fallidos.append(item["titulo"])
            else:
                resultados[estado] += 1
        except QuotaAgotada as q:
            print(f"\n🛑 {q} Se detiene la ejecución para no gastar más peticiones.")
            print("   Soluciones: esperar al reinicio diario, activar facturación en Google AI Studio,")
            print("   usar otro modelo (GEMINI_MODEL) o activar UNA_LLAMADA=1.")
            fallidos.extend(p["titulo"] for p in productos_catalogo[i:])
            break
        # Pausa entre productos (no hace falta si el producto se ha saltado)
        if i < len(productos_catalogo) - 1:
            time.sleep(PAUSA_ENTRE_PRODUCTOS)

    print("\n==============================")
    print(f"Publicados/actualizados: {resultados['publicado']} | Saltados (ya existían): {resultados['saltado']} | Con problemas: {len(fallidos)}")
    if fallidos:
        print("Con problemas:")
        for t in fallidos:
            print(f"  - {t}")
        sys.exit(1)  # marca el workflow de GitHub en rojo para que lo veas
