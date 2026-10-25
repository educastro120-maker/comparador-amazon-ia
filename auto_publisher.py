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
        "modelo_corto": "Watch GT 5",
        "busqueda": "Huawei Watch GT 5",
        "titulo": "Huawei Watch GT 5 - Reloj Inteligente 46mm, Sistema TruSense, Autonomía de hasta 14 días",
        "especificaciones": "Diseño en acero inoxidable pulido, pantalla AMOLED de 1.43\", nuevo sistema de sensores TruSense, GPS mejorado, llamadas Bluetooth y resistencia 5 ATM.",
        "precio": "249.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/23/Huawei_Watch_GT_2_Smartwatch.jpg"
    },
    {
        "marca": "Xiaomi",
        "modelo_corto": "Watch 2",
        "busqueda": "Xiaomi Watch 2",
        "titulo": "Xiaomi Watch 2 - Smartwatch con Wear OS de Google, Snapdragon W5+ Gen 1, Batería hasta 65h",
        "especificaciones": "Sistema Wear OS con Google Play, arquitectura de 4 nm, caja de aleación de aluminio, GPS Dual y más de 160 modos deportivos.",
        "precio": "139.00€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Mi_Watch.jpg"
    },
    {
        "marca": "Garmin",
        "modelo_corto": "Vivoactive 5",
        "busqueda": "Garmin Vivoactive 5",
        "titulo": "Garmin Vivoactive 5 - Reloj Inteligente GPS con Pantalla AMOLED, Control Body Battery",
        "especificaciones": "Pantalla AMOLED brillante, análisis personalizado del sueño, más de 30 apps deportivas, Garmin Pay y hasta 11 días de autonomía.",
        "precio": "269.99€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/5/5e/Garmin_Vivoactive_4.jpg"
    },
]

def procesar_y_publicar(producto):
    query_encoded = urllib.parse.quote_plus(producto['busqueda'])
    affiliate_link = f"https://www.amazon.es/s?k={query_encoded}&tag={AMAZON_TAG}"

    # Prompt actualizado para que Gemini devuelva también las especificaciones técnicas ordenadas
    prompt = f"""
    Actúa como analista de tecnología experto en Smartwatches y CRO.
    Analiza este producto:
    - Título: {producto['titulo']}
    - Especificaciones base: {producto['especificaciones']}
    - Precio: {producto['precio']}

    Devuelve ÚNICAMENTE un objeto JSON válido (y nada más que el JSON) con exactamente estas claves:
    "badge", "resumen_ejecutivo", 
    "specs" (un objeto JSON con estas 6 claves de texto exactas: "pantalla", "bateria", "conectividad", "sensores", "deportes", "construccion"),
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

    # HTML del artículo con la lista de especificaciones colocada antes de pros y contras
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

      <!-- Ficha de Especificaciones Ordenadas -->
      <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin: 20px 0;">
        <h3 style="color: #0f172a; margin-top: 0; font-size: 1.1em; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px;">⚙️ Ficha Técnica Resumida</h3>
        <ul style="list-style: none; padding: 0; margin: 0; font-size: 0.95em; color: #334155; line-height: 1.6;">
          <li style="padding: 6px 0; border-bottom: 1px solid #f1f5f9;"><strong>📺 Pantalla:</strong> {s['pantalla']}</li>
          <li style="padding: 6px 0; border-bottom: 1px solid #f1f5f9;"><strong>🔋 Batería:</strong> {s['bateria']}</li>
          <li style="padding: 6px 0; border-bottom: 1px solid #f1f5f9;"><strong>🌐 Conectividad:</strong> {s['conectividad']}</li>
          <li style="padding: 6px 0; border-bottom: 1px solid #f1f5f9;"><strong>💓 Sensores:</strong> {s['sensores']}</li>
          <li style="padding: 6px 0; border-bottom: 1px solid #f1f5f9;"><strong>🏃‍♂️ Deportes:</strong> {s['deportes']}</li>
          <li style="padding: 6px 0;"><strong>🛡️ Construcción:</strong> {s['construccion']}</li>
        </ul>
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
            # Guardamos también las especificaciones en metadatos individuales para el comparador
            "spec_pantalla": s['pantalla'],
            "spec_bateria": s['bateria'],
            "spec_conectiv": s['conectividad'],
            "spec_sensores": s['sensores'],
            "spec_deportes": s['deportes'],
            "spec_cuerpo": s['construccion']
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
