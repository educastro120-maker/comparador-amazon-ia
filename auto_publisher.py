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

def render_bullets(items):
    """Convierte una lista de strings en elementos de lista HTML con viñetas"""
    if isinstance(items, list):
        return "".join([f"<li style='margin-bottom: 4px;'>{item}</li>" for item in items])
    return f"<li>{items}</li>"

def procesar_y_publicar(producto):
    query_encoded = urllib.parse.quote_plus(producto['busqueda'])
    affiliate_link = f"https://www.amazon.es/s?k={query_encoded}&tag={AMAZON_TAG}"

    # PROMPT MEJORADO CON EXIGENCIA TÉCNICA RIGUROSA Y EN TIEMPO REAL
    prompt = f"""
    Actúa como un ingeniero de hardware y periodista tecnológico de élite especializado en análisis ultratécnicos de smartwatches deportivos y de aventura.
    
    INSTRUCCIÓN CRÍTICA: Debes navegar obligatoriamente por internet en tiempo real para extraer los datos de las especificaciones técnicas oficiales exactas, fichas de fabricante y análisis de laboratorio del dispositivo: "{producto['busqueda']}". 
    PROHIBIDO dar respuestas genéricas, vagas o rellenar con frases como "pantalla de alta definición". Tienes que proporcionar datos numéricos duros, tecnologías exactas, materiales específicos (ej. titanio grado 5, zafiro sintético, cerámica), resoluciones en píxeles, nits de brillo, miliamperios (mAh), sistemas de posicionamiento multibanda (L1+L5) y certificaciones oficiales (MIL-STD-810H, EN13319, IP68, 10 ATM).

    Datos base del producto:
    - Marca: {producto['marca']}
    - Modelo: {producto['modelo_corto']}
    - Título: {producto['titulo']}
    - Especificaciones orientativas: {producto['especificaciones']}
    - Precio de referencia: {producto['precio']}

    Tu objetivo es redactar un análisis técnico de nivel profesional absoluto. Devuelve ÚNICAMENTE un objeto JSON válido (sin texto adicional fuera del bloque JSON) con esta estructura exacta y claves:
    {{
      "badge": "Etiqueta comercial llamativa en mayúsculas (ej: REY DE LA ULTRARESISTENCIA, GPS TÁCTICO AVANZADO)",
      "resumen_ejecutivo": "Un análisis profundo y riguroso de 150 a 220 palabras redactado con tono experto. Detalla su rendimiento real sobre el terreno, tecnologías propietarias, público al que va enfocado y una conclusión argumentada de su valor en el mercado.",
      "specs": {{
        "pantalla": [
          "Tecnología exacta del panel (ej: AMOLED, MIP, Retina LTPO) y tipo de protección (cristal de zafiro sintético, Corning Gorilla Glass).",
          "Tamaño en pulgadas, resolución exacta en píxeles y densidad (ppi).",
          "Niveles de brillo pico máximo (nits) y brillo mínimo nocturno, además de tasa de refresco o modo Always-On."
        ],
        "bateria": [
          "Capacidad estimada de la celda en mAh y tipo de arquitectura de procesador o gestión energética.",
          "Autonomía real desglosada: modo smartwatch diario, modo ahorro y horas máximas con seguimiento GPS continuo.",
          "Tecnología de carga rápida inalámbrica o magnética y autonomía obtenida en pocos minutos de carga."
        ],
        "conectividad": [
          "Sistemas de posicionamiento satelital integrados (GPS de doble frecuencia L1/L5, GLONASS, Galileo, BeiDou, QZSS).",
          "Versión de conectividad inalámbrica (Bluetooth, Wi-Fi, NFC para pagos, eSIM/LTE o conectividad satelital de emergencia si aplica).",
          "Prestaciones de audio, altavoces, micrófonos integrados o sirenas de socorro en decibelios."
        ],
        "sensores": [
          "Sensores biométricos de salud: pulsómetro óptico de alta precisión, sensor ECG, SpO2 (oxígeno en sangre) y temperatura cutánea/corporal.",
          "Sensores de entorno y navegación: altímetro barométrico, brújula digital, giroscopio y acelerómetro de alta fuerza G.",
          "Funciones avanzadas de monitorización continua de estrés, recuperación (HRV) y sueño."
        ],
        "deportes": [
          "Modos deportivos especializados (perfiles de ultramaratón, trail, ciclismo, triatlón o certificaciones de buceo recreativo/técnico).",
          "Métricas avanzadas de rendimiento (potencia de carrera, dinámicas, VO2 máx, mapas topográficos offline giro a giro).",
          "Funciones de seguridad y retorno al punto de origen (Backtrack, llamadas SOS o detección automática de caídas/accidentes)."
        ],
        "construccion": [
          "Materiales exactos de fabricación de la caja (titanio de grado 5, acero inoxidable, polímero reforzado) y cubierta posterior (cerámica/zafiro).",
          "Certificaciones oficiales de resistencia al agua y polvo (ej: 10 ATM, norma ISO 22810, EN13319) y estándar militar de durabilidad (MIL-STD-810H).",
          "Dimensiones físicas exactas en milímetros, grosor y peso total del dispositivo en gramos."
        ]
      }},
      "pros": [
        "Primer punto fuerte altamente técnico y argumentado con datos concretos (mínimo 15 palabras)",
        "Segundo punto fuerte destacando rendimiento o materiales avanzados",
        "Tercer punto fuerte describiendo un beneficio clave para el usuario experto"
      ],
      "contras": [
        "Primer punto negativo o limitación explicada con rigor técnico",
        "Segundo aspecto mejorable que impacte de forma real en la experiencia de uso"
      ],
      "puntuacion": 9.4
    }}
    """

    print(f"🌐 Navegando y extrayendo especificaciones técnicas en tiempo real para: {producto['titulo']}...")
    
    max_intentos = 3
    response = None
    for intento in range(1, max_intentos + 1):
        try:
            config = types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.2, # Temperatura baja para priorizar datos técnicos reales y evitar inventiva
                max_output_tokens=3000
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

    # Extracción y limpieza segura del JSON devuelto por la IA
    datos_ia = None
    if response and hasattr(response, 'text') and response.text:
        texto_respuesta = response.text.strip()
        if "```json" in texto_respuesta:
            texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0].strip()
        elif "```" in texto_respuesta:
            texto_respuesta = texto_respuesta.split("```")[1].split("```")[0].strip()
        
        inicio = texto_respuesta.find('{')
        fin = texto_respuesta.rfind('}')
        
        if inicio != -1 and fin != -1:
            clean_json_str = texto_respuesta[inicio:fin+1]
            try:
                datos_ia = json.loads(clean_json_str)
            except json.JSONDecodeError as err:
                print(f"⚠️ Advertencia: Error analizando JSON en {producto['titulo']}: {err}")

    # Plantilla de respaldo robusta en caso de fallo excepcional de red
    if not datos_ia:
        print(f"💡 Aplicando plantilla de respaldo detallada para {producto['titulo']}...")
        datos_ia = {
            "badge": "ANÁLISIS TÉCNICO DESTACADO",
            "resumen_ejecutivo": f"{producto['titulo']} destaca en el mercado actual por integrar componentes de altas prestaciones enfocados tanto al rendimiento deportivo extremo como al seguimiento diario de la salud. Su estructura robusta y su optimización de software garantizan una experiencia fluida y fiable bajo cualquier circunstancia ambiental.",
            "specs": {
                "pantalla": ["Panel táctil de alta definición con excelente nitidez en exteriores.", "Tratamiento antirreflejos y óptima respuesta táctil bajo luz solar directa."],
                "bateria": ["Sistema de gestión energética optimizado para varios días de uso continuado.", "Soporte para modos avanzados de ahorro inteligente y carga rápida."],
                "conectividad": ["Conectividad Bluetooth de alta velocidad y posicionamiento satelital integrado.", "Soporte para sincronización de datos y notificaciones inteligentes en tiempo real."],
                "sensores": ["Sensores ópticos de última generación para frecuencia cardíaca y oxígeno en sangre.", "Monitoreo continuo de constantes vitales, descanso y gestión de estrés."],
                "deportes": ["Amplio catálogo de perfiles deportivos con métricas de rendimiento avanzadas.", "Registro automático de actividades y seguimiento cartográfico de rutas."],
                "construccion": ["Chasis ligero y resistente diseñado para soportar exigencias cotidianas.", "Certificación oficial de resistencia frente al agua, polvo y condiciones térmicas."]
            },
            "pros": ["Diseño robusto con materiales de alta calidad y gran durabilidad.", "Excelente precisión en el seguimiento de métricas deportivas y de salud.", "Interfaz intuitiva y altamente personalizable."],
            "contras": ["Autonomía variable al activar de forma simultánea todas las opciones de alta precisión y pantalla.", "Precio elevado acorde a su gama prémium."],
            "puntuacion": 9.1
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
