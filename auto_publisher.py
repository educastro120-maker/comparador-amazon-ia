import os
import json
import time
import requests
import urllib.parse
from google import genai
from google.genai import types

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
# 2. CATÁLOGO DE SMARTWATCHES
# ==========================================
productos_catalogo = [
    {
        "marca": "Garmin",
        "modelo_corto": "fēnix 8 Solar",
        "busqueda": "Garmin fēnix 8 Solar",
        "titulo": "Garmin fēnix 8 Solar - Smartwatch Multideporte GPS Premium, Cristal de Zafiro Carga Solar, Micrófono y Altavoz, Linterna LED",
        "especificaciones": "Pantalla Memory-in-Pixel con tecnología de carga solar Solar Sapphire, bisel de titanio de grado 5, resistencia militar MIL-STD-810H y botones inductivos estancos aptos para buceo (40m). Incorpora micrófono/altavoz para llamadas y comandos por voz, linterna LED y hasta 48 días de autonomía en modo reloj.",
        "precio": "1099.99€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Mi_Watch.jpg"
    },
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
        "especificaciones": "Caja de titanio de grado 4 con grado de resistencia 10 ATM, certificación militar MIL-STD-810H y resistencia a temperaturas extremas (-20 °C a 55 °C). Procesador de 3 nm para máxima fluidez, pantalla AMOLED de 3.000 nits, sirena de socorro de 86 dB y funciones de entrenamiento com Galaxy AI.",
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

def render_bullets(items):
    """Convierte una lista de strings en elementos de lista HTML con viñetas"""
    if isinstance(items, list):
        return "".join([f"<li style='margin-bottom: 4px;'>{item}</li>" for item in items])
    return f"<li>{items}</li>"

def procesar_y_publicar(producto):
    query_encoded = urllib.parse.quote_plus(producto['busqueda'])
    affiliate_link = f"https://www.amazon.es/s?k={query_encoded}&tag={AMAZON_TAG}"

    # PROMPT EXHAUSTIVO CON EXIGENCIA DE DATOS NUMÉRICOS Y TÉCNICOS ESPECÍFICOS
    prompt = f"""
    Actúa estrictamente como un ingeniero de hardware, especialista en tecnología wearable y periodista tecnológico experto en smartwatches de gama alta.
    Utiliza obligatoriamente la herramienta de búsqueda web en tiempo real para investigar a fondo y extraer los DATOS TÉCNICOS, MÉTRICAS Y CIFRAS REALES (horas exactas de batería, número exacto de modos deportivos, resolución de pantalla, brillo en nits, profundidad en metros) del dispositivo: "{producto['busqueda']}".
    
    Datos base de referencia:
    - Marca: {producto['marca']}
    - Modelo: {producto['modelo_corto']}
    - Título oficial: {producto['titulo']}
    - Specs base orientativas: {producto['especificaciones']}
    - Precio de referencia: {producto['precio']}

    REQUISITOS OBLIGATORIOS PARA LA GENERACIÓN DEL JSON (MÁXIMO NIVEL DE DETALLE Y RIGOR):
    1. PROHIBIDO dar respuestas vagas o generales (como "batería de larga duración" o "múltiples deportes"). DEBES APORTAR CIFRAS Y DATOS CONCRETOS:
       - En Pantalla: Tipo exacto de panel, tamaño en pulgadas, resolución exacta en píxeles y brillo máximo en nits.
       - En Batería: Días exactos de autonomía en modo smartwatch y horas exactas continuas con GPS activo (ej. "Hasta 40 horas continuas con GPS").
       - En Conectividad: Sistemas GNSS de doble frecuencia (ej. L1 + L5, GPS, GLONASS, Galileo), NFC, Bluetooth y soporte eSIM/LTE si aplica.
       - En Sensores: Sensores biométricos (frecuencia cardíaca, SpO2, ECG, temperatura) y barómetro/brújula.
       - En Deportes: El número exacto o aproximado de modos deportivos (ej. "Más de 100 modalidades"), profundidad exacta de inmersión en metros (ej. "Sumergible hasta 40m o 100m con certificación EN13319") y mapas offline.
       - En Construcción: Material exacto de la caja (ej. Titanio de grado 5), bisel, certificaciones militares (MIL-STD-810H), resistencia (ATM) y dimensiones/peso exactos.
    2. NUNCA mezcles conceptos (está prohibido poner precios o enlaces dentro de las especificaciones de batería o pantalla).
    3. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla estrictamente con esta estructura de claves:
    {{
      "badge": "ETIQUETA COMERCIAL CORTA EN MAYÚSCULAS",
      "resumen_ejecutivo": "Análisis técnico profundo de 150 a 220 palabras explicando sus prestaciones, materiales, rendimiento y valor en el mercado.",
      "specs": {{
        "pantalla": ["Detalle técnico con tamaño y panel exacto", "Resolución en píxeles y densidad", "Brillo máximo en nits y tipo de cristal protector"],
        "bateria": ["Autonomía exacta en días para uso normal/ahorro", "Autonomía exacta en horas con GPS continuo activo", "Tecnología de carga y tiempo estimado de 0 a 100%"],
        "conectividad": ["Sistemas de posicionamiento GNSS (doble frecuencia y satélites soportados)", "Conectividad inalámbrica (Bluetooth, Wi-Fi, NFC y eSIM si procede)", "Funciones de llamada o altavoz/micrófono"],
        "sensores": ["Sensores de salud y biometría (frecuencia cardíaca, SpO2, ECG, temperatura cutánea)", "Sensores de entorno y orientación (altímetro barométrico, brújula, giroscopio)"],
        "deportes": ["Número exacto de modos deportivos y perfiles de entrenamiento especializados", "Profundidad de inmersión y certificación de buceo/multideporte", "Mapas offline y navegación avanzada"],
        "construccion": ["Material exacto de caja, bisel y fondo (ej. titanio grado 5, zafiro)", "Certificaciones de resistencia (MIL-STD-810H, ATM)", "Dimensiones de caja y peso sin correa"]
      }},
      "pros": ["Punto fuerte técnico 1 muy detallado y específico", "Punto fuerte técnico 2 muy detallado", "Punto fuerte técnico 3 muy detallado"],
      "contras": ["Punto débil 1 detallado", "Punto débil 2 detallado"],
      "puntuacion": 9.4
    }}
    """

    print(f"🌐 Navegando y extrayendo datos cuantitativos exhaustivos en tiempo real para: {producto['titulo']}...")
    
    max_intentos = 3
    response = None
    for intento in range(1, max_intentos + 1):
        try:
            config = types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.1,  # Temperatura muy baja para máxima precisión factual
                response_mime_type="application/json"
            )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=config
            )
            break
        except Exception as e:
            print(f"⚠️ Intento {intento}/{max_intentos} fallido por error en la API: {e}")
            if intento < max_intentos:
                time.sleep(5)
            else:
                print(f"❌ Imposible analizar {producto['titulo']} tras {max_intentos} intentos.")

    # Extracción del JSON garantizado por la API
    datos_ia = None
    if response and hasattr(response, 'text') and response.text:
        try:
            datos_ia = json.loads(response.text.strip())
        except json.JSONDecodeError as err:
            print(f"⚠️ Advertencia: Error analizando JSON directo en {producto['titulo']}: {err}")

    # Respaldo inteligente enriquecido con métricas estimadas y datos técnicos reales del catálogo
    if not datos_ia:
        print(f"💡 Aplicando respaldo técnico estructurado con métricas para {producto['titulo']}...")
        datos_ia = {
            "badge": f"ANÁLISIS TÉCNICO {producto['marca'].upper()}",
            "resumen_ejecutivo": f"{producto['titulo']} representa una opción sobresaliente dentro del mercado actual de dispositivos wearables. Diseñado para ofrecer un rendimiento fluido y constante, combina materiales de alta durabilidad con una completa suite de sensores orientados al deporte de alto rendimiento y la salud. Su optimización de hardware lo convierte en un compañero ideal para entrenamientos exigentes.",
            "specs": {
                "pantalla": [f"Panel optimizado de alta visibilidad en exteriores para el modelo {producto['modelo_corto']}.", f"Especificación base integrada: {producto['especificaciones']}."],
                "bateria": ["Sistema de gestión energética de alta eficiencia adaptado para uso prolongado.", "Autonomía optimizada para soporte de seguimiento GPS multideporte continuo."],
                "conectividad": ["Soporte para sincronización de datos y conectividad inalámbrica de alta velocidad.", "Sistemas de posicionamiento geográfico por satélite de alta precisión integrados."],
                "sensores": ["Monitoreo continuo de frecuencia cardíaca óptica y saturación de oxígeno (SpO2).", "Sensores barométricos y de movimiento para métricas de altitud y entorno."],
                "deportes": ["Perfiles multideporte avanzados con más de 30 a 100 modalidades especializadas según el perfil.", "Resistencia certificada para entornos de alta exigencia al aire libre."],
                "construccion": [f"Estructura robusta de alta gama desarrollada por {producto['marca']}.", f"Detalle de construcción base: {producto['especificaciones']}"]
            },
            "pros": [
                f"Construcción robusta y materiales de primera línea respaldados por la ingeniería de {producto['marca']}.",
                "Excelente precisión en el registro de métricas deportivas y de salud.",
                "Interfaz optimizada para visibilidad y usabilidad bajo condiciones extremas."
            ],
            "contras": [
                "Dimensiones y peso adaptados al formato deportivo robusto.",
                "Inversión económica acorde a la gama alta de la categoría."
            ],
            "puntuacion": 9.2
        }

    s = datos_ia['specs']

    # HTML profesional y optimizado para WordPress
    html_content = f"""
    <div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 24px; background-color: #ffffff; max-width: 750px; margin: 20px auto; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
      
      <div style="text-align: center; margin-bottom: 20px;">
        <img src="{producto['imagen']}" alt="{producto['titulo']}" style="max-height: 280px; width: auto; object-fit: contain; border-radius: 8px;" />
      </div>

      <div style="background-color: #ff9900; color: #fff; font-weight: bold; display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 0.85em; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px;">
        🔥 {datos_ia['badge']}
      </div>

      <h2 style="margin-top: 0; color: #111; font-size: 1.6em; line-height: 1.3;">{producto['titulo']}</h2>
      
      <p style="font-size: 1.05em; color: #333; line-height: 1.7; text-align: justify;">
        {datos_ia['resumen_ejecutivo']}
      </p>

      <!-- Ficha Técnica Detallada -->
      <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin: 20px 0;">
        <h3 style="color: #0f172a; margin-top: 0; font-size: 1.1em; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; margin-bottom: 12px;">⚙️ Ficha Técnica Detallada</h3>
        
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
