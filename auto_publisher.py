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

# Tu ID de afiliado de Amazon configurado
AMAZON_TAG = "topcomparad00-21"

# Configurar el cliente oficial de Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# 2. CATÁLOGO INTELIGENTE DE SMARTWATCHES
# ==========================================
productos_catalogo = [
[
    {
        "busqueda": "Xiaomi Redmi Watch 5 Lite",
        "titulo": "Xiaomi Redmi Watch 5 Lite - Smartwatch Pantalla AMOLED 1.96\", GPS Integrado, Llamadas Bluetooth, Resistencia 5ATM, Batería 18 días",
        "especificaciones": "Pantalla AMOLED brillante de 1,96 pulgadas, GPS autónomo compatible con 5 sistemas por satélite, llamadas de voz Bluetooth con cancelación de ruido de dos micrófonos, seguimiento de salud continuo 24/7 y más de 140 modos deportivos.",
        "precio": "49.99€",
        "imagen": "https://images.unsplash.com/photo-1544117519-31a4b719223d?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "CMF Watch Pro by Nothing",
        "titulo": "CMF Watch Pro - Smartwatch Pantalla AMOLED 1.96\", Llamadas Bluetooth con IA, GPS Integrado, Monitorización de Salud 24/7, IP68",
        "especificaciones": "Diseño icónico y minimalista en aleación de aluminio, pantalla AMOLED fluida de 1,96\" a 58 fps con 600 nits, llamadas claras por Bluetooth con tecnología de reducción de ruido por IA, GPS multisistema y hasta 13 días de autonomía.",
        "precio": "69.00€",
        "imagen": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Amazfit Pop 3S",
        "titulo": "Amazfit Pop 3S - Reloj Inteligente Pantalla HD AMOLED 1.96\", Llamadas Bluetooth, Monitor SpO2 y Ritmo Cardíaco, Marco Metálico",
        "especificaciones": "Pantalla rectangular AMOLED con función Always-on Display, cuerpo de acero inoxidable con cristal curvo 2.5D, micrófono y altavoz para llamadas de voz por Bluetooth, más de 100 modos de entrenamiento y 12 días de batería.",
        "precio": "54.90€",
        "imagen": "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Haylou Solar Plus RT3",
        "titulo": "Haylou Solar Plus RT3 - Smartwatch Pantalla AMOLED 1.43\", Llamadas Bluetooth, Monitor de Frecuencia Cardíaca y Estrés, Bisel de Metal",
        "especificaciones": "Pantalla circular AMOLED de alta resolución 466x466 px, cuerpo metálico pulido con corona navegatoria, llamadas de teléfono Bluetooth, monitorización de oxígeno en sangre, seguimiento del sueño y 105 modos de deporte.",
        "precio": "45.99€",
        "imagen": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Redmi Watch 3 Active",
        "titulo": "Xiaomi Redmi Watch 3 Active - Reloj Inteligente LCD 1.83\", Llamadas por Bluetooth, 100+ Modos Deportivos, Resistencia al Agua 5 ATM",
        "especificaciones": "Pantalla LCD ultragrande de 1,83 pulgadas con interfaz personalizable, llamadas telefónicas con un solo toque por Bluetooth, diseño curvo con acabado metalizado, monitor de SpO2 y ritmo cardíaco continuo, batería hasta 12 días.",
        "precio": "39.99€",
        "imagen": "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Mibro GS Pro",
        "titulo": "Mibro GS Pro - Smartwatch Deportivo Pantalla AMOLED 1.43\", GPS Dual, Caja de Acero 316L, Sensor de Salud de 9 Ejes, 5ATM",
        "especificaciones": "Cuerpo ultrarresistente fabricado en acero inoxidable 316L, pantalla AMOLED redonda de alta definición, GPS satelital dual integrado con altímetro y barómetro, llamadas por Bluetooth, resistencia al agua de 50 metros y 20 días de batería.",
        "precio": "69.90€",
        "imagen": "https://images.unsplash.com/photo-1517502884422-41eaead166d4?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Blackview W50",
        "titulo": "Blackview W50 - Reloj Inteligente Rugerizado, Pantalla 1.39\" HD, Llamadas Bluetooth, Resistencia IP68 y Antiarañazos, Linterna Integrada",
        "especificaciones": "Construcción rugerizada de alta durabilidad resistente a golpes y caídas, cristal PANDA antiarañazos, soporte para responder llamadas vía Bluetooth, brújula, linterna LED integrada, 100+ modos deportivos y autonomía de 5 días de uso intenso.",
        "precio": "35.99€",
        "imagen": "https://images.unsplash.com/photo-1510017803434-a899398421b3?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Realme Watch 3",
        "titulo": "Realme Watch 3 - Smartwatch Pantalla 1.8\", Llamadas Bluetooth con Cancelación de Ruido por IA, Más de 110 Modos Deportivos",
        "especificaciones": "Pantalla de 1,8 pulgadas con relación pantalla-cuerpo del 67.5%, altavoz potente con algoritmo de IA para llamadas sin interferencias de viento o ruido, seguimiento continuo de salud (SpO2, pulso y sueño) y resistencia IP68.",
        "precio": "49.00€",
        "imagen": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Honor Watch Fit",
        "titulo": "Honor Watch Fit - Reloj Deportivo Pantalla AMOLED 1.64\", Entrenador Animado 3D, GPS Integrado, Monitor SpO2 y Batería de 10 días",
        "especificaciones": "Pantalla AMOLED rectangular con ajuste automático de brillo, 12 cursos de entrenamiento animados con demostraciones rápidas en pantalla, GPS integrado para carreras, monitor de salud 24/7 y carga rápida de batería.",
        "precio": "59.90€",
        "imagen": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Ksix Core 3",
        "titulo": "Ksix Core 3 - Smartwatch Pantalla AMOLED 1.43\", Llamadas Bluetooth, Asistente de Voz, Control de Salud Completo, IP67",
        "especificaciones": "Pantalla AMOLED redonda táctil con colores vívidos y gran contraste, micrófono y altavoz integrados para llamadas y comandos de asistente de voz (Siri/Google Assistant), control de música y disparo de cámara remoto, más de 100 modos de deporte.",
        "precio": "42.50€",
        "imagen": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80"
    }
]
]

def procesar_y_publicar(producto):
    # Generar enlace de búsqueda optimizado y 100% funcional con tu Tag de afiliado
    query_encoded = urllib.parse.quote_plus(producto['busqueda'])
    affiliate_link = f"https://www.amazon.es/s?k={query_encoded}&tag={AMAZON_TAG}"

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
    
    texto_respuesta = response.text.strip()
    if "```json" in texto_respuesta:
        texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0].strip()
    elif "```" in texto_respuesta:
        texto_respuesta = texto_respuesta.split("```")[1].split("```")[0].strip()
    
    inicio = texto_respuesta.find('{')
    fin = texto_respuesta.rfind('}')
    clean_json_str = texto_respuesta[inicio:fin+1]

    datos_ia = json.loads(clean_json_str)

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
        print(f"¡Publicación creada exitosamente en WordPress para {producto['titulo']}!")
    else:
        print(f"Error ({res.text})")

if __name__ == "__main__":
    for item in productos_catalogo:
        procesar_y_publicar(item)
