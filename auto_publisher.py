import os
import json
import time
import requests
import urllib.parse
from google import genai

# ==========================================
# 1. LECTURA SEGURA DE CREDENCIALES
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WP_URL = os.environ.get("WP_URL").rstrip('/')
WP_USER = os.environ.get("WP_USER")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")

AMAZON_TAG = "topcomparad00-21"

client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# 2. CATÁLOGO DE SMARTWATCHES CON CAMPOS LIMPIOS
# ==========================================
# Top 10 smartwatches con mejor batería (datos recopilados en noviembre de 2026)
# Ordenados por la cifra de autonomía más alta que declara el fabricante en modo reloj inteligente
# (con carga solar cuando el reloj la tiene). Son cifras "hasta": dependen del uso y de la luz solar.
#
# IMPORTANTE ANTES DE PUBLICAR:
#  - "link_afiliado" y "asin" están vacíos a propósito: hay que obtenerlos desde tu cuenta de Afiliados.
#  - "imagen" está vacío: sube una foto correcta a tu biblioteca de medios y pega la URL.
#  - "titulo" es descriptivo; ajústalo si quieres que coincida exactamente con el anuncio de Amazon.
#  - Los precios son orientativos (PVP o precio de mercado reciente) y cambian a menudo.

productos_catalogo = [

    # 1) RUNNING
    {
        "categoria": "smartwatch",
        "marca": "COROS",
        "modelo_corto": "PACE 4",
        "busqueda": "COROS PACE 4",
        "link_afiliado": "",
        "asin": "",
        "titulo": "COROS PACE 4 - Reloj GPS de Running Ultraligero con Pantalla AMOLED, GPS de Doble Frecuencia, 5 ATM y hasta 41 Horas de Batería",
        "especificaciones": "MEJOR PARA RUNNING. Es el reloj de running con mejor equilibrio entre precio y prestaciones: GPS de doble frecuencia que mantiene la precisión incluso entre edificios o bosque cerrado, solo 27 g (32 g con la correa de nailon), pantalla AMOLED de 390 x 390 píxeles, resistencia 5 ATM y hasta 41 horas de autonomía con GPS. Incluye perfiles de piscina, aguas abiertas y triatlón, y en septiembre de 2026 recibió mapas sin conexión mediante una actualización (en beta). Xataka lo señala como el de mejor relación calidad-precio entre los relojes deportivos con GPS que recomienda. Precio en España: 269 €. Si quieres más pantalla y batería, existe el PACE 4 Pro (449 €, hasta 60 horas de GPS).",
        "precio": "269.00€",
        "imagen": "",
    },
    # 2) CICLISMO Y TRIATLÓN
    {
        "categoria": "smartwatch",
        "marca": "Garmin",
        "modelo_corto": "Forerunner 970",
        "busqueda": "Garmin Forerunner 970",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Garmin Forerunner 970 - Reloj GPS Multideporte Premium para Triatlón, Ciclismo y Running con Pantalla AMOLED, GPS Multibanda y Mapas",
        "especificaciones": "MEJOR PARA CICLISMO Y TRIATLÓN. Es el modelo que Xataka recomienda como mejor reloj deportivo con GPS: reúne algunas de las mejores prestaciones de la gama fēnix a un precio más bajo. Es un reloj multideporte con pantalla AMOLED, GPS multibanda y mapas integrados, y TechRadar lo elige como mejor reloj de natación para triatlón (resistencia 5 ATM). Es compatible con los sensores externos habituales del ciclismo (potenciómetro, cadencia) por ANT+ y Bluetooth, un terreno en el que, según una guía, Garmin y COROS superan al Apple Watch en precisión y autonomía. Precio orientativo de 720-750 €; verifícalo en Amazon.es.",
        "precio": "749.99€",
        "imagen": "",
    },
    # 3) NATACIÓN
    {
        "categoria": "smartwatch",
        "marca": "Garmin",
        "modelo_corto": "Swim 2",
        "busqueda": "Garmin Swim 2",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Garmin Swim 2 - Reloj GPS de Natación para Piscina y Aguas Abiertas con Pulsómetro, Detección de Brazada y SWOLF",
        "especificaciones": "MEJOR PARA NATACIÓN (piscina y aguas abiertas). Fue diseñado alrededor de la natación: detecta el estilo de brazada, cuenta brazadas y largos, calcula el índice SWOLF y mide el pulso en el agua, con GPS, GLONASS y Galileo para aguas abiertas. Pesa 36 g y su batería dura en torno a una semana según usuarios. También tiene perfiles de carrera y ciclismo, pero no es un smartwatch completo: se centra en nadar. PVP de 250 €, y en julio de 2026 se vio a 140,48 € en Amazon. Si usas iPhone y quieres un reloj para varios deportes, el Apple Watch Ultra 3 es una alternativa; si además corres, el COROS PACE 4 funciona bien en piscina y aguas abiertas.",
        "precio": "250.00€",
        "imagen": "",
    },
    # 4) BUCEO
    {
        "categoria": "smartwatch",
        "marca": "Garmin",
        "modelo_corto": "Descent G2",
        "busqueda": "Garmin Descent G2",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Garmin Descent G2 - Ordenador de Buceo Tipo Reloj con Pantalla AMOLED, hasta 100 m, Modos Recreativo, Técnico y Apnea y 10 Días de Batería",
        "especificaciones": "MEJOR PARA BUCEO. Es un ordenador de buceo con forma de reloj, no un smartwatch con una app: resiste hasta 100 metros y admite buceo recreativo, técnico y apnea, incluida la apnea en piscina. Tiene pantalla AMOLED de 1,2 pulgadas y unos 10 días de batería, se empareja con el inReach Mini 2 para SOS por satélite y, fuera del agua, funciona como smartwatch Garmin. Frente al Apple Watch Ultra, certificado para buceo recreativo hasta 40 m y que necesita la suscripción Oceanic+ (9,99 € al mes) para actuar como ordenador de buceo, el Descent G2 llega mucho más profundo. No tiene linterna, algo que sí incluyen los Descent Mk3. Precio orientativo de unos 680 € (visto en una tienda europea): verifícalo en Amazon.es. Bucear exige formación certificada.",
        "precio": "679.90€",
        "imagen": "",
    },
    # 5) SURF
    {
        "categoria": "smartwatch",
        "marca": "Apple",
        "modelo_corto": "Watch Ultra 3",
        "busqueda": "Apple Watch Ultra 3 GPS + Cellular 49mm",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Apple Watch Ultra 3 (GPS + Cellular, 49 mm) - Smartwatch de Titanio con 100 m de Resistencia, GPS de Doble Frecuencia y Conectividad Satelital, solo para iPhone",
        "especificaciones": "MEJOR PARA SURF (con iPhone). Combina caja de titanio con resistencia WR100 (100 m), que aguanta mejor la corrosión del agua salada que el aluminio, con sirena de emergencia muy potente, GPS de doble frecuencia y conectividad móvil y satelital independiente del teléfono. Hay apps de olas y mareas como Ocean Watch, Surf Watch o Dawn Patrol y es compatible con Surfline Sessions. También puede funcionar como ordenador de buceo recreativo hasta 40 m con la suscripción Oceanic+. Autonomía de hasta 42 horas en modo ahorro. Solo funciona con iPhone; si usas Android, los Garmin Instinct son la alternativa habitual en surf. PVP de 899 €; tras salir el Ultra 4 se ha visto a 704 € en MediaMarkt.",
        "precio": "899.00€",
        "imagen": "",
    },
    # 6) GOLF
    {
        "categoria": "smartwatch",
        "marca": "Garmin",
        "modelo_corto": "Approach S72",
        "busqueda": "Garmin Approach S72",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Garmin Approach S72 - Smartwatch GPS de Golf Premium con Pantalla AMOLED, Mapas Integrados, Linterna LED y ECG",
        "especificaciones": "MEJOR PARA GOLF. Garmin lo presenta como su reloj inteligente definitivo para golf y sustituye al Approach S70 (que traía más de 43.000 campos precargados, un caddie virtual con dispersión de golpes y la función PlaysLike para ajustar la distancia). El S72 añade mapas integrados, linterna LED y el software Training Readiness, con pantalla AMOLED y ECG. Salió a principios de octubre de 2026 a 799,99 €, así que aún hay pocas pruebas a largo plazo. Si buscas algo más barato, el Approach S44 (pantalla AMOLED y más de 43.000 campos) ronda los 231 €.",
        "precio": "799.99€",
        "imagen": "",
    },
    # 7) PÁDEL Y TENIS
    {
        "categoria": "smartwatch",
        "marca": "Mibro",
        "modelo_corto": "GS Pro 2",
        "busqueda": "Mibro GS Pro2",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Mibro GS Pro2 - Reloj Inteligente Deportivo con GPS de Doble Frecuencia, Pantalla AMOLED de 1,43 Pulgadas, Modo Pádel, Llamadas Bluetooth y 5 ATM",
        "especificaciones": "MEJOR PARA PÁDEL (y deportes de raqueta). Es uno de los pocos relojes pensados para jugar al pádel: Xataka lo probó en partidos y clases y destaca que su modo pádel detecta el tipo de golpe y su velocidad. Según la marca, reconoce seis golpes: revés cortado, derecha cortada, smash, globo de derecha, globo de revés y bandeja. Pantalla AMOLED de 1,43 pulgadas, GPS de doble frecuencia, resistencia 5 ATM, llamadas Bluetooth, más de 100 modos deportivos (con triatlón) y una batería de hasta dos semanas. Cuesta 99,99 € en Amazon. Para tenis no he encontrado pruebas independientes de análisis de golpes: úsalo como reloj deportivo con modo de raqueta.",
        "precio": "99.99€",
        "imagen": "",
    },
    # 8) ESQUÍ Y SNOWBOARD
    {
        "categoria": "smartwatch",
        "marca": "Garmin",
        "modelo_corto": "fēnix E 47 mm",
        "busqueda": "Garmin fēnix E 47mm AMOLED",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Garmin fēnix E 47 mm - Smartwatch GPS Multideporte con Pantalla AMOLED, Mapas TopoActive de Estaciones de Esquí y Campos de Golf, 10 ATM",
        "especificaciones": "MEJOR PARA ESQUÍ Y SNOWBOARD. Incluye perfiles específicos de esquí, mapas TopoActive de estaciones de esquí y cinco botones físicos que se manejan bien con guantes, lluvia o manos sudadas. Pantalla AMOLED táctil de 1,3 pulgadas, caja de 47 mm con bisel de acero inoxidable, resistencia 10 ATM y pruebas bajo estándares militares. Hasta 16 días en modo smartwatch (unos 6 con la pantalla siempre activa) y hasta 42 horas con GPS. También cubre running, ciclismo, natación, senderismo, golf, triatlón y fuerza. No incluye linterna LED, altavoz, micrófono ni cristal de zafiro, y no tiene las funciones de buceo del fēnix 8. PVP de 599,99 €; en junio de 2026 se vio a 360,90 € en Amazon.",
        "precio": "599.99€",
        "imagen": "",
    },
    # 9) SENDERISMO Y MONTAÑA
    {
        "categoria": "smartwatch",
        "marca": "COROS",
        "modelo_corto": "APEX 4 42 mm",
        "busqueda": "COROS APEX 4 42mm",
        "link_afiliado": "",
        "asin": "",
        "titulo": "COROS APEX 4 (42 mm) - Reloj GPS de Montaña y Aventura con Titanio y Zafiro, Mapas Topográficos y Autonomía Extrema",
        "especificaciones": "MEJOR PARA SENDERISMO Y MONTAÑA. Reúne construcción de titanio y zafiro con una autonomía muy larga y mapas topográficos, que se renderizan hasta 30 veces más rápido que en versiones anteriores de la marca. Versión de 42 mm a 449 € en Amazon y El Corte Inglés, que era su mínimo histórico en junio de 2026. Alternativas de precio similar o inferior para montaña: Garmin Instinct 3 AMOLED (desde 359 €), Polar Grit X2 (desde 380 €) y Suunto Race (desde 399 €).",
        "precio": "449.00€",
        "imagen": "",
    },
    # 10) GIMNASIO Y FUERZA (YA ESTÁ EN EL CATÁLOGO DE MAYORES: ver nota de arriba)
    {
        "categoria": "smartwatch",
        "marca": "Garmin",
        "modelo_corto": "Venu 4",
        "busqueda": "Garmin Venu 4",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Garmin Venu 4 - Smartwatch con Pantalla AMOLED, Entrenamiento de Fuerza con Recuento de Repeticiones y hasta 12 Días de Batería, para iPhone y Android",
        "especificaciones": "MEJOR PARA GIMNASIO Y FUERZA. Los relojes Garmin registran el entrenamiento de fuerza por series: cuentan las repeticiones (el recuento aparece al completar al menos cuatro), pueden detectar automáticamente el inicio y el final de cada serie y envían la sesión a Garmin Connect, aunque los ejercicios de pierna pueden no contabilizarse. Una guía lo considera la mejor opción «fitness primero, smartwatch después». Autonomía de hasta 12 días en el modelo de 45 mm (10 en el de 41 mm), compatible con iPhone y Android. PVP de 499 €.",
        "precio": "499.00€",
        "imagen": "",
    },
]


def render_bullets(items):
    """Convierte una lista de strings en elementos de lista HTML con viñetas"""
    if isinstance(items, list):
        return "".join([f"<li style='margin-bottom: 4px;'>{item}</li>" for item in items])
    return f"<li>{items}</li>"

def procesar_y_publicar(producto):
    query_encoded = urllib.parse.quote_plus(producto['busqueda'])
    affiliate_link = f"https://www.amazon.es/s?k={query_encoded}&tag={AMAZON_TAG}"

    prompt = f"""
    Actúa como analista de tecnología experto en Smartwatches y CRO.
    Analiza este producto:
    - Título: {producto['titulo']}
    - Especificaciones base: {producto['especificaciones']}
    - Precio: {producto['precio']}

    IMPORTANTE: Debes rellenar TODAS las siguientes especificaciones de forma exhaustiva y esquemática (nunca dejes campos vacíos o con datos faltantes como el tamaño de pantalla si se puede deducir).
    
    Devuelve ÚNICAMENTE un objeto JSON válido (y nada más que el JSON) con exactamente estas claves:
    "badge", "resumen_ejecutivo", 
    "specs" (un objeto JSON con exactamente estas 6 claves, donde cada clave es una LISTA de strings esquemáticos: 
       "pantalla" (incluir obligatoriamente tecnología y tamaño en pulgadas si aplica), 
       "bateria" (incluir autonomía estimada), 
       "conectividad" (incluir GPS y pagos NFC), 
       "sensores" (incluir frecuencia cardíaca, SpO2, etc.), 
       "deportes" (modos deportivos y entrenadores), 
       "construccion" (materiales y resistencia al agua)),
    "pros" (lista de 3 strings), 
    "contras" (lista de 2 strings), 
    "puntuacion" (número decimal).
    """

    print(f"Analizando con Gemini: {producto['titulo']}...")
    
    # --- SISTEMA DE REINTENTOS PARA EVITAR ERRORES TEMPORALES DE CONEXIÓN/SERVIDORES (503) ---
    max_intentos = 3
    response = None
    for intento in range(1, max_intentos + 1):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            break
        except Exception as e:
            print(f"⚠️ Intento {intento}/{max_intentos} fallido por error en la API: {e}")
            if intento < max_intentos:
                time.sleep(5)  # Espera 5 segundos antes de reintentar
            else:
                print(f"❌ Imposible analizar {producto['titulo']} tras {max_intentos} intentos.")

# --- EXTRACCIÓN Y LIMPIEZA SEGURA DEL JSON ---
    datos_ia = None
    if response and hasattr(response, 'text') and response.text:
        texto_respuesta = response.text.strip()
        
        # Limpieza robusta de bloques de código Markdown
        if "```json" in texto_respuesta:
            texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0].strip()
        elif "```" in texto_respuesta:
            texto_respuesta = texto_respuesta.split("```")[1].split("```")[0].strip()
        
        # Intentar parsear el JSON directamente o buscar llaves
        try:
            datos_ia = json.loads(texto_respuesta)
        except json.JSONDecodeError:
            inicio = texto_respuesta.find('{')
            fin = texto_respuesta.rfind('}')
            if inicio != -1 and fin != -1:
                clean_json_str = texto_respuesta[inicio:fin+1]
                try:
                    datos_ia = json.loads(clean_json_str)
                except json.JSONDecodeError as err:
                    print(f"⚠️ Error crítico de JSON en {producto['titulo']}: {err}")
                    print(f"Respuesta recibida de la IA:\n{texto_respuesta}")

    # --- VALORES POR DEFECTO DE EMERGENCIA SI FALLA LA IA O EL JSON ---
    if not datos_ia:
        print(f"💡 Aplicando plantilla de respaldo segura para {producto['titulo']}...")
        datos_ia = {
            "badge": "Destacado Calidad-Precio",
            "resumen_ejecutivo": producto['titulo'] + " ofrece un equilibrio sobresaliente entre diseño, funcionalidad y autonomía para el uso cotidiano.",
            "specs": {
                "pantalla": ["Pantalla de alta definición y óptima visibilidad."],
                "bateria": ["Batería de larga duración adaptada a uso continuo."],
                "conectividad": ["Conexión Bluetooth estable y posicionamiento GPS."],
                "sensores": ["Seguimiento de salud, pulso y calidad del sueño."],
                "deportes": ["Múltiples modos de entrenamiento integrados."],
                "construccion": ["Cuerpo resistente al agua y materiales ligeros."]
            },
            "pros": ["Excelente relación calidad-precio", "Gran autonomía de batería", "Diseño ergonómico y cómodo"],
            "contras": ["Funciones personalizadas según el SO", "Sin NFC para pagos en algunos mercados"],
            "puntuacion": 8.5
        }

    s = datos_ia['specs']

    # HTML del artículo con la tabla oculta de 6 filas x 2 columnas para las especificaciones
    html_content = f"""
    <div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 24px; background-color: #ffffff; max-width: 750px; margin: 20px auto; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
      
      <div style="text-align: center; margin-bottom: 20px;">
        <img src="{producto['imagen']}" alt="{producto['titulo']}" style="max-height: 280px; width: auto; object-fit: contain; border-radius: 8px;" />
      </div>

      <div style="background-color: #ff9900; color: #fff; font-weight: bold; display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 0.85em; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px;">
        🔥 {datos_ia['badge']}
      </div>

      <h2 style="margin-top: 0; color: #111; font-size: 1.6em; line-height: 1.3;">{producto['titulo']}</h2>
      
      <p style="font-size: 1.1em; color: #444; line-height: 1.6;">
        {datos_ia['resumen_ejecutivo']}
      </p>

      <!-- Ficha Técnica en Tabla Oculta (6 filas x 2 columnas) -->
      <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin: 20px 0;">
        <h3 style="color: #0f172a; margin-top: 0; font-size: 1.1em; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; margin-bottom: 12px;">⚙️ Ficha Técnica Resumida</h3>
        
        <table style="width: 100%; border-collapse: collapse; border: none; font-size: 0.95em; color: #334155;">
          <tr style="border: none; border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: bold; width: 30%; vertical-align: top; border: none; background-color: #f1f5f9; border-top-left-radius: 6px;">📺 Pantalla</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
                {render_bullets(s.get('pantalla', []))}
              </ul>
            </td>
          </tr>
          
          <tr style="border: none; border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: bold; vertical-align: top; border: none; background-color: #f1f5f9;">🔋 Batería</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
                {render_bullets(s.get('bateria', []))}
              </ul>
            </td>
          </tr>

          <tr style="border: none; border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: bold; vertical-align: top; border: none; background-color: #f1f5f9;">🌐 Conectividad</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
                {render_bullets(s.get('conectividad', []))}
              </ul>
            </td>
          </tr>

          <tr style="border: none; border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: bold; vertical-align: top; border: none; background-color: #f1f5f9;">💓 Sensores</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
                {render_bullets(s.get('sensores', []))}
              </ul>
            </td>
          </tr>

          <tr style="border: none; border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: bold; vertical-align: top; border: none; background-color: #f1f5f9;">🏃‍♂️ Deportes</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
                {render_bullets(s.get('deportes', []))}
              </ul>
            </td>
          </tr>

          <tr style="border: none;">
            <td style="padding: 10px 12px; font-weight: bold; vertical-align: top; border: none; background-color: #f1f5f9; border-bottom-left-radius: 6px;">🛡️ Construcción</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
                {render_bullets(s.get('construccion', []))}
              </ul>
            </td>
          </tr>
        </table>
      </div>

      <div style="display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 250px; background-color: #f0fdf4; padding: 18px; border-radius: 8px; border-left: 4px solid #22c55e;">
          <h4 style="color: #15803d; margin-top: 0; font-size: 1.1em;">✅ Lo Mejor (Pros)</h4>
          <ul style="padding-left: 18px; color: #166534; margin-bottom: 0; line-height: 1.5;">
            {"".join([f'<li style="margin-bottom: 6px;">{p}</li>' for p in datos_ia['pros']])}
          </ul>
        </div>
        
        <div style="flex: 1; min-width: 250px; background-color: #fef2f2; padding: 18px; border-radius: 8px; border-left: 4px solid #ef4444;">
          <h4 style="color: #b91c1c; margin-top: 0; font-size: 1.1em;">❌ A mejorar (Contras)</h4>
          <ul style="padding-left: 18px; color: #991b1b; margin-bottom: 0; line-height: 1.5;">
            {"".join([f'<li style="margin-bottom: 6px;">{c}</li>' for c in datos_ia['contras']])}
          </ul>
        </div>
      </div>

      <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #f0f0f0;">
        <p style="font-size: 1.3em; font-weight: bold; color: #111; margin-bottom: 15px;">
          Precio estimado: <span style="color: #b12704;">{producto['precio']}</span> | Puntuación: ⭐ <strong>{datos_ia['puntuacion']}/10</strong>
        </p>
        <a href="{affiliate_link}" target="_blank" rel="sponsored nofollow" style="background-color: #ffa41c; color: #111; text-decoration: none; font-size: 1.2em; font-weight: bold; padding: 16px 32px; border-radius: 8px; border: 1px solid #ff8f00; display: inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
          Ver precio actualizado en Amazon 🛒
        </a>
      </div>
    </div>
    """

    wp_endpoint = f"{WP_URL}/wp-json/wp/v2/posts"
    payload = {
        "title": f"Análisis y Opinión: {producto['titulo']}",
        "content": html_content,
        "status": "publish",
        "meta": {
            "top_marca": producto['marca'],
            "top_modelo": producto['modelo_corto'],
            "top_busqueda": producto['busqueda'],
            "spec_pantalla": str(s.get('pantalla', [])),
            "spec_bateria": str(s.get('bateria', [])),
            "spec_conectiv": str(s.get('conectividad', [])),
            "spec_sensores": str(s.get('sensores', [])),
            "spec_deportes": str(s.get('deportes', [])),
            "spec_cuerpo": str(s.get('construccion', []))
        }
    }

    res = requests.post(wp_endpoint, json=payload, auth=(WP_USER, WP_APP_PASSWORD))
    if res.status_code == 201:
        print(f"¡Publicación creada exitosamente para {producto['titulo']}!")
    else:
        print(f"Error ({res.text})")

if __name__ == "__main__":
    for item in productos_catalogo:
        procesar_y_publicar(item)
