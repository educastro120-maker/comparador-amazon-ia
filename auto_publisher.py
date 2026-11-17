import os
import sys
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

# Timeout estricto de 35 segundos (35000 ms) en la API de Google para evitar bloqueos eternos
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={'timeout': 35000}
)

# ==========================================
# 2. CATÁLOGO MULTI-CATEGORÍA
# ==========================================
productos_catalogo = [

    # 1) Primero en la mayoría de guías de compra y en el listado de más vendidos de Kimovil de noviembre de 2026
    {
        "categoria": "smartphone",
        "marca": "Xiaomi",
        "modelo_corto": "POCO X8 Pro",
        "busqueda": "Xiaomi POCO X8 Pro 8GB 256GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Xiaomi POCO X8 Pro (8 GB + 256 GB) - Smartphone 5G con Dimensity 8500-Ultra, Pantalla AMOLED 1.5K de 6,59 Pulgadas a 120 Hz, Batería de 6.500 mAh y Carga de 100 W",
        "especificaciones": "Es el favorito de las guías de calidad-precio de 2026: potencia de gama alta con procesador MediaTek Dimensity 8500-Ultra, memoria UFS 4.1, pantalla AMOLED 1.5K de 6,59 pulgadas a 120 Hz con hasta 3.500 nits, batería de silicio-carbono de 6.500 mAh con carga de 100 W (Xataka comprobó que llega a tres días), cámara principal Sony IMX882 de 50 MP con estabilización óptica y NFC. Pesa 201 g. Su punto débil es la cámara secundaria. Salió en España a 340 € (8 GB + 256 GB); en Amazon se ha visto a 379 € y a 289 € en el Prime Day de 2026, y Kimovil lo sitúa desde unos 265 €.",
        "precio": "340.00€",
        "imagen": "",
    },
    # 2) Mejor calidad-precio de gama media según Compra Smartphone; ya en el catálogo de más vendidos
    {
        "categoria": "smartphone",
        "marca": "Xiaomi",
        "modelo_corto": "Redmi Note 15 Pro 5G",
        "busqueda": "Xiaomi Redmi Note 15 Pro 5G 8GB 256GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Xiaomi Redmi Note 15 Pro 5G (8 GB + 256 GB) - Smartphone con Pantalla AMOLED 1.5K de 6,83 Pulgadas, Cámara de 200 MP con OIS y Batería de 6.580 mAh",
        "especificaciones": "Compra Smartphone lo elige como el mejor calidad-precio de la gama media y el mejor móvil barato por menos de 300 euros. Pantalla AMOLED 1.5K de 6,83 pulgadas a 120 Hz, procesador MediaTek Dimensity 7400-Ultra, cámara principal de 200 MP con estabilización óptica, batería de 6.580 mAh, resistencia IP68 y NFC. La carga de 45 W es su punto flojo. Salió en España a 399 € (8 GB + 256 GB); en Amazon se ha visto entre 278 y 320 € durante 2026.",
        "precio": "399.00€",
        "imagen": "",
    },
    # 3) La opción de más autonomía
    {
        "categoria": "smartphone",
        "marca": "Xiaomi",
        "modelo_corto": "Redmi Note 15 Pro+ 5G",
        "busqueda": "Xiaomi Redmi Note 15 Pro+ 5G 8GB 256GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Xiaomi Redmi Note 15 Pro+ 5G (8 GB + 256 GB) - Smartphone con Pantalla AMOLED 1.5K de 6,83 Pulgadas, Snapdragon 7s Gen 4, Cámara de 200 MP y HyperCharge de 100 W",
        "especificaciones": "Xataka lo recomienda si priorizas una autonomía enorme y la cámara no es lo más importante, y otras guías lo señalan como la compra más equilibrada de la gama media. Pantalla AMOLED de 6,83 pulgadas con resolución 1.5K, procesador Snapdragon 7s Gen 4, cámara principal de 200 MP con sensor de 1/1,4 pulgadas y carga de 100 W. Pesa 207 g. PVP en España de 499,99 € (8 GB + 256 GB) y 529,99 € (12 GB + 512 GB); se ha visto a 359,99 € en oferta y en torno a 319-324 € en las guías.",
        "precio": "499.99€",
        "imagen": "",
    },
    # 4) La opción segura con Samsung; ya en el catálogo de más vendidos
    {
        "categoria": "smartphone",
        "marca": "Samsung",
        "modelo_corto": "Galaxy A57 5G",
        "busqueda": "Samsung Galaxy A57 5G 256GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Samsung Galaxy A57 5G (256 GB) - Smartphone Android de Gama Media con Pantalla Super AMOLED Plus de 6,7 Pulgadas, IP68 y Años de Actualizaciones",
        "especificaciones": "Xataka lo recomienda para quien quiere ir a lo seguro: un móvil que cumple de sobra con lo esperable y lleva la firma de Samsung, con IP68, actualizaciones durante años y pantalla Super AMOLED Plus FHD+ de 6,7 pulgadas. Rinde menos por euro que los POCO y Redmi. PVP de 589 € (otras fuentes dan 559 €); en Amazon se ha visto a 471 € en el Prime Day de 2026 y se citan precios de 399 € en guías recientes. Samsung ha subido el precio de los Galaxy A en Estados Unidos, así que puede subir también aquí.",
        "precio": "589.00€",
        "imagen": "",
    },
    # 5) Ganador de Xataka en gama media; mejor cámara y soporte
    {
        "categoria": "smartphone",
        "marca": "Google",
        "modelo_corto": "Pixel 10a",
        "busqueda": "Google Pixel 10a 128GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Google Pixel 10a (128 GB) - Smartphone Android con 7 Años de Actualizaciones, Cámara de 48 MP con OIS, Gemini y Batería de Más de 30 Horas",
        "especificaciones": "Xataka lo elige como el ganador entre los móviles de gama media calidad-precio, sobre todo si quieres buena cámara y un móvil compacto. Chip Tensor G4, 8 GB de RAM, pantalla pOLED de 6,3 pulgadas con hasta 3.000 nits, cámara principal de 48 MP f/1.7 con OIS más gran angular de 13 MP, batería de 5.100 mAh con carga inalámbrica Qi, Android 16 y siete años de actualizaciones de sistema y seguridad. PVP de 549 € (128 GB) y 649 € (256 GB); en Amazon se ha visto a 416,50 € (128 GB) y a 449 € (256 GB), y tras salir el Pixel 11 llegó a su mínimo histórico. Es menos potente que un POCO X8 Pro, pero dura años.",
        "precio": "549.00€",
        "imagen": "",
    },
    # 6) El de diseño y software limpio
    {
        "categoria": "smartphone",
        "marca": "Nothing",
        "modelo_corto": "Phone (4a)",
        "busqueda": "Nothing Phone (4a) 8GB 128GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Nothing Phone (4a) (8 GB + 128 GB) - Smartphone 5G con Pantalla AMOLED de 6,78 Pulgadas, Triple Cámara de 50 MP con Zoom y Diseño Transparente con Glyph",
        "especificaciones": "El móvil de la lista que menos parece barato: diseño transparente con barra de glifos, software muy limpio y triple cámara de 50 MP con zoom que, según Wikiversus, no tiene rival por este precio. Pantalla AMOLED de 6,78 pulgadas a 120 Hz, procesador Snapdragon 7s Gen 4 y batería de unos 5.000 mAh (en la prueba de la OCU llegó a unas 45 horas de uso). Salió en marzo de 2026 a 349 € (8 GB + 128 GB) y ese es el precio habitual en MediaMarkt, Fnac y PcComponentes. Una reseña señala que el procesador podría ser más potente por el precio. El Phone (4a) Pro cuesta 479 € de salida.",
        "precio": "349.00€",
        "imagen": "",
    },
    # 7) Gran pantalla, carga inalámbrica y buen diseño
    {
        "categoria": "smartphone",
        "marca": "Motorola",
        "modelo_corto": "Edge 70 Fusion",
        "busqueda": "Motorola Edge 70 Fusion 8GB 256GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Motorola Edge 70 Fusion 5G (8 GB + 256 GB) - Smartphone con Pantalla AMOLED de 6,78 Pulgadas a 144 Hz, Cámara Sony LYT-710 de 50 MP y Carga Inalámbrica",
        "especificaciones": "Xataka lo recomienda si priorizas la autonomía y una pantalla grande y de gran calidad. AMOLED de 6,78 pulgadas a 144 Hz, procesador Snapdragon 7s Gen 3, cámara principal Sony LYT-710 de 50 MP con estabilización óptica, 177 g y solo 7,2 mm de grosor, carga de 68 W y carga inalámbrica de 15 W. Salió en España a 448,99 € (8 GB + 256 GB) con unos auriculares Moto Buds Loop de regalo en las primeras semanas, y se vio a 329 € en junio de 2026. ATENCIÓN: en Europa existe también una versión con batería de 7.000 mAh por unos 20 € más; comprueba qué versión es antes de comprar.",
        "precio": "448.99€",
        "imagen": "",
    },
    # 8) El más potente de la lista (gama media-alta); su precio real baja mucho en ofertas
    {
        "categoria": "smartphone",
        "marca": "Xiaomi",
        "modelo_corto": "17T",
        "busqueda": "Xiaomi 17T 12GB 256GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Xiaomi 17T (12 GB + 256 GB) - Smartphone con Cámara Leica y Teleobjetivo 5x, Dimensity 8500-Ultra, Pantalla AMOLED 1.5K de 6,59 Pulgadas y Batería de 6.500 mAh",
        "especificaciones": "Es el móvil de gama media-alta de la lista: triple cámara Leica con cámara principal de 50 MP con OIS, teleobjetivo periscópico 5x de 50 MP y gran angular de 12 MP, procesador Dimensity 8500-Ultra, pantalla AMOLED 1.5K de 6,59 pulgadas a 120 Hz con hasta 3.500 nits, batería de silicio-carbono de 6.500 mAh con carga de 67 W e IP68. Xiaomi adelantó su lanzamiento de septiembre a mayo de 2026. Su PVP en España es de 749,99 €, pero se ha visto a 399 € en Amazon con un descuento de 200 € en el carrito, y entre 477 y 519 € en otras ofertas, así que solo compensa si lo encuentras rebajado.",
        "precio": "749.99€",
        "imagen": "",
    },
    # 9) El Redmi barato recomendable
    {
        "categoria": "smartphone",
        "marca": "Xiaomi",
        "modelo_corto": "Redmi Note 15 5G",
        "busqueda": "Xiaomi Redmi Note 15 5G 8GB 256GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Xiaomi Redmi Note 15 5G (8 GB + 256 GB) - Smartphone con Pantalla AMOLED FHD+ de 6,77 Pulgadas, Snapdragon 6 Gen 3, Cámara de 108 MP y Batería de 5.520 mAh",
        "especificaciones": "Xataka lo describe como un Redmi recomendable si buscas un móvil barato. Pantalla AMOLED FHD+ de 6,77 pulgadas, procesador Snapdragon 6 Gen 3, cámara principal de 108 MP, batería de 5.520 mAh, lector de huellas en pantalla, HyperOS y seis años de actualizaciones de seguridad. Precio de lanzamiento en España de 299,99 € (8 GB + 256 GB); la versión 4G con 128 GB costaba 199,99 €. Renuncia a la cámara de 200 MP y a las prestaciones de los Pro, pero es la entrada razonable a la serie.",
        "precio": "299.99€",
        "imagen": "",
    },
    # 10) El mejor móvil Android de entrada; ya en el catálogo de más vendidos
    {
        "categoria": "smartphone",
        "marca": "Samsung",
        "modelo_corto": "Galaxy A17 5G",
        "busqueda": "Samsung Galaxy A17 5G 128GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Samsung Galaxy A17 5G (128 GB) - Smartphone Android con Pantalla Super AMOLED de 6,7 Pulgadas a 90 Hz y Cámara Principal de 50 MP",
        "especificaciones": "La opción más barata que sigue mereciendo la pena y el Android más vendido de España. Pantalla Super AMOLED de 6,7 pulgadas con 90 Hz, cámara principal de 50 MP y 192 g de peso. Se vende desde unos 159 € en la versión de 4 GB + 128 GB (hay una de 8 GB + 256 GB desde unos 280 €); su precio original era de 309 € y en el Prime Day de 2026 se vio a 236 €. Samsung ha subido el precio de los Galaxy A en Estados Unidos, así que puede subir también aquí.",
        "precio": "159.00€",
        "imagen": "",
    }

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
        res = requests.get(cat_endpoint, params={"search": nombre_categoria}, auth=(WP_USER, WP_APP_PASSWORD), timeout=15)
        if res.status_code == 200:
            categorias = res.json()
            for cat in categorias:
                if cat['name'].lower() == nombre_categoria.lower():
                    return cat['id']
        
        payload_cat = {"name": nombre_categoria}
        res_crear = requests.post(cat_endpoint, json=payload_cat, auth=(WP_USER, WP_APP_PASSWORD), timeout=15)
        if res_crear.status_code == 201:
            return res_crear.json()['id']
    except Exception as e:
        print(f"   ⚠️ Advertencia al gestionar categoría en WordPress: {e}")
    
    return None


def llamar_gemini_con_respaldo(prompt):
    """Gestiona automáticamente los límites de cuota por minuto (429) de Google AI Studio."""
    modelos_a_probar = ['gemini-3.5-flash-lite', 'gemini-3.8-flash', 'gemini-2.5-flash-lite']
    
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
                error_str = str(e)
                print(f"   ⚠️ Fallo con {modelo} (Intento {intento}): {type(e).__name__} -> {error_str}")
                
                # Si es límite de cuota por minuto (429), esperar 62 segundos a que se reinicie el minuto
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    print("   🛑 Límite de cuota por minuto alcanzado. Esperando 62 segundos para reanudar...")
                    time.sleep(62)
                else:
                    time.sleep(4)
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
        return False

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

    if categoria_id:
        payload["categories"] = [categoria_id]

    try:
        res = requests.post(wp_endpoint, json=payload, auth=(WP_USER, WP_APP_PASSWORD), timeout=30)
        if res.status_code == 201:
            print(f"✅ ¡Publicación detallada creada exitosamente para {producto['titulo']} (Categoría ID: {categoria_id})!")
            return True
        else:
            print(f"❌ Error al publicar en WordPress ({res.status_code}): {res.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Error de tiempo de espera (Timeout) al conectar con WordPress para {producto['titulo']}.")
        return False
    except Exception as e:
        print(f"❌ Error crítico de red al publicar en WordPress: {e}")
        return False


if __name__ == "__main__":
    total_productos = len(productos_catalogo)
    publicados_ok = 0
    print(f"🚀 Iniciando procesamiento de {total_productos} productos...")
    
    for index, item in enumerate(productos_catalogo):
        print(f"\n[{index + 1}/{total_productos}] Procesando: {item['modelo_corto']}")
        exito = procesar_y_publicar(item)
        if exito:
            publicados_ok += 1
        
        if index < total_productos - 1:
            print("⏳ Esperando 15 segundos para no saturar los tokens por minuto de la capa gratuita...")
            time.sleep(15)
            
    print(f"\n📊 Resumen: {publicados_ok}/{total_productos} entradas publicadas correctamente.")
    if publicados_ok == 0 and total_productos > 0:
        sys.exit(1)
