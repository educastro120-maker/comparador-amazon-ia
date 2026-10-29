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
        "marca": "Google",
        "modelo_corto": "Pixel Watch 4 45mm",
        "busqueda": "Google Pixel Watch 4 45mm",
        "titulo": "Google Pixel Watch 4 - Pantalla Actua AMOLED de 3.000 nits, Ecosistema Google y Fitbit, Formato 45mm, Chip Snapdragon W5+",
        "especificaciones": "Pantalla Actua AMOLED sin bordes de 3.000 nits, procesador Snapdragon W5+ Gen 2, métricas avanzadas de preparación y carga cardiovascular guiadas por Fitbit AI, integración con Google Maps offline y Wallet.",
        "precio": "449.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/a/af/Amazfit_GTS_2_Mini.png"
    },
{
        "marca": "Suunto",
        "modelo_corto": "Vertical 2",
        "busqueda": "Suunto Vertical 2 Titanium Solar",
        "titulo": "Suunto Vertical 2 Titanium Solar - Smartwatch Deportivo Outdoor con Carga Solar, Pantalla AMOLED, Bisel Titanio Grado 5, Mapas Offline",
        "especificaciones": "Pantalla AMOLED brillante combinada con cristal de zafiro solar, bisel de titanio de grado 5, mapas topográficos offline de máxima precisión dual con soporte GNSS de 5 satélites y autonomía de hasta 60 horas con GPS activo.",
        "precio": "799.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/f/fb/Galaxy_Watch_7.jpg"
    },
{
        "marca": "Apple",
        "modelo_corto": "Watch Ultra 4",
        "busqueda": "Apple Watch Ultra 4",
        "titulo": "Apple Watch Ultra 4 - Caja de Titanio de 49 mm, Chip S11, Pantalla LTPO3 de 3.000 nits, Conectividad Satelital, Resistencia 100 m",
        "especificaciones": "Caja de titanio de grado 5 fabricada en 3D, pantalla LTPO3 OLED de gran ángulo de visión, procesador S11 con sistema de monitoreo continuo de salud 24/7, conexión satelital para emergencias y hasta 84 horas de batería en modo ahorro.",
        "precio": "899.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/23/Huawei_Watch_GT_2_Smartwatch.jpg"
    },
    {
        "marca": "Garmin",
        "modelo_corto": "fēnix 9 Pro",
        "busqueda": "Garmin fēnix 9 Pro",
        "titulo": "Garmin fēnix 9 Pro - Smartwatch Multideporte GPS Premium, Pantalla AMOLED 3.000 nits, Cristal de Zafiro, Micrófono y Altavoz, Linterna LED",
        "especificaciones": "Pantalla AMOLED brillante de 3.000 nits con bisel de titanio, resistencia militar STD-810H y sumergible a 100m, altavoz/micrófono para llamadas y comandos de voz, mapas topo mundiales y autonomía de hasta 31 días.",
        "precio": "1099.99€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Mi_Watch.jpg"
    },
    {
        "marca": "Samsung",
        "modelo_corto": "Galaxy Watch Ultra 2",
        "busqueda": "Samsung Galaxy Watch Ultra 2",
        "titulo": "Samsung Galaxy Watch Ultra 2 - Smartwatch 47mm Titanio, Chip Snapdragon Wear Elite, GPS Dual, Pantalla 5.000 nits, Galaxy AI",
        "especificaciones": "Caja de titanio de grado 4, procesador Snapdragon Wear Elite con 64 GB de almacenamiento, pantalla AMOLED de 5.000 nits de brillo, GPS de frecuencia dual, sirena de socorro de 86 dB y batería de 800 mAh.",
        "precio": "699.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/f/f0/Amazfit_GTR_2e.jpg"
    },
    {
        "marca": "Huawei",
        "modelo_corto": "Watch Ultimate 2",
        "busqueda": "Huawei Watch Ultimate 2",
        "titulo": "Huawei Watch Ultimate 2 - Reloj Inteligente de Metal Líquido con Circonio, Sumergible 100m, Pantalla AMOLED Zafiro, Asistente de Salud AI",
        "especificaciones": "Cuerpo de metal líquido a base de circonio de altísima dureza, bisel de cerámica nanocristalina y cristal de zafiro, ordenador de buceo profesional certificado para 100m, posicionamiento Sunflower GPS y 14 días de batería.",
        "precio": "799.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/29/Coros_Pace_3.jpeg"
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
    Eres un periodista experto en tecnología y analista de wearables para blogs de afiliados de alta conversión (CRO).
    
    INSTRUCCIÓN OBLIGATORIA: Busca en internet información real y actualizada de las especificaciones oficiales y análisis técnicos sobre el dispositivo "{producto['busqueda']}".
    
    Datos base del producto:
    - Marca: {producto['marca']}
    - Modelo: {producto['modelo_corto']}
    - Título: {producto['titulo']}
    - Especificaciones básicas: {producto['especificaciones']}
    
    Genera un análisis técnico exhaustivo, riguroso y detallado basándote en datos reales actualizados.
    
    REQUISITOS DEL JSON:
    1. "badge": Una etiqueta corta y llamativa (Ej: "Mejor Calidad-Precio", "Top Gama Alta", "Máxima Autonomía").
    2. "resumen_ejecutivo": Un análisis completo y detallado (de entre 120 y 180 palabras) enfocado en la experiencia de uso real, puntos fuertes, público objetivo y por qué vale la pena comprarlo frente a sus competidores directos.
    3. "specs": Objeto con 6 categorías técnicas. Cada categoría DEBE contener entre 2 y 4 viñetas (strings) detalladas con datos técnicos específicos recuperados de internet:
       - "pantalla": Tecnología de panel (AMOLED/OLED/TFT), tamaño exacto en pulgadas, resolución de píxeles, nits de brillo máximo y funciones (Always On, etc.).
       - "bateria": Capacidad en mAh, autonomía estimada en uso normal e intenso, tiempo y tipo de carga.
       - "conectividad": Versión de Bluetooth, conectividad Wi-Fi, sistemas de posicionamiento GPS (banda dual/sistemas soportados), NFC y soporte de llamadas.
       - "sensores": Sensores ópticos y de salud (ritmo cardíaco, SpO2, ECG, temperatura, acelerómetro, giroscopio, barómetro, etc.).
       - "deportes": Número de modos deportivos, entrenadores IA, métricas avanzadas (VO2 Max, tiempo de recuperación, carga de entrenamiento).
       - "construccion": Materiales del bisel y caja (titanio/aluminio/acero), resistencia al agua (5ATM/IP68/100m) y dimensiones/peso aproximado.
    4. "pros": Lista de exactamente 3 puntos fuertes concretos y bien explicados.
    5. "contras": Lista de exactamente 2 puntos a mejorar o limitaciones reales.
    6. "puntuacion": Número decimal entre 7.0 y 10.0 basado en su relación calidad-precio.
    """

    print(f"🌐 Buscando información en tiempo real y analizando con Gemini: {producto['titulo']}...")
    
    # Esquema estricto de respuesta JSON para garantizar la sintaxis perfecta
    json_schema = {
        "type": "OBJECT",
        "properties": {
            "badge": {"type": "STRING"},
            "resumen_ejecutivo": {"type": "STRING"},
            "specs": {
                "type": "OBJECT",
                "properties": {
                    "pantalla": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "bateria": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "conectividad": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "sensores": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "deportes": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "construccion": {"type": "ARRAY", "items": {"type": "STRING"}}
                },
                "required": ["pantalla", "bateria", "conectividad", "sensores", "deportes", "construccion"]
            },
            "pros": {"type": "ARRAY", "items": {"type": "STRING"}},
            "contras": {"type": "ARRAY", "items": {"type": "STRING"}},
            "puntuacion": {"type": "NUMBER"}
        },
        "required": ["badge", "resumen_ejecutivo", "specs", "pros", "contras", "puntuacion"]
    }

    max_intentos = 3
    response = None
    for intento in range(1, max_intentos + 1):
        try:
            # Habilitamos Google Search Grounding y la salida JSON estructurada
            config = types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                response_mime_type="application/json",
                response_schema=json_schema,
                temperature=0.3
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

    # Parseo directo y seguro gracias a la respuesta forzada en JSON
    datos_ia = None
    if response and hasattr(response, 'text') and response.text:
        try:
            datos_ia = json.loads(response.text.strip())
        except json.JSONDecodeError as err:
            print(f"⚠️ Error parseando JSON estructurado para {producto['titulo']}: {err}")

    # Plantilla por defecto de seguridad sólo en caso de fallo crítico de red
    if not datos_ia:
        print(f"💡 Aplicando plantilla de respaldo para {producto['titulo']}...")
        datos_ia = {
            "badge": "Destacado Calidad-Precio",
            "resumen_ejecutivo": producto['titulo'] + " ofrece una experiencia completa con pantalla de alta resolución, seguimiento avanzado de actividad física y excelente autonomía.",
            "specs": {
                "pantalla": ["Pantalla táctil de alta definición con excelente nitidez en exteriores."],
                "bateria": ["Batería optimizada para varios días de uso continuo sin interrupciones."],
                "conectividad": ["Sincronización Bluetooth rápida con smartphone y seguimiento GPS."],
                "sensores": ["Sensores ópticos para medición continua de pulso y calidad del sueño."],
                "deportes": ["Múltiples perfiles deportivos y registro automático de actividad."],
                "construccion": ["Chasis resistente al agua y polvo con acabado ergonómico."]
            },
            "pros": ["Gran relación calidad-precio", "Buena autonomía de batería", "Pantalla de clara visibilidad"],
            "contras": ["Opciones de personalización limitadas según el SO", "Sin pagos NFC en algunas plataformas"],
            "puntuacion": 8.5
        }

    s = datos_ia['specs']

    # HTML optimizado del artículo para WordPress
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

      <!-- Ficha Técnica Resumida -->
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
