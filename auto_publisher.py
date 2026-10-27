import os
import json
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
productos_catalogo = [
    {
        "marca": "Huawei",
        "modelo_corto": "Watch GT 4 46mm",
        "busqueda": "Huawei Watch GT 4 46mm",
        "titulo": "Huawei Watch GT 4 - Reloj Inteligente 46 mm, Autonomía hasta 14 días, Análisis de arritmias por onda de pulso, GPS de alta precisión",
        "especificaciones": "Diseño geométrico elegante, pantalla AMOLED, autonomía de hasta 14 días, GPS de doble banda y 5 sistemas por satélite, llamadas Bluetooth, compatible con iOS y Android, más de 100 modos de entrenamiento.",
        "precio": "199.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/23/Huawei_Watch_GT_2_Smartwatch.jpg"
    },
    {
        "marca": "Apple",
        "modelo_corto": "Watch SE (2ª gen.)",
        "busqueda": "Apple Watch SE (2ª generación)",
        "titulo": "Apple Watch SE (2.ª gen.) - Reloj Inteligente con caja de aluminio, Detección de Accidentes, Entrenos avanzados y Control de Salud",
        "especificaciones": "Pantalla Retina OLED, chip S8 SiP súper rápido, detección de caídas y accidentes de tráfico, resistencia al agua hasta 50 metros, seguimiento del sueño y frecuencia cardíaca, compatible con ecosistema Apple.",
        "precio": "249.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/29/Coros_Pace_3.jpeg"
    },
    {
        "marca": "Samsung",
        "modelo_corto": "Galaxy Watch 6 40mm",
        "busqueda": "Samsung Galaxy Watch 6 40mm",
        "titulo": "Samsung Galaxy Watch 6 - Reloj inteligente 40mm, Monitorización del sueño, Sensor BioActive, Cristal de zafiro, Bisel estilizado",
        "especificaciones": "Pantalla Super AMOLED con cristal de zafiro, procesador Exynos W930, sistema Wear OS impulsado por Samsung, sensor BioActive para análisis de composición corporal (BIA) y ECG, resistencia IP68/5ATM.",
        "precio": "189.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/f/fb/Galaxy_Watch_7.jpg"
    },
    {
        "marca": "Xiaomi",
        "modelo_corto": "Redmi Watch 4",
        "busqueda": "Xiaomi Redmi Watch 4",
        "titulo": "Xiaomi Redmi Watch 4 - Reloj Inteligente Pantalla AMOLED 1.97\", Batería hasta 20 días, Cuadro de aleación de aluminio, Llamadas Bluetooth",
        "especificaciones": "Pantalla AMOLED ultragrande de 1,97 pulgada a 60 Hz, marco central de aleación de aluminio con corona giratoria, autonomía de hasta 20 días, más de 150 modos deportivos, monitorización de SpO2 y ritmo cardíaco.",
        "precio": "89.99€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Mi_Watch.jpg"
    },
    {
        "marca": "Amazfit",
        "modelo_corto": "GTS 4 Mini",
        "busqueda": "Amazfit GTS 4 Mini",
        "titulo": "Amazfit GTS 4 Mini - Smartwatch ultraligero, Pantalla AMOLED 1.65\", GPS con 5 sistemas, Batería 15 días, Monitorización de salud 24h",
        "especificaciones": "Diseño ultraestilizado de 9,1 mm y 19g de peso, posicionamiento por satélite integrado con 5 sistemas, autonomía de 15 días, medición de frecuencia cardíaca, SpO2 y estrés 24/7, evaluación de salud PAI.",
        "precio": "79.90€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/a/af/Amazfit_GTS_2_Mini.png"
    },
    {
        "marca": "Garmin",
        "modelo_corto": "Forerunner 55",
        "busqueda": "Garmin Forerunner 55",
        "titulo": "Garmin Forerunner 55 - Reloj para carreras con GPS integrado, Sugerencias de entrenamiento diario, Autonomía hasta 2 semanas",
        "especificaciones": "GPS integrado de alta precisión para atletismo y ciclismo, métricas de carrera avanzadas como Garmin Coach, ritmo PacePro, control de energía Body Battery, seguimiento diario de salud y hasta 14 días de batería.",
        "precio": "149.99€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/5/5e/Garmin_Vivoactive_4.jpg"
    },
    {
        "marca": "Xiaomi",
        "modelo_corto": "Smart Band 8 Pro",
        "busqueda": "Xiaomi Smart Band 8 Pro",
        "titulo": "Xiaomi Smart Band 8 Pro - Pulsómetro y reloj deportivo con pantalla AMOLED 1.74\", GPS integrado, Batería 14 días, Resistencia 5ATM",
        "especificaciones": "Diseño híbrido entre pulsera y smartwatch con panel AMOLED rectangular a 60 Hz, GNSS de 5 satélites integrado, monitorización médica continua, más de 150 modos deportivos y resistencia al agua 5 ATM.",
        "precio": "69.99€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/22/Xiaomi_Mi_Watch_S1_Active.jpg"
    },
    {
        "marca": "Amazfit",
        "modelo_corto": "Bip 5",
        "busqueda": "Amazfit Bip 5",
        "titulo": "Amazfit Bip 5 - Smartwatch Pantalla Ultra Grande 1.91\", Llamadas Bluetooth, Amazon Alexa integrado, GPS de 4 satélites",
        "especificaciones": "Pantalla táctil de alta resolución de 1,91\", soporte para llamadas de voz por Bluetooth y asistente Alexa integrado, más de 120 modos de entrenamiento con detección inteligente, hasta 10 días de autonomía.",
        "precio": "64.90€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/f/f0/Amazfit_GTR_2e.jpg"
    },
    {
        "marca": "Samsung",
        "modelo_corto": "Galaxy Fit3",
        "busqueda": "Samsung Galaxy Fit3",
        "titulo": "Samsung Galaxy Fit3 - Pulsera de actividad y reloj inteligente, Pantalla AMOLED 1.6\", Detección de caídas, Batería de 13 días",
        "especificaciones": "Pantalla AMOLED rectangular de 1,6 pulgadas con cuerpo de aluminio pulido, más de 100 ejercicios guardados, detección de caídas con llamada de emergencia SOS, análisis completo del sueño y resistencia 5ATM e IP68.",
        "precio": "49.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/5/52/Fitbit_Charge_5.jpg"
    },
    {
        "marca": "Huawei",
        "modelo_corto": "Watch FIT 3",
        "busqueda": "Huawei Watch FIT 3",
        "titulo": "Huawei Watch FIT 3 - Reloj Inteligente ultrafino 9.9 mm, Pantalla AMOLED 1.82\", Gestión de calorías, Batería hasta 10 días",
        "especificaciones": "Diseño ultradelgado en forma cuadrada con corona giratoria, pantalla AMOLED fluida de 1.82\", seguimiento preciso de salud y forma física Stay Fit, llamadas Bluetooth, compatible con Android e iOS.",
        "precio": "139.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/5/5e/TicWatch_Pro_3.jpg"
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

    # Prompt actualizado para que Gemini devuelva las especificaciones desglosadas en listas (arrays)
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
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    
    texto_respuesta = response.text.strip()
    if "```json" in texto_respuesta:
        texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0].strip()
    elif "```" in texto_respuesta:
        texto_respuesta = texto_respuesta.split("```")[1].split("```")[0].strip()
    
    inicio = texto_respuesta.find('{')
    fin = texto_respuesta.rfind('}')
    clean_json_str = texto_respuesta[inicio:fin+1]
    datos_ia = json.loads(clean_json_str)

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
                {render_bullets(s['pantalla'])}
              </ul>
            </td>
          </tr>
          
          <tr style="border: none; border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: bold; vertical-align: top; border: none; background-color: #f1f5f9;">🔋 Batería</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
                {render_bullets(s['bateria'])}
              </ul>
            </td>
          </tr>

          <tr style="border: none; border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: bold; vertical-align: top; border: none; background-color: #f1f5f9;">🌐 Conectividad</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
                {render_bullets(s['conectividad'])}
              </ul>
            </td>
          </tr>

          <tr style="border: none; border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: bold; vertical-align: top; border: none; background-color: #f1f5f9;">💓 Sensores</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
                {render_bullets(s['sensores'])}
              </ul>
            </td>
          </tr>

          <tr style="border: none; border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: bold; vertical-align: top; border: none; background-color: #f1f5f9;">🏃‍♂️ Deportes</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
                {render_bullets(s['deportes'])}
              </ul>
            </td>
          </tr>

          <tr style="border: none;">
            <td style="padding: 10px 12px; font-weight: bold; vertical-align: top; border: none; background-color: #f1f5f9; border-bottom-left-radius: 6px;">🛡️ Construcción</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
                {render_bullets(s['construccion'])}
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
            "spec_pantalla": str(s['pantalla']),
            "spec_bateria": str(s['bateria']),
            "spec_conectiv": str(s['conectividad']),
            "spec_sensores": str(s['sensores']),
            "spec_deportes": str(s['deportes']),
            "spec_cuerpo": str(s['construccion'])
        }
    }

    res = requests.post(wp_json_endpoint if 'wp_json_endpoint' in locals() else wp_endpoint, json=payload, auth=(WP_USER, WP_APP_PASSWORD))
    if res.status_code == 201:
        print(f"¡Publicación creada exitosamente para {producto['titulo']}!")
    else:
        print(f"Error ({res.text})")

if __name__ == "__main__":
    for item in productos_catalogo:
        procesar_y_publicar(item)
