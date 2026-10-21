import os
import json
import requests
from google import genai

# ==========================================
# 1. LECTURA SEGURA DE CREDENCIALES
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WP_URL = os.environ.get("WP_URL").rstrip('/')
WP_USER = os.environ.get("WP_USER")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")

# Tu ID de afiliado de Amazon configurado
AMAZON_TAG = "topcomparad00-21"

# Configurar el cliente oficial de Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# 2. CATÁLOGO INTELIGENTE DE SMARTWATCHES
# ==========================================
productos_catalogo = [
    {
        "asin": "B0CQPY6L2V",
        "titulo": "Xiaomi Watch S3 - Smartwatch con esfera intercambiable, Pantalla AMOLED 1.43\", Llamadas Bluetooth, GNSS de doble banda",
        "especificaciones": "Pantalla AMOLED 1.43 pulgadas, marco intercambiable, batería de hasta 15 días, llamadas por Bluetooth, GPS de doble banda, resistencia 5 ATM, monitorización avanzada de frecuencia cardiaca y SpO2.",
        "precio": "149.00€",
        "imagen": "https://m.media-amazon.com/images/I/61S90T5vUJL._AC_SL1500_.jpg"
    },
    {
        "asin": "B0CM5W2K9F",
        "titulo": "Huawei Watch GT 4 - Reloj Inteligente 46 mm, Autonomía hasta 14 días, Análisis de arritmias por onda de pulso, GPS de alta precisión",
        "especificaciones": "Diseño geométrico elegante, pantalla AMOLED, autonomía de hasta 14 días, GPS de doble banda y 5 sistemas por satélite, llamadas Bluetooth, compatible con iOS y Android, más de 100 modos de entrenamiento.",
        "precio": "199.00€",
        "imagen": "https://m.media-amazon.com/images/I/61kR19106kL._AC_SL1500_.jpg"
    },
    {
        "asin": "B0CHX4D89W",
        "titulo": "Amazfit Balance Smartwatch Deportivo con IA, Zepp Coach, GPS de Doble Banda, Llamadas y Música, Pantalla AMOLED 1.5\"",
        "especificaciones": "Pantalla AMOLED HD de 1.5 pulgadas, entrenador personal Zepp Coach basado en IA, medición de composición corporal (grasa corporal, músculo), GPS hiperpreciso, pagos sin contacto Zepp Pay, autonomía de 14 días.",
        "precio": "229.00€",
        "imagen": "https://m.media-amazon.com/images/I/61aW15xIeIL._AC_SL1500_.jpg"
    }
]

def procesar_y_publicar(producto):
    affiliate_link = f"https://www.amazon.es/dp/{producto['asin']}?tag={AMAZON_TAG}&linkCode=ogi&th=1&psc=1"

    prompt = f"""
    Actúa como analista de tecnología experto en Smartwatches y CRO.
    Analiza este producto:
    - Título: {producto['titulo']}
    - Especificaciones: {producto['especificaciones']}
    - Precio: {producto['precio']}

    Devuelve ÚNICAMENTE un objeto JSON válido (y nada más que el JSON) con exactamente estas claves:
    "badge", "resumen_ejecutivo", "pros" (lista de 3 strings), "contras" (lista de 2 strings), "puntuacion" (número decimal).
    """

    print(f"Analizando con Gemini: {producto['titulo']}...")
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    
    # Limpieza robusta del JSON para evitar errores de sintaxis
    texto_respuesta = response.text.strip()
    if "```json" in texto_respuesta:
        texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0].strip()
    elif "```" in texto_respuesta:
        texto_respuesta = texto_respuesta.split("```")[1].split("```")[0].strip()
    
    # Asegurar que extraemos estrictamente desde la primera llave hasta la última
    inicio = texto_respuesta.find('{')
    fin = texto_respuesta.rfind('}')
    clean_json_str = texto_respuesta[inicio:fin+1]

    datos_ia = json.loads(clean_json_str)

    # Maquetación HTML profesional con imagen y conversión
    html_content = f"""
    <div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 24px; background-color: #ffffff; max-width: 750px; margin: 20px auto; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
      
      <div style="text-align: center; margin-bottom: 20px;">
        <img src="{producto['imagen']}" alt="{producto['titulo']}" style="max-height: 300px; width: auto; object-fit: contain; border-radius: 8px;" />
      </div>

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
        "status": "publish"
    }

    res = requests.post(wp_endpoint, json=payload, auth=(WP_USER, WP_APP_PASSWORD))
    if res.status_code == 201:
        print(f"¡Publicación creada exitosamente en WordPress para {producto['asin']}!")
    else:
        print(f"Error ({res.text})")

if __name__ == "__main__":
    for item in productos_catalogo:
        procesar_y_publicar(item)
