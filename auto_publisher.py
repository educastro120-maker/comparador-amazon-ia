import os
import json
import time
from datetime import datetime
import requests
import urllib.parse
from google import genai
from google.genai import types

# ==========================================
# 1. LECTURA SEGURA DE CREDENCIALES
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
WP_URL = os.environ.get("WP_URL", "").rstrip('/')
WP_USER = os.environ.get("WP_USER", "").strip()
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "").strip()

AMAZON_TAG = "topcomparad00-21"

if not GEMINI_API_KEY:
    raise ValueError("❌ ERROR CRÍTICO: La variable de entorno GEMINI_API_KEY está vacía en GitHub Secrets.")

client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# 2. CATÁLOGO MULTI-CATEGORÍA
# ==========================================
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
]


def formatear_item_negrita(texto):
    """Si un item tiene formato 'Etiqueta: Valor', pone la etiqueta en negrita automáticamente."""
    if ":" in texto:
        partes = texto.split(":", 1)
        return f"<strong>{partes[0].strip()}:</strong> {partes[1].strip()}"
    return texto


def render_bullets(items):
    """Convierte una lista de strings en elementos de lista HTML con viñetas y etiquetas en negrita."""
    if isinstance(items, list):
        return "".join([f"<li style='margin-bottom: 5px;'>{formatear_item_negrita(item)}</li>" for item in items])
    return f"<li>{formatear_item_negrita(str(items))}</li>"


def obtener_o_crear_categoria(nombre_cat_input):
    """Busca la categoría en WordPress por su nombre (ej: 'Smartphones'). Si no existe, la crea."""
    nombre_categoria = nombre_cat_input.capitalize()
    if nombre_categoria.lower() == 'smartphone':
        nombre_categoria = 'Smartphones'
    elif nombre_categoria.lower() == 'smartwatch':
        nombre_categoria = 'Smartwatches'

    cat_endpoint = f"{WP_URL}/wp-json/wp/v2/categories"
    
    try:
        # Buscar si ya existe
        res = requests.get(cat_endpoint, params={"search": nombre_categoria}, auth=(WP_USER, WP_APP_PASSWORD), timeout=15)
        if res.status_code == 200:
            categorias = res.json()
            for cat in categorias:
                if cat['name'].lower() == nombre_categoria.lower():
                    return cat['id']
        
        # Si no existe, crearla
        payload_cat = {"name": nombre_categoria}
        res_crear = requests.post(cat_endpoint, json=payload_cat, auth=(WP_USER, WP_APP_PASSWORD), timeout=15)
        if res_crear.status_code == 201:
            return res_crear.json()['id']
    except Exception as e:
        print(f"   ⚠️ Advertencia al gestionar categoría en WordPress: {e}")
    
    return None


def llamar_gemini_con_respaldo(prompt):
    """Intenta generar el JSON con gemini-3.8-flash y usa gemini-3.5-flash-lite como respaldo."""
    modelos_a_probar = ['gemini-3.8-flash', 'gemini-3.5-flash-lite']
    
    for modelo in modelos_a_probar:
        for intento in range(1, 3):
            try:
                print(f"   🤖 Llamando a {modelo} (Intento {intento})...")
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.3,
                        max_output_tokens=4096,
                    )
                )
                if response and response.text:
                    return json.loads(response.text)
            except Exception as e:
                print(f"   ⚠️ Fallo con {modelo} (Intento {intento}): {type(e).__name__} -> {e}")
                time.sleep(3)
    return None


def procesar_y_publicar(producto):
    asin = producto.get('asin', '').strip()
    if asin:
        affiliate_link = f"https://www.amazon.es/dp/{asin}?tag={AMAZON_TAG}"
    else:
        query_encoded = urllib.parse.quote_plus(producto['busqueda'])
        affiliate_link = f"https://www.amazon.es/s?k={query_encoded}&tag={AMAZON_TAG}"
    
    categoria_str = producto.get('categoria', 'smartwatch').lower()
    imagen_url = producto.get('imagen', '').strip()
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")

    # --- PROMPTS EXHAUSTIVOS PARA FICHA TÉCNICA DETALLADA ---
    if categoria_str == 'smartphone':
        prompt = f"""
        Actúa como un analista experto en hardware móvil, SEO técnico y CRO para una web comparadora de productos de Amazon.
        Analiza en máxima profundidad este smartphone basándote en los datos aportados y tu conocimiento técnico del modelo exacto:
        - Marca y Modelo: {producto['marca']} {producto['modelo_corto']}
        - Título: {producto['titulo']}
        - Especificaciones base: {producto['especificaciones']}
        - Precio: {producto['precio']}

        REGLAS ESTRICTAS DE CONTENIDO (MUY IMPORTANTE):
        1. No hagas resúmenes cortos. Queremos una Ficha Técnica Detallada y exhaustiva donde cada categoría de "specs" tenga entre 5 y 8 viñetas individuales.
        2. Usa SIEMPRE el formato "Característica: Dato técnico exacto" en cada viñeta (ej. "Panel: LTPO AMOLED de 6,8 pulgadas", "Tasa de refresco: 1-120 Hz adaptativos", etc.). Nunca dejes datos genéricos si se conocen las especificaciones reales del modelo.
        3. El "resumen_ejecutivo" debe ser un párrafo rico, experto y persuasivo de unas 90-120 palabras.
        4. Incluye exactamente 6 Pros detallados y 4 Contras detallados, todos con formato "Título corto: Explicación detallada".

        Devuelve ÚNICAMENTE un objeto JSON válido con esta estructura exacta:
        {{
            "badge": "ETIQUETA CORTA EN MAYÚSCULAS (ej: REFERENCIA EN FOTOGRAFÍA MÓVIL)",
            "resumen_ejecutivo": "Párrafo extenso, técnico y persuasivo de 90-120 palabras.",
            "specs": {{
                "pantalla": [
                    "Panel: ...",
                    "Tamaño: ...",
                    "Resolución: ...",
                    "Tasa de refresco: ...",
                    "Brillo máximo: ...",
                    "Protección: ..."
                ],
                "rendimiento": [
                    "Procesador: ...",
                    "Arquitectura / GPU: ...",
                    "Memoria RAM: ...",
                    "Sistema operativo: ...",
                    "Inteligencia Artificial: ...",
                    "Refrigeración: ..."
                ],
                "camaras": [
                    "Sensor principal: ...",
                    "Teleobjetivo(s): ...",
                    "Ultra gran angular: ...",
                    "Cámara frontal: ...",
                    "Grabación de vídeo: ...",
                    "Óptica / Procesado: ..."
                ],
                "bateria": [
                    "Capacidad: ...",
                    "Carga rápida por cable: ...",
                    "Carga inalámbrica: ...",
                    "Carga inversa: ...",
                    "Autonomía estimada: ..."
                ],
                "almacenamiento": [
                    "Capacidad interna: ...",
                    "Tecnología de memoria: ...",
                    "Ampliación microSD: ...",
                    "Versiones disponibles: ..."
                ],
                "conectividad": [
                    "Redes móviles: ...",
                    "Wi-Fi: ...",
                    "Bluetooth: ...",
                    "NFC: ...",
                    "Navegación / GPS: ...",
                    "Puerto y audio: ...",
                    "Resistencia y construcción: ..."
                ]
            }},
            "pros": [
                "Ventaja 1: Explicación detallada...",
                "Ventaja 2: Explicación detallada...",
                "Ventaja 3: Explicación detallada...",
                "Ventaja 4: Explicación detallada...",
                "Ventaja 5: Explicación detallada...",
                "Ventaja 6: Explicación detallada..."
            ],
            "contras": [
                "Desventaja 1: Explicación detallada...",
                "Desventaja 2: Explicación detallada...",
                "Desventaja 3: Explicación detallada...",
                "Desventaja 4: Explicación detallada..."
            ],
            "puntuacion": 9.4
        }}
        """
    else:
        prompt = f"""
        Actúa como un analista experto en wearables, deporte, SEO técnico y CRO para una web comparadora de productos de Amazon.
        Analiza en máxima profundidad este smartwatch basándote en los datos aportados y tu conocimiento técnico del modelo exacto:
        - Marca y Modelo: {producto['marca']} {producto['modelo_corto']}
        - Título: {producto['titulo']}
        - Especificaciones base: {producto['especificaciones']}
        - Precio: {producto['precio']}

        REGLAS ESTRICTAS DE CONTENIDO (MUY IMPORTANTE):
        1. Queremos una Ficha Técnica Detallada y exhaustiva donde cada categoría de "specs" tenga entre 5 y 8 viñetas individuales.
        2. Usa SIEMPRE el formato "Característica: Dato técnico exacto" en cada viñeta (ej. "Panel: AMOLED", "Tamaño: 1.4 pulgadas", "Resolución: 454x454 píxeles", "Autonomía reloj: Hasta 16 días", etc.).
        3. El "resumen_ejecutivo" debe ser un párrafo rico, experto y persuasivo de unas 90-120 palabras.
        4. Incluye exactamente 6 Pros detallados y 4 Contras detallados, todos con formato "Título corto: Explicación detallada".

        Devuelve ÚNICAMENTE un objeto JSON válido con esta estructura exacta:
        {{
            "badge": "ETIQUETA CORTA EN MAYÚSCULAS (ej: REFERENCIA MULTIDEPORTE PREMIUM)",
            "resumen_ejecutivo": "Párrafo extenso, técnico y persuasivo de 90-120 palabras.",
            "specs": {{
                "pantalla": [
                    "Panel: ...",
                    "Tamaño: ...",
                    "Resolución: ...",
                    "Protección: ...",
                    "Siempre activa: ...",
                    "Control: ..."
                ],
                "bateria": [
                    "Autonomía reloj: ...",
                    "Autonomía GPS: ...",
                    "Carga solar / rápida: ...",
                    "Modo ahorro: ...",
                    "Tipo de carga: ..."
                ],
                "conectividad": [
                    "Wi-Fi: ...",
                    "NFC: ...",
                    "GNSS: ...",
                    "Almacenamiento: ...",
                    "Audio: ...",
                    "Llamadas: ...",
                    "Mapas: ..."
                ],
                "sensores": [
                    "Frecuencia cardíaca: ...",
                    "Oxígeno en sangre: ...",
                    "ECG: ...",
                    "Temperatura: ...",
                    "Altímetro: ...",
                    "Profundidad: ...",
                    "Otros: ..."
                ],
                "deportes": [
                    "Perfiles: ...",
                    "Buceo / Agua: ...",
                    "Entrenamiento: ...",
                    "Navegación: ...",
                    "Salud: ..."
                ],
                "construccion": [
                    "Caja: ...",
                    "Bisel: ...",
                    "Fondo: ...",
                    "Correa: ...",
                    "Resistencia agua: ...",
                    "Dimensiones: ...",
                    "Peso: ...",
                    "Sistema operativo: ..."
                ]
            }},
            "pros": [
                "Ventaja 1: Explicación detallada...",
                "Ventaja 2: Explicación detallada...",
                "Ventaja 3: Explicación detallada...",
                "Ventaja 4: Explicación detallada...",
                "Ventaja 5: Explicación detallada...",
                "Ventaja 6: Explicación detallada..."
            ],
            "contras": [
                "Desventaja 1: Explicación detallada...",
                "Desventaja 2: Explicación detallada...",
                "Desventaja 3: Explicación detallada...",
                "Desventaja 4: Explicación detallada..."
            ],
            "puntuacion": 9.3
        }}
        """

    print(f"   🔍 Analizando en profundidad ({categoria_str.upper()}): {producto['modelo_corto']}...")
    datos_ia = llamar_gemini_con_respaldo(prompt)

    if not datos_ia:
        print(f"❌ ABORTANDO PUBLICACIÓN de '{producto['modelo_corto']}': Gemini no devolvió datos válidos.")
        return

    s = datos_ia.get('specs', {})

    # --- CONSTRUCCIÓN DE FILAS DE LA TABLA ---
    if categoria_str == 'smartphone':
        spec_rows = [
            ("📺 Pantalla", s.get('pantalla', [])),
            ("⚡ Rendimiento", s.get('rendimiento', [])),
            ("📸 Cámaras", s.get('camaras', [])),
            ("🔋 Batería", s.get('bateria', [])),
            ("💾 Almacenamiento", s.get('almacenamiento', [])),
            ("🌐 Conectividad", s.get('conectividad', []))
        ]
    else:
        spec_rows = [
            ("📺 Pantalla", s.get('pantalla', [])),
            ("🔋 Batería", s.get('bateria', [])),
            ("🌐 Conectividad", s.get('conectividad', [])),
            ("💓 Sensores", s.get('sensores', [])),
            ("🏃‍♂️ Deportes", s.get('deportes', [])),
            ("🛡️ Construcción", s.get('construccion', []))
        ]

    html_rows_str = ""
    for idx, (label, values) in enumerate(spec_rows):
        is_first = (idx == 0)
        is_last = (idx == len(spec_rows) - 1)
        td_top_left = " border-top-left-radius: 6px;" if is_first else ""
        td_bottom_left = " border-bottom-left-radius: 6px;" if is_last else ""
        border_bottom = " border-bottom: 1px solid #e2e8f0;" if not is_last else ""
        
        html_rows_str += f"""
          <tr style="border: none;{border_bottom}">
            <td style="padding: 12px 14px; font-weight: bold; width: 28%; vertical-align: top; border: none; background-color: #f1f5f9;{td_top_left}{td_bottom_left}">{label}</td>
            <td style="padding: 12px 14px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.55;">
                {render_bullets(values)}
              </ul>
            </td>
          </tr>
        """

    bloque_imagen = ""
    if imagen_url:
        bloque_imagen = f"""
        <div style="text-align: center; margin-bottom: 20px;">
          <img src="{imagen_url}" alt="{producto['titulo']}" style="max-height: 280px; width: auto; object-fit: contain; border-radius: 8px;" />
        </div>
        """

    # --- HTML DE LA ENTRADA ---
    html_content = f"""
    <div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 24px; background-color: #ffffff; max-width: 780px; margin: 20px auto; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
      
      {bloque_imagen}

      <div style="background-color: #ff9900; color: #fff; font-weight: bold; display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 0.85em; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px;">
        🔥 {datos_ia.get('badge', 'DESTACADO')}
      </div>

      <h2 style="margin-top: 0; color: #111; font-size: 1.6em; line-height: 1.3;">{producto['titulo']}</h2>
      
      <p style="font-size: 1.08em; color: #334155; line-height: 1.65;">
        {datos_ia.get('resumen_ejecutivo', '')}
      </p>

      <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 18px; margin: 24px 0;">
        <h3 style="color: #0f172a; margin-top: 0; font-size: 1.15em; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; margin-bottom: 12px;">⚙️ Ficha Técnica Detallada</h3>
        
        <table style="width: 100%; border-collapse: collapse; border: none; font-size: 0.95em; color: #1e293b;">
          {html_rows_str}
        </table>
      </div>

      <div style="display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 280px; background-color: #f0fdf4; padding: 18px; border-radius: 8px; border-left: 4px solid #22c55e;">
          <h4 style="color: #15803d; margin-top: 0; font-size: 1.1em;">✅ Lo Mejor (Pros)</h4>
          <ul style="padding-left: 18px; color: #166534; margin-bottom: 0; line-height: 1.55;">
            {render_bullets(datos_ia.get('pros', []))}
          </ul>
        </div>
        
        <div style="flex: 1; min-width: 280px; background-color: #fef2f2; padding: 18px; border-radius: 8px; border-left: 4px solid #ef4444;">
          <h4 style="color: #b91c1c; margin-top: 0; font-size: 1.1em;">❌ A mejorar (Contras)</h4>
          <ul style="padding-left: 18px; color: #991b1b; margin-bottom: 0; line-height: 1.55;">
            {render_bullets(datos_ia.get('contras', []))}
          </ul>
        </div>
      </div>

      <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
        <p style="font-size: 1.3em; font-weight: bold; color: #111; margin-bottom: 6px;">
          Precio orientativo: <span style="color: #b12704;">{producto['precio']}</span> | Puntuación: ⭐ <strong>{datos_ia.get('puntuacion', 9.0)}/10</strong>
        </p>
        <p style="font-size: 0.85em; color: #64748b; margin-top: 0; margin-bottom: 18px;">
          Precio de referencia a fecha {fecha_hoy}; puede variar. Consulta el precio actual en Amazon.
        </p>
        <a href="{affiliate_link}" target="_blank" rel="sponsored nofollow" style="background-color: #ffa41c; color: #111; text-decoration: none; font-size: 1.2em; font-weight: bold; padding: 16px 32px; border-radius: 8px; border: 1px solid #ff8f00; display: inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
          Ver precio actualizado en Amazon 🛒
        </a>
      </div>
    </div>
    """

    # Obtener el ID de la categoría dinámicamente en WordPress
    categoria_id = obtener_o_crear_categoria(categoria_str)

    meta_payload = {
        "top_marca": producto['marca'],
        "top_modelo": producto['modelo_corto'],
        "top_busqueda": producto['busqueda'],
        "producto_categoria": categoria_str
    }

    if categoria_str == 'smartphone':
        meta_payload.update({
            "spec_pantalla": str(s.get('pantalla', [])),
            "spec_rendimiento": str(s.get('rendimiento', [])),
            "spec_camaras": str(s.get('camaras', [])),
            "spec_bateria": str(s.get('bateria', [])),
            "spec_almacenamiento": str(s.get('almacenamiento', [])),
            "spec_conectiv": str(s.get('conectividad', []))
        })
    else:
        meta_payload.update({
            "spec_pantalla": str(s.get('pantalla', [])),
            "spec_bateria": str(s.get('bateria', [])),
            "spec_conectiv": str(s.get('conectividad', [])),
            "spec_sensores": str(s.get('sensores', [])),
            "spec_deportes": str(s.get('deportes', [])),
            "spec_cuerpo": str(s.get('construccion', []))
        })

    wp_endpoint = f"{WP_URL}/wp-json/wp/v2/posts"
    payload = {
        "title": f"Análisis y Opinión: {producto['titulo']}",
        "content": html_content,
        "status": "publish",
        "meta": meta_payload
    }

    # Asignar la categoría en WordPress si se encontró/creó con éxito
    if categoria_id:
        payload["categories"] = [categoria_id]

    try:
        # TIMEOUT DE 30 SEGUNDOS PARA EVITAR BLOQUEOS INFINITOS EN GITHUB
        res = requests.post(wp_endpoint, json=payload, auth=(WP_USER, WP_APP_PASSWORD), timeout=30)
        if res.status_code == 201:
            print(f"✅ ¡Publicación detallada creada exitosamente para {producto['titulo']} (Categoría ID: {categoria_id})!")
        else:
            print(f"❌ Error al publicar en WordPress ({res.status_code}): {res.text}")
    except requests.exceptions.Timeout:
        print(f"❌ Error de tiempo de espera (Timeout) al conectar con WordPress para {producto['titulo']}.")
    except Exception as e:
        print(f"❌ Error crítico de red al publicar en WordPress: {e}")


if __name__ == "__main__":
    total_productos = len(productos_catalogo)
    print(f"🚀 Iniciando procesamiento de {total_productos} productos...")
    
    for index, item in enumerate(productos_catalogo):
        print(f"\n[{index + 1}/{total_productos}] Procesando: {item['modelo_corto']}")
        procesar_y_publicar(item)
        
        # Pausa de seguridad de 6 segundos entre productos para respetar los límites RPM de la IA
        if index < total_productos - 1:
            print("⏳ Esperando 6 segundos para respetar los límites de la IA y asegurar una entrega limpia...")
            time.sleep(6)
            
    print("\n✨ ¡Proceso de publicación completado con éxito!")
