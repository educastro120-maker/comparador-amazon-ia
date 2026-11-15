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
# Top 10 smartwatches con mejor batería (datos recopilados en noviembre de 2026)
# Ordenados por la cifra de autonomía más alta que declara el fabricante en modo reloj inteligente
# (con carga solar cuando el reloj la tiene). Son cifras "hasta": dependen del uso y de la luz solar.
#
# IMPORTANTE ANTES DE PUBLICAR:
#  - "link_afiliado" y "asin" están vacíos a propósito: hay que obtenerlos desde tu cuenta de Afiliados.
#  - "imagen" está vacío: sube una foto correcta a tu biblioteca de medios y pega la URL.
#  - "titulo" es descriptivo; ajústalo si quieres que coincida exactamente con el anuncio de Amazon.
#  - Los precios son orientativos (PVP o precio de mercado reciente) y cambian a menudo.

productos_catalogo = [
    # 1) DXOMARK 175 - número 1 del ranking mundial
    {
        "categoria": "smartphone",
        "marca": "Huawei",
        "modelo_corto": "Pura 80 Ultra",
        "busqueda": "HUAWEI Pura 80 Ultra 16GB 512GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "HUAWEI Pura 80 Ultra - Smartphone con Cámara Principal de 1 Pulgada y Teleobjetivo Dual, 16 GB + 512 GB, Pantalla LTPO OLED de 6,8 Pulgadas",
        "especificaciones": "Primero del ranking mundial de cámaras de DXOMARK con 175 puntos, más de un año después de su lanzamiento. Cámara principal de 1 pulgada con teleobjetivo dual en un sistema de cuatro cámaras, pantalla LTPO OLED de 6,8 pulgadas a 120 Hz, 16 GB de RAM, 512 GB de almacenamiento y batería de 5.170 mAh. Llegó a España en octubre de 2025 a 1.499 € y se ha visto a 1.299 € en la tienda de Huawei en junio de 2026. Como móvil de Huawei no incluye los servicios de Google, así que conviene comprobar que funcionan las aplicaciones que usas; compruébalo también si lo vende Amazon.es con garantía española.",
        "precio": "1299.00€",
        "imagen": "",
    },
    # 2) DXOMARK 173 - novedad de noviembre de 2026
    {
        "categoria": "smartphone",
        "marca": "Motorola",
        "modelo_corto": "Signature 27",
        "busqueda": "Motorola Signature 27",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Motorola Signature 27 - Smartphone Ultra Premium con Cámara Gold Label DXOMARK, Snapdragon 8 Elite Extreme Gen 6, Batería de 7.000 mAh y Pantalla AMOLED de 165 Hz",
        "especificaciones": "Lanzado el 5 de noviembre de 2026, DXOMARK le dio 173 puntos y su etiqueta Gold, la mejor cámara de un móvil lanzado en 2026 según la prueba, y el segundo puesto mundial, a solo dos puntos del Huawei Pura 80 Ultra; el Signature original (enero de 2026) había obtenido 164. DXOMARK destaca una fotografía de aspecto natural, zoom versátil y buen vídeo. Incluye pantalla AMOLED de 165 Hz, Snapdragon 8 Elite Extreme Gen 6, batería de 7.000 mAh con carga de 90 W y carga inalámbrica de 50 W, y Android 17 con siete años de actualizaciones. Ya se puede reservar en España a un precio estimado de 1.595 €; al ser tan reciente, aún hay pocas pruebas independientes y el precio puede variar.",
        "precio": "1595.00€",
        "imagen": "",
    },
    # 3) DXOMARK 172 - el mejor iPhone
    {
        "categoria": "smartphone",
        "marca": "Apple",
        "modelo_corto": "iPhone 18 Pro",
        "busqueda": "Apple iPhone 18 Pro 256GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Apple iPhone 18 Pro (256 GB) - Cámara Pro Fusion de 48 MP con Apertura Variable, Teleobjetivo 4x, Chip A20 Pro y Pantalla de 6,3 Pulgadas",
        "especificaciones": "Tercero del ranking de DXOMARK con 172 puntos. Tres cámaras traseras Fusion de 48 MP: la principal de 24 mm estrena apertura variable entre f/1.48 y f/4.0, la ultra gran angular cubre 120 grados y el teleobjetivo de tetraprisma ofrece zoom óptico 4x (equivalente a 100 mm). Pantalla OLED LTPO de 6,3 pulgadas con ProMotion de hasta 120 Hz, chip A20 Pro e iOS 27. Disponible en España desde el 18 de septiembre de 2026 desde 1.469 € (256 GB); sube 150 € respecto al iPhone 17 Pro. El iPhone 18 Pro Max parte de 1.619 €.",
        "precio": "1469.00€",
        "imagen": "",
    },
    # 4) DXOMARK 171 - el mejor zoom probado por DXOMARK según Digital Trends
    {
        "categoria": "smartphone",
        "marca": "vivo",
        "modelo_corto": "X300 Pro",
        "busqueda": "vivo X300 Pro 16GB 512GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "vivo X300 Pro 5G (16 GB + 512 GB) - Smartphone con Teleobjetivo ZEISS APO de 200 MP, Cámara Principal Gimbal de 50 MP y Vídeo 4K a 120 fps con Dolby Vision",
        "especificaciones": "Cuarto del ranking de DXOMARK con 171 puntos, y según Digital Trends tiene la mejor calidad de zoom que DXOMARK ha probado. Cámara principal de 50 MP (Sony LYT-828, 1/1,28 pulgadas, f/1.57) con estabilización tipo gimbal, teleobjetivo ZEISS APO de 200 MP (sensor de 1/1,4 pulgadas, f/2.67) y ultra gran angular de 50 MP; cámara frontal de 50 MP con autofocus y vídeo 4K a 120 fps con Dolby Vision. Procesador Dimensity 9500 y compatibilidad con el kit extensor de teleobjetivo ZEISS de 2,35x. Llegó a España a 1.399 € (16 GB + 512 GB) en noviembre de 2025, así que conviene comprobar si hoy está más barato.",
        "precio": "1399.00€",
        "imagen": "",
    },
    # 5) DXOMARK 170 - empatado en quinto lugar
    {
        "categoria": "smartphone",
        "marca": "OPPO",
        "modelo_corto": "Find X9 Ultra",
        "busqueda": "OPPO Find X9 Ultra 12GB 512GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "OPPO Find X9 Ultra (12 GB + 512 GB) - Smartphone con Doble Cámara Hasselblad de 200 MP, Teleobjetivo 10x de 50 MP, Vídeo 8K y Batería de 7.050 mAh",
        "especificaciones": "Empatado en el quinto puesto de DXOMARK con 170 puntos. Es la primera vez que OPPO vende en España un modelo Ultra. Doble cámara Hasselblad de 200 MP, teleobjetivo Hasselblad de 50 MP con zoom óptico 10x (calidad óptica 20x y hasta 120x digital), cámara True Color con 24 canales espectrales, vídeo 8K y batería de 7.050 mAh con carga de 100 W. Es de los pocos con dos teleobjetivos capaces. Precio oficial en España de 1.699 € (12 GB + 512 GB); el kit Hasselblad con teleconvertidor de 300 mm es opcional y cuesta 599 € aparte.",
        "precio": "1699.00€",
        "imagen": "",
    },
    # 6) DXOMARK 170 - empatado en quinto lugar
    {
        "categoria": "smartphone",
        "marca": "vivo",
        "modelo_corto": "X300 Ultra",
        "busqueda": "vivo X300 Ultra 16GB 1TB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "vivo X300 Ultra (16 GB + 1 TB) - Smartphone con Triple Cámara ZEISS de 200 MP, Super Teleobjetivo, Vídeo 4K a 120 fps y Snapdragon 8 Elite Gen 5",
        "especificaciones": "Empatado en el quinto puesto de DXOMARK con 170 puntos. Cámara principal de 200 MP (Sony LYTIA 901, 1/1,12 pulgadas, f/1.85, lente ZEISS), super teleobjetivo ZEISS de 200 MP con zoom digital de hasta 100x, ultra gran angular de 50 MP con 123,4 grados y vídeo 4K a 120 fps con captura Log de 10 bits. Procesador Snapdragon 8 Elite Gen 5, 16 GB de RAM y 1 TB de almacenamiento. Se vende en España desde finales de marzo de 2026 a 2.399 €, en un pack con los accesorios de cámara, así que es el más caro de la lista.",
        "precio": "2399.00€",
        "imagen": "",
    },
    # 7) DXOMARK 168 - el mejor para "apuntar y disparar"
    {
        "categoria": "smartphone",
        "marca": "Google",
        "modelo_corto": "Pixel 11 Pro XL",
        "busqueda": "Google Pixel 11 Pro XL 256GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Google Pixel 11 Pro XL (256 GB) - Smartphone Android con Cámara Pixel Pro, Fotografía Computacional y Funciones de IA de Google, 12 GB de RAM",
        "especificaciones": "168 puntos en DXOMARK y, según Tech Advisor, el mejor móvil para apuntar y disparar, con pantalla muy brillante y hasta dos días de batería. Destaca por la fotografía computacional y las funciones de edición con IA más que por el hardware. Precio de lanzamiento en Europa desde 1.399 € con 256 GB y 12 GB de RAM, unos 100 € más que su predecesor. Es el único de la lista de Google; el Pixel 11 Pro (6,3 pulgadas) parte de 1.199 €.",
        "precio": "1399.00€",
        "imagen": "",
    },
    # 8) DXOMARK 168 (mismo sistema de cámaras que el iPhone 17 Pro) - opción más barata de Apple
    {
        "categoria": "smartphone",
        "marca": "Apple",
        "modelo_corto": "iPhone 17 Pro Max",
        "busqueda": "Apple iPhone 17 Pro Max 256GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Apple iPhone 17 Pro Max (256 GB) - Smartphone con Sistema de Triple Cámara de 48 MP y Cámara Frontal de 18 MP Center Stage",
        "especificaciones": "El iPhone 17 Pro obtuvo 168 puntos en DXOMARK y el sistema de cámaras del 17 Pro Max es el mismo; además lidera la subpuntuación de vídeo de DXOMARK. Cámara principal Fusion de 48 MP (24 mm, f/1.78, estabilización por desplazamiento de sensor), cámara frontal de 18 MP con Center Stage y color muy consistente, aunque no es el más ambicioso en fotografía. Tras salir el iPhone 18 Pro Max pasó de 1.469 a 1.319 € en Amazon, su mínimo histórico en ese momento. Es la forma más barata de tener cámara Apple de gama alta.",
        "precio": "1319.00€",
        "imagen": "",
    },
    # 9) DXOMARK 166 - Leica
    {
        "categoria": "smartphone",
        "marca": "Xiaomi",
        "modelo_corto": "17 Ultra",
        "busqueda": "Xiaomi 17 Ultra",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Xiaomi 17 Ultra - Smartphone con Óptica Leica Summilux, Sensor Principal de Gran Tamaño y Teleobjetivo para Retrato y Zoom a Distancia, con Kit Fotográfico",
        "especificaciones": "166 puntos en DXOMARK, aunque Xataka lo elige como su mejor propuesta para fotografía sin kits adicionales: un sistema de cámaras muy versátil con óptica Leica Summilux, un sensor principal que consideran posiblemente el mejor de su categoría y un teleobjetivo pensado para retrato y fotografía a distancia. Según Xataka se vende en España en pack con kit fotográfico y su precio parte de 2.259 €, así que es de los más caros. Comprueba si ya existe una versión sin kit más barata.",
        "precio": "2259.00€",
        "imagen": "",
    },
    # 10) Fuera del top 10 de DXOMARK, pero el más vendido y el mejor vídeo en Android
    {
        "categoria": "smartphone",
        "marca": "Samsung",
        "modelo_corto": "Galaxy S26 Ultra",
        "busqueda": "Samsung Galaxy S26 Ultra 256GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Samsung Galaxy S26 Ultra (256 GB) - Smartphone con Cámara Principal de 200 MP, Doble Teleobjetivo 3x y 5x, Pantalla QHD+ de 6,9 Pulgadas y Galaxy AI",
        "especificaciones": "En la clasificación global de DXOMARK queda en torno al puesto 20, pero es el único de los mejores que se vende en tienda en todas partes y, según Xataka, tiene el mejor vídeo de Android y cámaras consistentes aunque poco ambiciosas. Cámara principal de 200 MP con f/1.4, ultra gran angular de 50 MP y dos teleobjetivos (10 MP con zoom óptico 3x y 50 MP con zoom óptico 5x), pantalla QHD+ de 6,9 pulgadas, Snapdragon 8 Elite Gen 5 y batería de 5.000 mAh. PVP de 1.549 € (256 GB) en España; se ha visto a 1.098,99 € en PcComponentes, así que puede ser la mejor compra de la lista por precio.",
        "precio": "1549.00€",
        "imagen": "",
    },
  
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
        
        # Limpieza robusta de bloques de código Markdown
        if "```json" in texto_respuesta:
            texto_respuesta = texto_respuesta.split("```json")[1].split("```")[0].strip()
        elif "```" in texto_respuesta:
            texto_respuesta = texto_respuesta.split("```")[1].split("```")[0].strip()
        
        # Intentar parsear el JSON directamente o buscar llaves
        try:
            datos_ia = json.loads(texto_respuesta)
        except json.JSONDecodeError:
            inicio = texto_respuesta.find('{')
            fin = texto_respuesta.rfind('}')
            if inicio != -1 and fin != -1:
                clean_json_str = texto_respuesta[inicio:fin+1]
                try:
                    datos_ia = json.loads(clean_json_str)
                except json.JSONDecodeError as err:
                    print(f"⚠️ Error crítico de JSON en {producto['titulo']}: {err}")
                    print(f"Respuesta recibida de la IA:\n{texto_respuesta}")

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
