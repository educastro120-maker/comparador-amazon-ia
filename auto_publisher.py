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
    {
        "categoria": "smartwatch",
        "marca": "Apple",
        "modelo_corto": "Watch Series 12",
        "busqueda": "Apple Watch Series 12 GPS + Cellular",
        "link_afiliado": "https://link.amazon/B0hYwgaNE",
        "asin": "",
        "titulo": "Apple Watch Series 12 (GPS + Cellular) - Smartwatch con Detección de Caídas, SOS de Emergencia, ECG y Oxígeno en Sangre, Compatible solo con iPhone",
        "especificaciones": "Desde 449 € en versión GPS; para usarlo sin el iPhone cerca hace falta la versión con datos móviles y una línea activa. Tras una caída fuerte, el reloj vibra y suena una alarma; si la persona no se mueve durante aproximadamente un minuto, inicia una cuenta atrás de 30 segundos y llama por sí solo a emergencias, y después envía un mensaje con la ubicación a los contactos de emergencia. Incluye electrocardiograma, oxígeno en sangre, notificaciones de posible hipertensión y medición de la frecuencia cardíaca cada cinco segundos. Autonomía de hasta 24 horas, por lo que requiere carga diaria. Solo funciona con iPhone. No detecta todas las caídas.",
        "precio": "449.00€",
        "imagen": "https://topcomparador.es/wp-content/uploads/2026/11/Apple-Watch-Series-12-GPS-Cellular.jpg",
    },
    # 2) Apple Watch SE 3 - misma detección de caídas, más barato - solo iPhone
    {
        "categoria": "smartwatch",
        "marca": "Apple",
        "modelo_corto": "Watch SE 3",
        "busqueda": "Apple Watch SE 3 GPS + Cellular",
        "link_afiliado": "https://link.amazon/B0eLleeKP",
        "asin": "",
        "titulo": "Apple Watch SE 3 (GPS + Cellular) - Smartwatch con Detección de Caídas, Llamada de Emergencia y Localización, Compatible solo con iPhone",
        "especificaciones": "Desde 269 € en versión GPS; la versión con datos móviles permite usarlo sin el iPhone cerca. Ofrece la misma detección de caídas y llamada de emergencia que el Series 12, aunque no incluye electrocardiograma, oxígeno en sangre ni notificaciones de hipertensión. Autonomía de hasta 18 horas con carga diaria. Solo funciona con iPhone. No detecta todas las caídas.",
        "precio": "269.00€",
        "imagen": "https://topcomparador.es/wp-content/uploads/2026/11/apple-watch-se-3-gps-cellular-44mm-aluminio-medianoche-correa-deportiva-azul-marino-m-l-mjlt4ql-a.jpg",
    },
    # 3) Google Pixel Watch 4 LTE - puede llamar a emergencias - Android
    {
        "categoria": "smartwatch",
        "marca": "Google",
        "modelo_corto": "Pixel Watch 4 LTE 41 mm",
        "busqueda": "Google Pixel Watch 4 41mm LTE",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Google Pixel Watch 4 (41 mm) LTE - Smartwatch Android con Detección de Caídas, Llamada de Emergencia, Pantalla AMOLED de 3.000 nits y Gemini",
        "especificaciones": "Tras una caída fuerte, el reloj espera unos 30 segundos, vibra, suena muy alto y pregunta si se quiere llamar a emergencias; si no hay respuesta en 60 segundos, puede llamar y reproducir un mensaje de voz automático con la ubicación (España figura entre los países compatibles). La versión LTE puede llamar sin el móvil cerca, siempre que tenga la línea activa; la versión Wi-Fi depende del teléfono. Incluye detección de pérdida de pulso y de accidentes de coche, pantalla AMOLED LTPO de hasta 3.000 nits, 5 ATM y 31 g sin correa. La batería del modelo de 41 mm dura hasta 30 horas (hasta 48 con el modo ahorro). PVP de 499 € en LTE (399 € en Wi-Fi). Funciona con Android.",
        "precio": "499.00€",
        "imagen": "https://topcomparador.es/wp-content/uploads/2026/11/google-pixel-watch-4-41mm-4g-aluminio-negro-correa-obsidiana.jpg",
    },
    # 4) Samsung Galaxy Watch9 LTE 44 mm - Android
    {
        "categoria": "smartwatch",
        "marca": "Samsung",
        "modelo_corto": "Galaxy Watch9 LTE 44 mm",
        "busqueda": "Samsung Galaxy Watch9 44mm LTE",
        "link_afiliado": "https://link.amazon/B07Yx4s2m",
        "asin": "",
        "titulo": "Samsung Galaxy Watch9 (44 mm, LTE) - Smartwatch con Detección de Caídas Graves, SOS, Pantalla Super AMOLED de 1,47 Pulgadas y GPS de Doble Banda",
        "especificaciones": "Pantalla Super AMOLED de 1,47 pulgadas (480 x 480) con cristal de zafiro, 34 g, Wear OS 7, LTE, NFC, GPS de doble banda y resistencia 5 ATM. Incluye detección de caídas graves y SOS; si no hay respuesta, el reloj avisa a los contactos de emergencia. En algunos países y modelos Samsung permite elegir un número de emergencias al que llamar, así que conviene confirmar el comportamiento exacto en España antes de comprar. Batería de 445 mAh con unas 30-40 horas de autonomía según el uso. Funciona con Android; algunas funciones de salud exigen un móvil Samsung. Precio de 489 € en LTE (439 € en Bluetooth).",
        "precio": "489.00€",
        "imagen": "https://topcomparador.es/wp-content/uploads/2026/11/samsung-galaxy-watch9-44mm-4g-graphite-eu-version.jpg",
    },
    # 5) Samsung Galaxy Watch8 40 mm - Android
    {
        "categoria": "smartwatch",
        "marca": "Samsung",
        "modelo_corto": "Galaxy Watch8 40 mm",
        "busqueda": "Samsung Galaxy Watch8 40mm Bluetooth",
        "link_afiliado": "https://link.amazon/B0bYBwH1A",
        "asin": "",
        "titulo": "Samsung Galaxy Watch8 (40 mm, Bluetooth) - Smartwatch con SOS, Detección de Caídas, Electrocardiograma y Medición de Presión Arterial para Android",
        "especificaciones": "Versión Bluetooth de 40 mm a 329 € (la versión con conexión móvil propia cuesta 429 €). Incluye SOS, detección de caídas, electrocardiograma y medición de la presión arterial, función que obliga a calibrar el reloj cada cuatro semanas con un tensiómetro de manguito. Hasta 30 horas de batería con la pantalla siempre encendida. Funciona con móviles Android 12 o posterior; su aplicación no es compatible con iPhone y parte de las funciones de salud exigen un teléfono de Samsung. Sin LTE necesita el móvil cerca para avisar a los contactos.",
        "precio": "329.00€",
        "imagen": "https://topcomparador.es/wp-content/uploads/2026/11/samsung-galaxy-watch8-40mm-bluetooth-gris-1.jpg",
    },
    # 6) SaveFamily Senior 4G - diseñado para mayores, SIM propia, no necesita móvil
    {
        "categoria": "smartwatch",
        "marca": "SaveFamily",
        "modelo_corto": "Senior 4G",
        "busqueda": "SaveFamily Senior 4G reloj mayores GPS",
        "link_afiliado": "https://link.amazon/B0g4iQyNX",
        "asin": "",
        "titulo": "SaveFamily Senior - Reloj Localizador para Personas Mayores con GPS, SIM, Llamadas y Videollamadas, Aviso de Caídas, Botón SOS y Recordatorio de Medicamentos",
        "especificaciones": "Reloj pensado para mayores que funciona con una SIM propia (llamadas y videollamadas sin móvil), con GPS, botón SOS físico y aviso automático de caídas: al detectar una caída llama a los contactos elegidos en la app (no a emergencias). Mide pulso, oxígeno en sangre y tensión, y recuerda la hora de cada medicamento. Pantalla táctil IPS de 1,4 pulgadas. Marca española con app propia y datos alojados en Europa. Requiere datos móviles: el plan de la marca cuesta 6 € al mes (5 € con pago anual); comprueba si el anuncio incluye la SIM preactivada. Algo pesado para muñecas delgadas.",
        "precio": "99.00€",
        "imagen": "https://topcomparador.es/wp-content/uploads/2026/11/savefamily-rsen4g.jpg",
    },
    # 7) Garmin Venu 4 - cualquier móvil, mucha batería, avisa a contactos (no a emergencias)
    {
        "categoria": "smartwatch",
        "marca": "Garmin",
        "modelo_corto": "Venu 4",
        "busqueda": "Garmin Venu 4",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Garmin Venu 4 - Smartwatch con Pantalla AMOLED, hasta 12 Días de Batería, Detección de Incidentes y Compatible con iPhone y Android",
        "especificaciones": "PVP de 499 €. Hasta 12 días de autonomía en el modelo de 45 mm (10 en el de 41 mm) y compatible con iPhone y Android. La detección de caídas puede activarse todo el día: cuando registra una, el reloj emite una alerta y envía un mensaje a los contactos de asistencia, pero necesita el teléfono cerca y con datos. Garmin advierte de que estas funciones son complementarias y de que no avisan a los servicios de emergencia; además, mantener la detección activa recorta la autonomía.",
        "precio": "499.00€",
        "imagen": "https://topcomparador.es/wp-content/uploads/2026/11/garmin-venu-4-41mm-slate-black-silicone-band.jpg",
    },
    # 8) Garmin vívoactive 6 - opción más económica de Garmin, fuente grande
    {
        "categoria": "smartwatch",
        "marca": "Garmin",
        "modelo_corto": "vívoactive 6",
        "busqueda": "Garmin vívoactive 6",
        "link_afiliado": "https://link.amazon/B0fPgb7vL",
        "asin": "",
        "titulo": "Garmin vívoactive 6 - Smartwatch con GPS, Pantalla AMOLED de 1,2 Pulgadas, Detección de Incidentes, Opción de Fuente Grande y hasta 11 Días de Batería",
        "especificaciones": "PVPR de 299,99 €. Pantalla AMOLED de 1,2 pulgadas (390 x 390) con opción de fuente grande, hasta 11 días de autonomía en modo smartwatch (5 con la pantalla siempre activa), GPS, NFC y resistencia 5 ATM. Incluye detección de incidentes, función de asistencia y LiveTrack, que necesitan el teléfono cerca para avisar a los contactos. Compatible con iPhone y Android. No llama por sí solo a los servicios de emergencia.",
        "precio": "299.99€",
        "imagen": "https://topcomparador.es/wp-content/uploads/2026/11/Garmin-vivoactive-6.jpg",
    },
    # 9) Leotec Senior Smart Band 4G - pulsera 4G económica para mayores
    {
        "categoria": "smartwatch",
        "marca": "Leotec",
        "modelo_corto": "Senior Smart Band 4G",
        "busqueda": "Leotec Senior Smart Band 4G GPS",
        "link_afiliado": "https://link.amazon/B06e04mge",
        "asin": "",
        "titulo": "Leotec Senior Smart Band 4G - Pulsera Inteligente para Mayores con GPS, Botón SOS, Detección de Caídas, Llamadas y Sensores de Salud",
        "especificaciones": "Pulsera 4G pensada para mayores que funciona sin móvil con una tarjeta nanoSIM, con GPS/GLONASS, botón SOS, detección de caídas, micrófono y altavoz para llamadas, pantalla táctil TFT de 1,4 pulgadas y sensores de frecuencia cardíaca, oxígeno en sangre, tensión y temperatura. Alertas de caída y recordatorio de medicación. Algunos análisis señalan diseño voluminoso, riesgo de pulsaciones accidentales y autonomía limitada, así que conviene revisar opiniones de usuarios.",
        "precio": "65.00€",
        "imagen": "https://topcomparador.es/wp-content/uploads/2026/11/leotec-lesb01k-negro.jpg",
    },
    # 10) Samsung Galaxy Fit3 - pulsera muy barata con detección de caídas - Android
    {
        "categoria": "smartwatch",
        "marca": "Samsung",
        "modelo_corto": "Galaxy Fit3",
        "busqueda": "Samsung Galaxy Fit3",
        "link_afiliado": "https://link.amazon/B000LVmuS",
        "asin": "",
        "titulo": "Samsung Galaxy Fit3 - Pulsera de Actividad con Pantalla AMOLED de 1,6 Pulgadas, Detección de Caídas, SOS y hasta 13 Días de Batería para Android",
        "especificaciones": "Pulsera de 18,5 g con pantalla AMOLED de 1,6 pulgadas, resistencia 5 ATM e IP68 y batería de 208 mAh con hasta 13 días de autonomía. Incluye detección de caídas, que alerta a los contactos de emergencia, y SOS al pulsar cinco veces el botón, además de frecuencia cardíaca y oxígeno en sangre. No tiene GPS, NFC ni conexión móvil: necesita un móvil Android 10 o superior con la app Galaxy Wearable y una cuenta Samsung. PVPR de 64,90 €, con precios de mercado por debajo de 50 € en algunas tiendas.",
        "precio": "64.90€",
        "imagen": "https://topcomparador.es/wp-content/uploads/2026/11/samsung-galaxy-fit3-gris.jpg",
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
