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
productos_catalogo = [
   {
        "marca": "Apple",
        "modelo_corto": "Watch Ultra 2",
        "busqueda": "Apple Watch Ultra 2",
        "titulo": "Apple Watch Ultra 2 - Caja de titanio de 49 mm, Pantalla de 3.000 nits, GPS de doble frecuencia, Resistencia al agua 100 m",
        "especificaciones": "Caja de titanio aeroespacial, pantalla Retina OLED de hasta 3.000 nits con cristal de zafiro, chip S9 SiP con doble toque, GPS multibanda de precisión, profundímetro para buceo y batería de hasta 72 horas.",
        "precio": "899.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/23/Huawei_Watch_GT_2_Smartwatch.jpg"
    },
    {
        "marca": "Garmin",
        "modelo_corto": "fēnix 8 AMOLED",
        "busqueda": "Garmin fēnix 8 AMOLED 47mm",
        "titulo": "Garmin fēnix 8 - Smartwatch multideporte premium, Pantalla AMOLED brillante, Micrófono y altavoz integrados, Linterna LED",
        "especificaciones": "Pantalla AMOLED con lente de zafiro y bisel de titanio, resistencia militar STD-810 y 10 ATM, comandos de voz y llamadas, linterna LED integrada y mapas topográficos mundiales avanzados.",
        "precio": "999.99€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Mi_Watch.jpg"
    },
    {
        "marca": "Samsung",
        "modelo_corto": "Galaxy Watch Ultra",
        "busqueda": "Samsung Galaxy Watch Ultra",
        "titulo": "Samsung Galaxy Watch Ultra - Smartwatch 47mm Titanio, GPS Dual, Resistencia 10 ATM e IP68, Procesador 3nm, Galaxy AI",
        "especificaciones": "Diseño en titanio de grado 4 con resistencia extrema, procesador de 3 nm con Wear OS, GPS de frecuencia dual, análisis de salud impulsado por Galaxy AI y hasta 100 horas en ahorro de energía.",
        "precio": "699.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/f/f0/Amazfit_GTR_2e.jpg"
    },
    {
        "marca": "Huawei",
        "modelo_corto": "Watch Ultimate",
        "busqueda": "Huawei Watch Ultimate",
        "titulo": "Huawei Watch Ultimate - Reloj Inteligente de Metal Líquido con Circonio, Sumergible 100m, Pantalla AMOLED Zafiro",
        "especificaciones": "Cuerpo de metal líquido con base de circonio, bisel cerámico y cristal de zafiro, sumergible hasta 100 metros con ordenador de buceo profesional, GPS de 5 sistemas y autonomía de hasta 14 días.",
        "precio": "749.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/29/Coros_Pace_3.jpeg"
    },
    {
        "marca": "Garmin",
        "modelo_corto": "Forerunner 965",
        "busqueda": "Garmin Forerunner 965",
        "titulo": "Garmin Forerunner 965 - Reloj deportivo para Triatlón y Running, Pantalla AMOLED 1.4\", Bisel de Titanio, Mapas Integrados",
        "especificaciones": "Pantalla táctil AMOLED de 1,4\", bisel ultraligero de titanio, métricas avanzadas de predisposición para entrenar, mapas TopoActive a todo color y GPS multibanda SatIQ.",
        "precio": "649.99€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/22/Xiaomi_Mi_Watch_S1_Active.jpg"
    },
    {
        "marca": "Polar",
        "modelo_corto": "Grit X2 Pro",
        "busqueda": "Polar Grit X2 Pro",
        "titulo": "Polar Grit X2 Pro - Reloj multideporte outdoor con Pantalla AMOLED Zafiro, Estándar Militar MIL-STD-810H, Biometría Elixir",
        "especificaciones": "Diseñado para deportes extremos con lente de cristal de zafiro y carcasa de titanio, mapas topográficos offline y sensor de biometría avanzada Polar Elixir con ECG y SpO2.",
        "precio": "749.90€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/5/5e/Garmin_Vivoactive_4.jpg"
    },
    {
        "marca": "Suunto",
        "modelo_corto": "Race Titanium",
        "busqueda": "Suunto Race Titanium",
        "titulo": "Suunto Race Titanium - Smartwatch Deportivo con Pantalla AMOLED, Bisel de Titanio, Navegación Offline",
        "especificaciones": "Pantalla AMOLED con cristal de zafiro, bisel de titanio de grado 5, navegación de rutas offline con precisión dual y hasta 40 horas de autonomía con GPS activo.",
        "precio": "549.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/f/fb/Galaxy_Watch_7.jpg"
    },
    {
        "marca": "Google",
        "modelo_corto": "Pixel Watch 3 45mm",
        "busqueda": "Google Pixel Watch 3 45mm",
        "titulo": "Google Pixel Watch 3 - Pantalla Actua AMOLED 2.000 nits, Ecosistema Google y Fitbit, Formato 45mm",
        "especificaciones": "Pantalla Actua AMOLED de alta luminosidad, chip Snapdragon W5 Gen 1, integración nativa con Google Assistant y Wallet, además de métricas avanzadas de recuperación de Fitbit.",
        "precio": "449.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/a/af/Amazfit_GTS_2_Mini.png"
    },
    {
        "marca": "Amazfit",
        "modelo_corto": "T-Rex 3",
        "busqueda": "Amazfit T-Rex 3",
        "titulo": "Amazfit T-Rex 3 - Smartwatch Táctico Rugerizado, Pantalla AMOLED 2.000 nits, Mapas Offline, 27 Días Batería",
        "especificaciones": "Cuerpo con bisel de acero inoxidable resistente de -30°C a +70°C, pantalla AMOLED de 1,5\", mapas topográficos giro a giro y procesamiento con IA mediante Zepp Flow.",
        "precio": "279.90€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/5/52/Fitbit_Charge_5.jpg"
    },
    {
        "marca": "OnePlus",
        "modelo_corto": "Watch 2",
        "busqueda": "OnePlus Watch 2",
        "titulo": "OnePlus Watch 2 - Smartwatch con Arquitectura Dual-Engine, Wear OS 4, Cristal de Zafiro, Autonomía 100h",
        "especificaciones": "Arquitectura de doble procesador independiente para máximo rendimiento y eficiencia, cristal de zafiro 2.5D, caja de acero inoxidable y hasta 100 horas de batería en modo inteligente.",
        "precio": "299.00€",
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
                print(f"⚠️ Advertencia: JSON mal formado por la IA en {producto['titulo']}: {err}")

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
