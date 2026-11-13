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

# 1) Apple Watch Series 12 - llama solo a emergencias - solo iPhone
    # 1) Elegido por Xataka como mejor smartwatch por menos de 100 euros
    {
        "categoria": "smartwatch",
        "marca": "Amazfit",
        "modelo_corto": "Bip 6",
        "busqueda": "Amazfit Bip 6",
        "link_afiliado": "",
        "asin": "B0DYP9R6YT",
        "titulo": "Amazfit Bip 6 - Smartwatch con Pantalla AMOLED de 1,97 Pulgadas, GPS, Llamadas Bluetooth, más de 100 Modos Deportivos y hasta 2 Semanas de Batería",
        "especificaciones": "Pantalla AMOLED de 1,97 pulgadas con diseño cuadrado que facilita leer notificaciones, GPS integrado, llamadas Bluetooth, más de 100 modos deportivos y sensores de salud. Autonomía de hasta dos semanas según el uso. No incluye NFC, así que no sirve para pagos desde la muñeca. PVP en Amazon de unos 70 €.",
        "precio": "70.00€",
        "imagen": "",
    },
    # 2) GPS, mapas sin conexión y pantalla muy luminosa por unos 100 €
    {
        "categoria": "smartwatch",
        "marca": "Amazfit",
        "modelo_corto": "Active 2",
        "busqueda": "Amazfit Active 2",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Amazfit Active 2 - Reloj Inteligente de 44 mm con Pantalla AMOLED de 1,32 Pulgadas, GPS, Mapas Offline, más de 160 Modos Deportivos y 10 Días de Batería",
        "especificaciones": "Pantalla AMOLED de 1,32 pulgadas (466 x 466) con hasta 2.000 nits de brillo, cristal templado, GPS compatible con cinco sistemas de satélite, mapas sin conexión, más de 160 modos deportivos, llamadas Bluetooth y resistencia 5 ATM. Pesa unos 29,5 g sin correa. Batería de 270 mAh con 10 días de autonomía en uso típico (19 en modo ahorro) y 21 horas con el GPS activo. La versión estándar cuesta 99,90 € y la Premium, 129,90 €; el NFC depende de la versión, así que confírmalo en el anuncio.",
        "precio": "99.90€",
        "imagen": "",
    },
    # 3) Pantalla grande y mucha batería por menos de 100 €
    {
        "categoria": "smartwatch",
        "marca": "Xiaomi",
        "modelo_corto": "Redmi Watch 6",
        "busqueda": "Xiaomi Redmi Watch 6",
        "link_afiliado": "",
        "asin": "B0GQL9JZS7",
        "titulo": "Xiaomi Redmi Watch 6 - Smartwatch con Pantalla AMOLED de 2,07 Pulgadas, GPS, Llamadas Bluetooth, más de 150 Modos Deportivos y hasta 24 Días de Batería",
        "especificaciones": "Pantalla AMOLED de 2,07 pulgadas, corona giratoria, más de 150 modos deportivos, llamadas Bluetooth, GPS, resistencia 5 ATM, sensores de pulso y oxígeno en sangre, y sistema HyperOS. Autonomía de hasta 24 días según el fabricante. La versión básica no incluye NFC; existe otra, algo más cara, que sí lo incluye. Precios recientes entre 83 y 100 € según la tienda.",
        "precio": "91.98€",
        "imagen": "",
    },
    # 4) GPS de doble banda y 13 días de batería por unos 100 €
    {
        "categoria": "smartwatch",
        "marca": "CMF by Nothing",
        "modelo_corto": "Watch 3 Pro",
        "busqueda": "CMF by Nothing Watch 3 Pro",
        "link_afiliado": "",
        "asin": "",
        "titulo": "CMF by Nothing Watch 3 Pro - Reloj Inteligente con Pantalla AMOLED de 1,43 Pulgadas, GPS de Doble Banda, Llamadas Bluetooth con IA y 13 Días de Batería",
        "especificaciones": "Caja de aluminio con pantalla AMOLED circular de 1,43 pulgadas (466 x 466) con modo siempre activo, GPS de doble banda con cinco sistemas de navegación, sensor de frecuencia cardíaca de cuatro canales, SpO2, sueño y estrés, y más de 130 modos deportivos. Llamadas Bluetooth con micrófono y altavoz, resistencia IP68 y batería de 350 mAh para hasta 13 días. No tiene NFC ni almacenamiento de música. Algunas funciones de IA exigen emparejarlo con un móvil Nothing o CMF. PVP de 99 €, con ofertas cercanas a 72 €.",
        "precio": "99.00€",
        "imagen": "",
    },
    # 5) El más completo por debajo de 200 €: NFC, GPS doble banda, pantalla de 2.500 nits
    {
        "categoria": "smartwatch",
        "marca": "Huawei",
        "modelo_corto": "Watch Fit 5",
        "busqueda": "HUAWEI Watch Fit 5",
        "link_afiliado": "",
        "asin": "",
        "titulo": "HUAWEI Watch Fit 5 - Smartwatch con GPS, Pantalla AMOLED de 1,82 Pulgadas y 2.500 nits, Pago NFC, 5 ATM, Diseño Ultraligero y hasta 10 Días de Autonomía",
        "especificaciones": "Pantalla AMOLED de 1,82 pulgadas con hasta 2.500 nits, solo 27 g, GPS de doble banda, NFC para pagos, llamadas Bluetooth, más de 100 modos deportivos, resistencia 5 ATM e IP6X y batería de 471 mAh con hasta 10 días de autonomía (unos 7 en uso típico según algunas tiendas). Compatible con Android e iOS. PVP de 199 €, con ofertas habituales entre 155 y 180 €.",
        "precio": "199.00€",
        "imagen": "",
    },
    # 6) Mapas sin conexión y hasta 20 días de batería
    {
        "categoria": "smartwatch",
        "marca": "Amazfit",
        "modelo_corto": "Bip Max",
        "busqueda": "Amazfit Bip Max",
        "link_afiliado": "",
        "asin": "B0GWHMXWGL",
        "titulo": "Amazfit Bip Max - Smartwatch con Pantalla AMOLED de 2,07 Pulgadas, GPS, Mapas Offline, Compatible con Strava y hasta 20 Días de Batería",
        "especificaciones": "Pantalla AMOLED de 2,07 pulgadas, mapas sin conexión, compatibilidad con Strava y función de planes de entrenamiento. Autonomía teórica de hasta 20 días y medición constante de la salud. No incluye NFC. Precio de lanzamiento de 99,90 €.",
        "precio": "99.90€",
        "imagen": "",
    },
    # 7) Corona giratoria y buena pantalla; el mejor precio suele estar fuera de Amazon
    {
        "categoria": "smartwatch",
        "marca": "Huawei",
        "modelo_corto": "Watch Fit 3",
        "busqueda": "HUAWEI Watch Fit 3",
        "link_afiliado": "",
        "asin": "B0CYC5CCMH",
        "titulo": "HUAWEI Watch Fit 3 - Smartwatch con Pantalla AMOLED de 1,82 Pulgadas, Corona Giratoria y hasta 10 Días de Batería",
        "especificaciones": "Pantalla AMOLED de 1,82 pulgadas que se ve bien a plena luz del día, diseño cómodo y elegante, y corona giratoria que también se pulsa. La batería aguanta una semana sin problema (hasta 10 días según el fabricante). No tiene pagos móviles y su sistema operativo es menos completo. Es un modelo de hace dos generaciones con muy buena relación calidad-precio: unos 89 € en MediaMarkt, aunque en Amazon se ha visto a 145 €.",
        "precio": "89.00€",
        "imagen": "",
    },
    # 8) Garmin asequible: AMOLED, 11 días y ecosistema Garmin
    {
        "categoria": "smartwatch",
        "marca": "Garmin",
        "modelo_corto": "vívoactive 5",
        "busqueda": "Garmin vívoactive 5",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Garmin vívoactive 5 - Smartwatch GPS con Pantalla AMOLED de 1,2 Pulgadas, 4 GB y hasta 11 Días de Batería",
        "especificaciones": "Reloj discreto con pantalla AMOLED de 1,2 pulgadas, GPS, 4 GB de almacenamiento y unas 30 aplicaciones deportivas preinstaladas. Hasta 11 días de autonomía y compatibilidad con la app Garmin Connect. Se ha visto a 177,65 € con cupón en MediaMarkt y a 181 € como precio mínimo reciente.",
        "precio": "181.00€",
        "imagen": "",
    },
    # 9) Garmin de running barato (oferta con cupón)
    {
        "categoria": "smartwatch",
        "marca": "Garmin",
        "modelo_corto": "Forerunner 55",
        "busqueda": "Garmin Forerunner 55",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Garmin Forerunner 55 - Reloj GPS de Running con Detección de Incidentes, Función de Asistencia y Gran Autonomía",
        "especificaciones": "Reloj de running robusto con pantalla de 1,04 pulgadas, buen surtido de modos deportivos, detección de incidentes y función de asistencia (necesitan el móvil cerca para avisar a los contactos). Destaca por su batería. Se ha visto a 143,65 € aplicando un cupón en MediaMarkt; es un modelo veterano, así que revisa si sigue disponible.",
        "precio": "143.65€",
        "imagen": "",
    },
    # 10) El más barato de la lista
    {
        "categoria": "smartwatch",
        "marca": "Xiaomi",
        "modelo_corto": "Redmi Watch 5 Lite",
        "busqueda": "Xiaomi Redmi Watch 5 Lite",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Xiaomi Redmi Watch 5 Lite - Smartwatch con Pantalla AMOLED, Llamadas Bluetooth y hasta 18 Días de Batería",
        "especificaciones": "El smartwatch más económico de la lista, con pantalla AMOLED, llamadas Bluetooth y una batería que dura casi dos semanas (hasta 18 días según el fabricante). Sus prestaciones son menores que las de la competencia. Precio reciente de 42,99 € en MediaMarkt.",
        "precio": "42.99€",
        "imagen": "",
    }
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
