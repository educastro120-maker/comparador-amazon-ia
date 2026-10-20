import os
import json
import requests
import google.generativeai as genai

# ==========================================
# 1. LECTURA SEGURA DE CREDENCIALES
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WP_URL = os.environ.get("WP_URL").rstrip('/')
WP_USER = os.environ.get("WP_USER")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 2. CATÁLOGO / ENTRADA DE PRODUCTOS
# (En esta versión enviamos una lista de prueba. 
#  Más adelante la API de Amazon alimentará esta lista automáticamente)
# ==========================================
productos_nuevos = [
    {
        "asin": "B0CX12345",
        "titulo": "Xiaomi Redmi Watch 4 - Smartwatch con Pantalla AMOLED 1.97'', Batería de 20 días, GPS",
        "especificaciones": "Pantalla AMOLED 1.97 pulgadas, Tasa de refresco 60Hz, Marco de aleación de aluminio, Sensor FC/SpO2, +150 modos deportivos, Resistencia 5 ATM, Autonomía hasta 20 días.",
        "precio": "89.99€",
        "affiliate_link": "https://www.amazon.es/dp/B0CX12345?tag=tubrand-21" # Reemplaza con tu Tracking ID de Amazon
    }
]

def procesar_y_publicar(producto):
    prompt = f"""
    Actúa como analista de tecnología experto en Smartwatches y CRO (Optimización de Conversión).
    Analiza este producto:
    - Título: {producto['titulo']}
    - Especificaciones: {producto['especificaciones']}
    - Precio: {producto['precio']}

    Devuelve ÚNICAMENTE un formato JSON válido con las llaves exactas:
    "badge", "resumen_ejecutivo", "pros" (lista de 3), "contras" (lista de 2), "puntuacion" (número del 1 al 10).
    Sin markdown extra ni bloques de código.
    """

    print(f"Analizando con Gemini: {producto['titulo']}...")
    response = model.generate_content(prompt)
    clean_json_str = response.text.replace("```json", "").replace("```", "").strip()
    datos_ia = json.loads(clean_json_str)

    # Maquetación HTML de conversión para WordPress
    html_content = f"""
    <div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 24px; background-color: #ffffff; max-width: 750px; margin: 20px auto; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
      
      <div style="background-color: #ff9900; color: #fff; font-weight: bold; display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 0.85em; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px;">
        🔥 {datos_ia['badge']}
      </div>

      <h2 style="margin-top: 0; color: #111; font-size: 1.6em; line-height: 1.3;">{producto['titulo']}</h2>
      
      <p style="font-size: 1.1em; color: #444; line-height: 1.6;">
        {datos_ia['resumen_ejecutivo']}
      </p>

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
        <a href="{producto['affiliate_link']}" target="_blank" rel="sponsored nofollow" style="background-color: #ffa41c; color: #111; text-decoration: none; font-size: 1.2em; font-weight: bold; padding: 16px 32px; border-radius: 8px; border: 1px solid #ff8f00; display: inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
          Ver precio actualizado en Amazon 🛒
        </a>
      </div>
    </div>
    """

    # Envío a la API de WordPress
    wp_endpoint = f"{WP_URL}/wp-json/wp/v2/posts"
    payload = {
        "title": f"Análisis y Opinión: {producto['titulo']}",
        "content": html_content,
        "status": "publish" # Cambia a "draft" si prefieres que queden como borradores para revisarlos
    }

    res = requests.post(wp_endpoint, json=payload, auth=(WP_USER, WP_APP_PASSWORD))
    if res.status_code == 201:
        print(f"¡Publicación creada exitosamente en WordPress para {producto['asin']}!")
    else:
        print(f"Error ({res.status_code}): {res.text}")

# Ejecución
if __name__ == "__main__":
    for item in productos_nuevos:
        procesar_y_publicar(item)
