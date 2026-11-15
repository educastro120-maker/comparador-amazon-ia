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
    {
        "categoria": "smartphone",
        "marca": "Samsung",
        "modelo_corto": "Galaxy S26 Ultra",
        "busqueda": "Samsung Galaxy S26 Ultra 256GB",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Samsung Galaxy S26 Ultra (256 GB) - Smartphone con Cámara Principal de 200 MP, Doble Teleobjetivo 3x y 5x, Pantalla QHD+ de 6,9 Pulgadas y Galaxy AI",
        "especificaciones": "Cámara principal de 200 MP con f/1.4, ultra gran angular de 50 MP y dos teleobjetivos (3x y 5x), pantalla QHD+ de 6,9 pulgadas, procesador Snapdragon de gama alta y batería de 5.000 mAh con Galaxy AI.",
        "precio": "1549.00€",
        "imagen": "",
    },
    {
        "categoria": "smartwatch",
        "marca": "Garmin",
        "modelo_corto": "Fenix 8",
        "busqueda": "Garmin Fenix 8 AMOLED 51mm",
        "link_afiliado": "",
        "asin": "",
        "titulo": "Garmin Fenix 8 - Smartwatch multideporte con pantalla AMOLED, funciones avanzadas de entrenamiento y autonomía superior",
        "especificaciones": "Pantalla AMOLED brillante, mapas TopoActive integrados, GPS de doble banda, llamadas y asistente de voz, resistencia avanzada al buceo y materiales de titanio.",
        "precio": "999.00€",
        "imagen": "",
    }
]


def render_bullets(items):
    """Convierte una lista de strings en elementos de lista HTML con viñetas"""
    if isinstance(items, list):
        return "".join([f"<li style='margin-bottom: 4px;'>{item}</li>" for item in items])
    return f"<li>{items}</li>"


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
    
    categoria = producto.get('categoria', 'smartwatch').lower()
    imagen_url = producto.get('imagen', '').strip()

    # --- PROMPTS ESTRUCTURADOS ---
    if categoria == 'smartphone':
        prompt = f"""
        Actúa como analista senior de tecnología y experto en SEO y CRO para afiliación de Amazon.
        Analiza detalladamente este smartphone basándote en los datos proporcionados:
        - Título: {producto['titulo']}
        - Especificaciones base: {producto['especificaciones']}
        - Precio: {producto['precio']}

        INSTRUCCIONES:
        - Extrae todos los datos técnicos exactos (pulgadas, resolución, Hz, procesador, RAM, megapíxeles, apertura focal, mAh, W de carga, etc.).
        - Redacta un resumen ejecutivo persuasivo de 3 a 4 líneas enfocado a convencer al comprador.
        - Cada lista dentro de "specs" debe tener entre 2 y 3 puntos detallados y técnicos.
        
        Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
        {{
            "badge": "texto corto persuasivo (ej: Destacado Fotografía o Rey del Zoom)",
            "resumen_ejecutivo": "párrafo comercial y atractivo sobre el rendimiento y valor del móvil",
            "specs": {{
                "pantalla": ["detalle 1", "detalle 2"],
                "rendimiento": ["detalle 1", "detalle 2"],
                "camaras": ["detalle 1", "detalle 2"],
                "bateria": ["detalle 1", "detalle 2"],
                "almacenamiento": ["detalle 1", "detalle 2"],
                "conectividad": ["detalle 1", "detalle 2"]
            }},
            "pros": ["pro 1", "pro 2", "pro 3"],
            "contras": ["contra 1", "contra 2"],
            "puntuacion": 9.2
        }}
        """
    else:
        prompt = f"""
        Actúa como analista de tecnología experto en Smartwatches y CRO. Analiza este producto:
        - Título: {producto['titulo']}
        - Especificaciones base: {producto['especificaciones']}
        - Precio: {producto['precio']}

        Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
        {{
            "badge": "texto corto persuasivo",
            "resumen_ejecutivo": "párrafo comercial y atractivo",
            "specs": {{
                "pantalla": ["detalle 1"],
                "bateria": ["detalle 1"],
                "conectividad": ["detalle 1"],
                "sensores": ["detalle 1"],
                "deportes": ["detalle 1"],
                "construccion": ["detalle 1"]
            }},
            "pros": ["pro 1", "pro 2", "pro 3"],
            "contras": ["contra 1", "contra 2"],
            "puntuacion": 8.8
        }}
        """

    print(f"\n🚀 Analizando con Gemini ({categoria.upper()}) el producto: {producto['modelo_corto']}...")
    datos_ia = llamar_gemini_con_respaldo(prompt)

    # Si la IA falla tras los reintentos, abortamos este producto para evitar publicaciones vacías o pobres
    if not datos_ia:
        print(f"❌ ABORTANDO PUBLICACIÓN de '{producto['modelo_corto']}': Gemini no devolvió datos válidos. Revisa el error mostrado arriba.")
        return

    s = datos_ia.get('specs', {})

    # --- CONSTRUCCIÓN DE FILAS DE LA TABLA ---
    if categoria == 'smartphone':
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
        border_bottom = " border-bottom: 1px solid #f1f5f9;" if not is_last else ""
        
        html_rows_str += f"""
          <tr style="border: none;{border_bottom}">
            <td style="padding: 10px 12px; font-weight: bold; width: 30%; vertical-align: top; border: none; background-color: #f1f5f9;{td_top_left}{td_bottom_left}">{label}</td>
            <td style="padding: 10px 12px; vertical-align: top; border: none; background-color: #f8fafc;">
              <ul style="margin: 0; padding-left: 18px; line-height: 1.5;">
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
    <div style="border: 2px solid #e0e0e0; border-radius: 12px; padding: 24px; background-color: #ffffff; max-width: 750px; margin: 20px auto; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
      
      {bloque_imagen}

      <div style="background-color: #ff9900; color: #fff; font-weight: bold; display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 0.85em; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px;">
        🔥 {datos_ia.get('badge', 'Destacado')}
      </div>

      <h2 style="margin-top: 0; color: #111; font-size: 1.6em; line-height: 1.3;">{producto['titulo']}</h2>
      
      <p style="font-size: 1.1em; color: #444; line-height: 1.6;">
        {datos_ia.get('resumen_ejecutivo', '')}
      </p>

      <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin: 20px 0;">
        <h3 style="color: #0f172a; margin-top: 0; font-size: 1.1em; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; margin-bottom: 12px;">⚙️ Ficha Técnica Resumida</h3>
        
        <table style="width: 100%; border-collapse: collapse; border: none; font-size: 0.95em; color: #334155;">
          {html_rows_str}
        </table>
      </div>

      <div style="display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 250px; background-color: #f0fdf4; padding: 18px; border-radius: 8px; border-left: 4px solid #22c55e;">
          <h4 style="color: #15803d; margin-top: 0; font-size: 1.1em;">✅ Lo Mejor (Pros)</h4>
          <ul style="padding-left: 18px; color: #166534; margin-bottom: 0; line-height: 1.5;">
            {"".join([f'<li style="margin-bottom: 6px;">{p}</li>' for p in datos_ia.get('pros', [])])}
          </ul>
        </div>
        
        <div style="flex: 1; min-width: 250px; background-color: #fef2f2; padding: 18px; border-radius: 8px; border-left: 4px solid #ef4444;">
          <h4 style="color: #b91c1c; margin-top: 0; font-size: 1.1em;">❌ A mejorar (Contras)</h4>
          <ul style="padding-left: 18px; color: #991b1b; margin-bottom: 0; line-height: 1.5;">
            {"".join([f'<li style="margin-bottom: 6px;">{c}</li>' for c in datos_ia.get('contras', [])])}
          </ul>
        </div>
      </div>

      <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #f0f0f0;">
        <p style="font-size: 1.3em; font-weight: bold; color: #111; margin-bottom: 15px;">
          Precio estimado: <span style="color: #b12704;">{producto['precio']}</span> | Puntuación: ⭐ <strong>{datos_ia.get('puntuacion', 8.5)}/10</strong>
        </p>
        <a href="{affiliate_link}" target="_blank" rel="sponsored nofollow" style="background-color: #ffa41c; color: #111; text-decoration: none; font-size: 1.2em; font-weight: bold; padding: 16px 32px; border-radius: 8px; border: 1px solid #ff8f00; display: inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
          Ver precio actualizado en Amazon 🛒
        </a>
      </div>
    </div>
    """

    meta_payload = {
        "top_marca": producto['marca'],
        "top_modelo": producto['modelo_corto'],
        "top_busqueda": producto['busqueda'],
        "producto_categoria": categoria
    }

    if categoria == 'smartphone':
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

    res = requests.post(wp_endpoint, json=payload, auth=(WP_USER, WP_APP_PASSWORD))
    if res.status_code == 201:
        print(f"✅ ¡Publicación creada exitosamente para {producto['titulo']}!")
    else:
        print(f"❌ Error al publicar en WordPress ({res.status_code}): {res.text}")

if __name__ == "__main__":
    for item in productos_catalogo:
        procesar_y_publicar(item)
