import os
import sys
import re
import json
import time
import html
import requests
import urllib.parse
from pydantic import BaseModel
from google import genai
from google.genai import types

# ==========================================
# 1. LECTURA SEGURA DE CREDENCIALES
# ==========================================
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

AMAZON_TAG = "topcomparad00-21"

# ==========================================
# 2. AJUSTES DE CALIDAD
# ==========================================
# Modelo con Google Search. Si quieres más profundidad: GEMINI_MODEL=gemini-2.5-pro
MODELO = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

MAX_INTENTOS_API = 3          # reintentos por llamada a la API (errores 429/500...)
MAX_RONDAS = 2                # veces que se repite investigación+estructurado si la ficha sale pobre
MIN_ITEMS_SECCION = 3         # mínimo de líneas por sección de la ficha técnica
MIN_ITEMS_TOTAL = 24          # mínimo total de líneas de especificaciones
PAUSA_ENTRE_PRODUCTOS = 4     # segundos (evita límites de cuota)

# True: usa el precio que encuentre Gemini si es coherente con el del catálogo (±40%)
USAR_PRECIO_EN_TIEMPO_REAL = True

# True: NO publica fichas pobres (el workflow termina en rojo para que lo veas)
# False: publica igualmente con lo que haya
SALTAR_SI_FICHA_POBRE = True

# UNA_LLAMADA=1 -> 1 petición por producto (búsqueda + JSON en la misma llamada).
# Ideal para la capa gratuita (20 peticiones/día). Por defecto: 2 llamadas (más fiable).
UNA_LLAMADA = os.environ.get("UNA_LLAMADA", "0") == "1"

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


# ==========================================
# 3. ESQUEMA DE SALIDA (JSON estructurado)
# ==========================================
class Specs(BaseModel):
    pantalla: list[str]
    bateria: list[str]
    conectividad: list[str]
    sensores: list[str]
    deportes: list[str]
    construccion: list[str]


class Ficha(BaseModel):
    badge: str
    resumen_ejecutivo: str
    specs: Specs
    pros: list[str]
    contras: list[str]
    puntuacion: float
    precio_actual_eur: str  # "" si no se ha encontrado


# ==========================================
# 4. CATÁLOGO DE SMARTWATCHES
# ==========================================
productos_catalogo = [
{
        "marca": "Apple",
        "modelo_corto": "Watch Ultra 2",
        "busqueda": "Apple Watch Ultra 2",
        "titulo": "Apple Watch Ultra 2 - Caja de Titanio de 49 mm, Pantalla Retina de 3.000 nits, Conectividad Satelital, Resistencia 100 m",
        "especificaciones": "Caja de titanio aeroespacial de grado 5, pantalla retina OLED de hasta 3.000 nits de brillo, profundímetro certificado para buceo a 40 metros (EN13319), conexión satelital directa para mensajes y SOS de emergencia, y autonomía de hasta 72 horas en modo ahorro.",
        "precio": "899.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/23/Huawei_Watch_GT_2_Smartwatch.jpg"
    },
    {
        "marca": "Garmin",
        "modelo_corto": "Enduro 3",
        "busqueda": "Garmin Enduro 3",
        "titulo": "Garmin Enduro 3 - Smartwatch para Ultra Resistencia, Cristal Solar Zafiro, Linterna LED, Hasta 320 Horas de Batería GPS",
        "especificaciones": "Diseñado para ultramaratones y expediciones extremos con un peso ultraligero de 63 g. Lente de carga solar Solar Sapphire con bisel de titanio, mapas topográficos TopoActive preinstalados, navegación SatIQ de doble frecuencia y autonomía imbatible de hasta 320 horas con GPS activo mediante carga solar.",
        "precio": "899.99€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/5/5e/Garmin_Vivoactive_4.jpg"
    },
    {
        "marca": "Suunto",
        "modelo_corto": "Vertical Titanium Solar",
        "busqueda": "Suunto Vertical Titanium Solar",
        "titulo": "Suunto Vertical Titanium Solar - Reloj Deportivo Outdoor con Carga Solar, Bisel Titanio Grado 5, Mapas Offline Gratuitos",
        "especificaciones": "Diseño escandinavo ultra resistente con bisel de titanio de grado 5 y cristal de zafiro solar. Ofrece mapas topográficos offline gratuitos de gran precisión, posicionamiento dual GNSS de 5 satélites simultáneos y autonomía continua de hasta 85 horas en seguimiento GPS máximo.",
        "precio": "799.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/f/fb/Galaxy_Watch_7.jpg"
    },
    {
        "marca": "Samsung",
        "modelo_corto": "Galaxy Watch Ultra",
        "busqueda": "Samsung Galaxy Watch Ultra",
        "titulo": "Samsung Galaxy Watch Ultra - Smartwatch 47mm Titanio, Chipset 3nm, GPS Dual, Resistencia 10 ATM e IP68, Galaxy AI",
        "especificaciones": "Caja de titanio de grado 4 con grado de resistencia 10 ATM, certificación militar MIL-STD-810H y resistencia a temperaturas extremas (-20 °C a 55 °C). Procesador de 3 nm para máxima fluidez, pantalla AMOLED de 3.000 nits, sirena de socorro de 86 dB y funciones de entrenamiento con Galaxy AI.",
        "precio": "699.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/f/f0/Amazfit_GTR_2e.jpg"
    },
    {
        "marca": "Polar",
        "modelo_corto": "Grit X2 Pro Titan",
        "busqueda": "Polar Grit X2 Pro Titan",
        "titulo": "Polar Grit X2 Pro Titan - Reloj Outdoor Extremo con Bisel de Titanio, Cristal de Zafiro, Estándar MIL-STD-810H, Biometría Elixir",
        "especificaciones": "Construido con bisel de titanio aeroespacial y pantalla AMOLED protegida por cristal de zafiro de alta dureza. Incluye mapas topográficos offline descargables, sensor biomecánico Polar Elixir (ECG en muñeca, SpO2 y temperatura cutánea) y resistencia a temperaturas operativas de -20°C a +50°C.",
        "precio": "869.90€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/29/Coros_Pace_3.jpeg"
    },
    {
        "marca": "COROS",
        "modelo_corto": "VERTIX 2S",
        "busqueda": "COROS VERTIX 2S",
        "titulo": "COROS VERTIX 2S - Reloj de Aventura y Escalada Extrema, Bisel Titanio Grado 5, Pantalla Zafiro, GPS Doble Frecuencia, Batería 118h GPS",
        "especificaciones": "Optimizado para expediciones de alta montaña y escalada con bisel de titanio de grado 5 revestido en PVD y cristal de zafiro. Sistema óptico de frecuencia cardíaca de 5 LEDs, mapas topográficos y paisajísticos globales offline y autonomía de 118 horas en modo GPS completo.",
        "precio": "699.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/29/Coros_Pace_3.jpeg"
    },
    {
        "marca": "Huawei",
        "modelo_corto": "Watch Ultimate",
        "busqueda": "Huawei Watch Ultimate",
        "titulo": "Huawei Watch Ultimate - Smartwatch de Metal Líquido con Circonio, Ordenador de Buceo 100m, Pantalla AMOLED Zafiro",
        "especificaciones": "Cuerpo innovador de metal líquido a base de circonio (4.5 veces más resistente que el titanio), bisel cerámico nanocristalino y cristal de zafiro. Certificado como ordenador de buceo profesional para 100 m (ISO 22810 / EN13319), posicionamiento GPS de 5 sistemas y hasta 14 días de batería.",
        "precio": "749.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/23/Huawei_Watch_GT_2_Smartwatch.jpg"
    },
    {
        "marca": "Garmin",
        "modelo_corto": "Instinct 2X Solar",
        "busqueda": "Garmin Instinct 2X Solar",
        "titulo": "Garmin Instinct 2X Solar - Smartwatch Táctico y Outdoor, Carga Solar Ilimitada, Linterna LED Integrada, Resistencia Militar",
        "especificaciones": "Caja de polímero reforzado con fibra de 50 mm, pantalla transflectiva monocroma de gran visibilidad al sol con cristal Power Glass para autonomía ilimitada en modo reloj inteligente. Incluye GPS multibanda, linterna LED con luz estroboscópica y cumplimiento con estándares térmicos y de choque MIL-STD-810.",
        "precio": "449.99€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/5/5e/Garmin_Vivoactive_4.jpg"
    },
    {
        "marca": "Amazfit",
        "modelo_corto": "T-Rex 3",
        "busqueda": "Amazfit T-Rex 3",
        "titulo": "Amazfit T-Rex 3 - Smartwatch Táctico Rugerizado, Pantalla AMOLED 2.000 nits, Mapas Offline, Hasta 27 Días de Batería",
        "especificaciones": "Construcción táctica de grado militar con bisel de acero inoxidable resistente a temperaturas extremas (-30°C a +70°C), pantalla de 1,5\", mapas topográficos giro a giro, asistente IA Zepp Flow y batería imbatible de hasta 27 días.",
        "precio": "279.90€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/5/52/Fitbit_Charge_5.jpg"
    }
]

# ==========================================
# 5. UTILIDADES
# ==========================================
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
        # el último separador es el decimal
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
    base = producto["precio"]
    if not USAR_PRECIO_EN_TIEMPO_REAL:
        return base
    n_base, n_ia = a_numero(base), a_numero(precio_ia)
    if n_base and n_ia and 0.6 * n_base <= n_ia <= 1.4 * n_base:
        return f"{n_ia:.2f}€"
    return base


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
    """Devuelve los dominios que Google Search ha usado (solo para el log)."""
    try:
        chunks = respuesta.candidates[0].grounding_metadata.grounding_chunks or []
        return sorted({c.web.title for c in chunks if c.web and c.web.title})
    except Exception:
        return []


# ==========================================
# 6. FASE 1: INVESTIGACIÓN EN TIEMPO REAL (Google Search, texto libre)
# ==========================================
def investigar(producto):
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
        temperature=0.1,
    )
    r = llamar_gemini(prompt, config, "investigación")
    if not r:
        return None
    fuentes = fuentes_usadas(r)
    if fuentes:
        print(f"   🔎 Fuentes consultadas: {', '.join(fuentes[:8])}")
    else:
        print("   ⚠️ Gemini no devolvió fuentes de búsqueda (datos posiblemente de memoria)")
    return r.text


# ==========================================
# 7. FASE 2: ESTRUCTURADO EN JSON (sin herramientas, esquema forzado)
# ==========================================
def extraer_json(texto):
    """Extrae el primer objeto JSON de un texto (por si viene con ``` o explicaciones)."""
    texto = texto.strip()
    a, b = texto.find("{"), texto.rfind("}")
    if a == -1 or b == -1:
        raise json.JSONDecodeError("sin JSON", texto, 0)
    return json.loads(texto[a:b + 1])


ESQUEMA_TEXTO = """Responde ÚNICAMENTE con un objeto JSON válido (sin ``` ni texto extra) con estas claves:
{"badge": str, "resumen_ejecutivo": str,
 "specs": {"pantalla": [str], "bateria": [str], "conectividad": [str], "sensores": [str], "deportes": [str], "construccion": [str]},
 "pros": [str], "contras": [str], "puntuacion": number, "precio_actual_eur": str}"""


def estructurar(producto, investigacion=None):
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

Todo en español de España. No inventes ningún dato que no esté en las fuentes o en el catálogo.
"""
    if investigacion:
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
        return None
    if not investigacion:
        fuentes = fuentes_usadas(r)
        print(f"   🔎 Fuentes consultadas: {', '.join(fuentes[:8])}" if fuentes
              else "   ⚠️ Sin fuentes de búsqueda (datos posiblemente de memoria)")
    try:
        return extraer_json(r.text)
    except json.JSONDecodeError as err:
        print(f"   ⚠️ JSON inválido en fase de estructurado: {err}")
        return None


# ==========================================
# 8. LIMPIEZA Y VALIDACIÓN DE CALIDAD
# ==========================================
RE_BASURA = re.compile(r"^\s*(precio|price|coste|fabricante|marca|modelo)\b", re.I)
RE_VAGO = re.compile(r"no confirmado|no disponible|n/a|optimizad[ao] para", re.I)


def limpiar(datos):
    """Quita líneas basura (precio/marca como spec, datos vagos o sin confirmar)."""
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
    return datos


def validar(datos):
    """Devuelve (ok, motivo)."""
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
    return True, ""


def obtener_ficha(producto):
    """Investiga + estructura + valida, repitiendo hasta MAX_RONDAS veces."""
    mejor = None
    for ronda in range(1, MAX_RONDAS + 1):
        print(f"   🔁 Ronda {ronda}/{MAX_RONDAS}")
        if UNA_LLAMADA:
            datos = estructurar(producto)
        else:
            investigacion = investigar(producto)
            if not investigacion:
                continue
            datos = estructurar(producto, investigacion)
        if not datos:
            continue
        datos = limpiar(datos)
        ok, motivo = validar(datos)
        if ok:
            return datos
        print(f"   ⚠️ Ficha pobre: {motivo}")
        total = sum(len(datos["specs"][c]) for c, _ in SECCIONES)
        if mejor is None or total > mejor[0]:
            mejor = (total, datos)
    if mejor and not SALTAR_SI_FICHA_POBRE:
        print("   ⚠️ Se usa la mejor ficha obtenida aunque sea incompleta.")
        return mejor[1]
    return None


# ==========================================
# 9. GENERACIÓN DE HTML Y PUBLICACIÓN
# ==========================================
def construir_html(producto, datos, precio, affiliate_link):
    s = datos["specs"]
    e = html.escape

    filas = []
    for i, (clave, titulo) in enumerate(SECCIONES):
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

    return f"""
    <div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 24px; background-color: #ffffff; max-width: 750px; margin: 20px auto; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">

      <div style="text-align: center; margin-bottom: 20px;">
        <img src="{e(producto['imagen'])}" alt="{e(producto['titulo'])}" style="max-height: 280px; width: auto; object-fit: contain; border-radius: 8px;" />
      </div>

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
        <p style="font-size: 1.3em; font-weight: bold; color: #111; margin-bottom: 15px;">
          Precio estimado: <span style="color: #b12704;">{e(precio)}</span> | Puntuación: ⭐ <strong>{puntuacion}/10</strong>
        </p>
        <a href="{affiliate_link}" target="_blank" rel="sponsored nofollow" style="background-color: #ffa41c; color: #111; text-decoration: none; font-size: 1.2em; font-weight: bold; padding: 16px 32px; border-radius: 8px; border: 1px solid #ff8f00; display: inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
          Ver precio actualizado en Amazon 🛒
        </a>
      </div>
    </div>
    """


def procesar_y_publicar(producto):
    print(f"\n🌐 Investigando en tiempo real: {producto['titulo']}")
    query_encoded = urllib.parse.quote_plus(producto["busqueda"])
    affiliate_link = f"https://www.amazon.es/s?k={query_encoded}&tag={AMAZON_TAG}"

    datos = obtener_ficha(producto)
    if not datos:
        print(f"❌ No se ha podido generar una ficha completa para {producto['titulo']}. NO se publica.")
        return False

    s = datos["specs"]
    total = sum(len(s[c]) for c, _ in SECCIONES)
    print(f"   ✅ Ficha completa: {total} líneas de especificaciones")

    precio = resolver_precio(producto, datos.get("precio_actual_eur", ""))
    html_content = construir_html(producto, datos, precio, affiliate_link)

    wp_endpoint = f"{WP_URL}/wp-json/wp/v2/posts"
    payload = {
        "title": f"Análisis y Opinión: {producto['titulo']}",
        "content": html_content,
        "status": "publish",
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

    try:
        res = requests.post(wp_endpoint, json=payload, auth=(WP_USER, WP_APP_PASSWORD), timeout=60)
    except requests.RequestException as err:
        print(f"❌ Error de conexión con WordPress: {err}")
        return False

    if res.status_code == 201:
        print(f"🎉 Publicación creada: {producto['titulo']}")
        return True
    print(f"❌ Error WordPress ({res.status_code}): {res.text[:300]}")
    return False


if __name__ == "__main__":
    fallidos = []
    for i, item in enumerate(productos_catalogo):
        try:
            if not procesar_y_publicar(item):
                fallidos.append(item["titulo"])
        except QuotaAgotada as q:
            print(f"\n🛑 {q} Se detiene la ejecución para no gastar más peticiones.")
            print("   Soluciones: esperar al reinicio diario, activar facturación en Google AI Studio,")
            print("   usar otro modelo (GEMINI_MODEL) o activar UNA_LLAMADA=1.")
            fallidos.extend(p["titulo"] for p in productos_catalogo[i:])
            break
        if i < len(productos_catalogo) - 1:
            time.sleep(PAUSA_ENTRE_PRODUCTOS)

    print("\n==============================")
    print(f"Publicados: {len(productos_catalogo) - len(fallidos)}/{len(productos_catalogo)}")
    if fallidos:
        print("Con problemas:")
        for t in fallidos:
            print(f"  - {t}")
        sys.exit(1)  # marca el workflow de GitHub en rojo para que lo veas
