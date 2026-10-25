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
    {
        "busqueda": "Huawei Watch GT 5",
        "titulo": "Huawei Watch GT 5 - Reloj Inteligente 46mm, Sistema TruSense, Navegación por mapa en muñeca, Autonomía de hasta 14 días, Compatible con iOS y Android",
        "especificaciones": "Diseño en acero inoxidable pulido, pantalla AMOLED de 1.43\", nuevo sistema de sensores TruSense para mediciones de salud ultraprecisas, posicionamiento de antena con algoritmo Sunflower para GPS mejorado, llamadas Bluetooth y resistencia 5 ATM.",
        "precio": "249.00€",
        "imagen": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Xiaomi Watch 2",
        "titulo": "Xiaomi Watch 2 - Smartwatch con Wear OS de Google, Procesador Snapdragon W5+ Gen 1, Pantalla AMOLED 1.43\", GPS Dual, Batería hasta 65h",
        "especificaciones": "Sistema operativo Wear OS con acceso completo a Google Play y Google Maps, arquitectura de procesador eficiente de 4 nm, caja de aleación de aluminio ligera, monitorización de salud 24/7 y más de 160 modos deportivos.",
        "precio": "139.00€",
        "imagen": "https://images.unsplash.com/photo-1544117519-31a4b719223d?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Garmin Vivoactive 5",
        "titulo": "Garmin Vivoactive 5 - Reloj Inteligente GPS con Pantalla AMOLED, Control de Energía Body Battery, Sesiones de Entrenamiento y Control del Sueño",
        "especificaciones": "Pantalla AMOLED brillante, análisis personalizado del sueño con sleep coach, sensor de salud Body Battery optimizado, más de 30 aplicaciones deportivas integradas (incluyendo modo silla de ruedas), pagos contactless Garmin Pay y hasta 11 días de autonomía.",
        "precio": "269.99€",
        "imagen": "https://images.unsplash.com/photo-1517502884422-41eaead166d4?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Amazfit Balance",
        "titulo": "Amazfit Balance - Smartwatch con Análisis de Composición Corporal, Asistente de IA Zepp Aura, Pantalla AMOLED 1.5\", GPS de Doble Banda",
        "especificaciones": "Medición de composición corporal (grasa corporal, masa muscular y agua), análisis de preparación física y mental diario, pantalla AMOLED de 1,5 pulgadas con 1.500 nits, altavoz y micrófono para llamadas, pagos NFC con Zepp Pay y batería de hasta 14 días.",
        "precio": "219.00€",
        "imagen": "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "COROS Pace 3",
        "titulo": "COROS Pace 3 - Reloj Deportivo Multideporte Ultraligero, GPS Multibanda, Pantalla Transflectiva, Sensor Frecuencia Cardíaca y SpO2, Batería 38h GPS",
        "especificaciones": "Peso pluma de solo 30 g, chip GPS de doble frecuencia para máxima precisión, pantalla Memory-in-Pixel siempre visible y legible bajo luz solar directa, altímetro barométrico, integración con plataformas de entrenamiento y hasta 17 días de uso diario.",
        "precio": "249.00€",
        "imagen": "https://images.unsplash.com/photo-1510017803434-a899398421b3?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Samsung Galaxy Watch 7",
        "titulo": "Samsung Galaxy Watch 7 - Reloj Inteligente 40mm, Procesador de 3nm, Sensor BioActive Mejorado, Análisis del Sueño con IA, GPS de Doble Frecuencia",
        "especificaciones": "Potente chip Exynos W1000 fabricado en 3 nm para máxima fluidez, sensor BioActive de 13 LED para precisión médica en frecuencia cardíaca y apnea del sueño, motor Wear OS impulsado por Samsung, puntuación de energía diaria por Galaxy AI y resistencia IP68/5ATM.",
        "precio": "229.00€",
        "imagen": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Xiaomi Watch S4",
        "titulo": "Xiaomi Watch S4 - Smartwatch con Bisel Intercambiable, Pantalla AMOLED 1.43\", HyperOS, GPS de 5 Sistemas, Resistencia 5 ATM",
        "especificaciones": "Diseño versátil con biseles e hilos de corona intercambiables por hardware, pantalla AMOLED ultrabrillante de 1.43\", sistema operativo optimizado Xiaomi HyperOS, llamadas Bluetooth con reducción de ruido, control por gestos en muñeca y 15 días de batería.",
        "precio": "149.99€",
        "imagen": "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Amazfit Active",
        "titulo": "Amazfit Active - Smartwatch Elegante y Ligero, Pantalla AMOLED 1.75\", Asistente de Entrenamiento Zepp Coach, Llamadas Bluetooth, GPS Integrado",
        "especificaciones": "Cuerpo ultraligero de aleación de aluminio, pantalla HD AMOLED de 1,75 pulgadas, planes de entrenamiento guiados por inteligencia artificial con Zepp Coach, reproductor de música integrado, llamadas de voz vía Bluetooth y autonomía de hasta 14 días.",
        "precio": "119.90€",
        "imagen": "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "Fitbit Charge 6",
        "titulo": "Fitbit Charge 6 - Pulsera Avanzada de Salud y Actividad Física, GPS Integrado, Controles de Google, ECG y Monitor de Estrés",
        "especificaciones": "Format compacto premium con integración nativa de apps de Google (Maps y Wallet), transmisión de frecuencia cardíaca a máquinas de gimnasio por Bluetooth, app de electrocardiograma (ECG), sensor EDA para gestión del estrés y 7 días de autonomía.",
        "precio": "159.95€",
        "imagen": "https://images.unsplash.com/photo-1544117519-31a4b719223d?w=600&auto=format&fit=crop&q=80"
    },
    {
        "busqueda": "TicWatch Pro 5 Enduro",
        "titulo": "TicWatch Pro 5 Enduro - Smartwatch Wear OS con Pantalla Ultra-Low-Power de Doble Capa, Snapdragon W5+ Gen 1, Cristal de Zafiro, Batería 90h",
        "especificaciones": "Tecnología de pantalla dual de 2 capas (AMOLED + FSTN ultrarreactiva) para ahorrar energía, cristal de zafiro altamente resistente a arañazos, procesador Snapdragon W5+ Gen 1 con Wear OS, brújula y altímetro integrados, y batería líder de hasta 90 horas en modo inteligente.",
        "precio": "299.99€",
        "imagen": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600&auto=format&fit=crop&q=80"
    }
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
