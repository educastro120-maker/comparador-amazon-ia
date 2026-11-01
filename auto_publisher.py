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
        "marca": "Garmin",
        "modelo_corto": "fēnix 8 Solar",
        "busqueda": "Garmin fēnix 8 Solar",
        "titulo": "Garmin fēnix 8 Solar - Smartwatch Multideporte GPS Premium, Cristal de Zafiro Carga Solar, Micrófono y Altavoz, Linterna LED",
        "especificaciones": "Pantalla Memory-in-Pixel con tecnología de carga solar Solar Sapphire, bisel de titanio de grado 5, resistencia militar MIL-STD-810H y botones inductivos estancos aptos para buceo (40m). Incorpora micrófono/altavoz para llamadas y comandos por voz, linterna LED y hasta 48 días de autonomía en modo reloj.",
        "precio": "1099.99€",
        "imagen": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Mi_Watch.jpg"
    }
]

def render_bullets(items):
    """Convierte una lista de strings en elementos de lista HTML con negritas en las claves y viñetas elegantes"""
    if isinstance(items, list):
        html_out = ""
        for item in items:
            if ":" in item:
                partes = item.split(":", 1)
                html_out += f"<li style='margin-bottom: 6px;'><strong>{partes[0].strip()}:</strong> {partes[1].strip()}</li>"
            else:
                html_out += f"<li style='margin-bottom: 6px;'>{item.strip()}</li>"
        return html_out
    return f"<li>{items}</li>"

def procesar_y_publicar(producto):
    query_encoded = urllib.parse.quote_plus(producto['busqueda'])
    affiliate_link = f"https://www.amazon.es/s?k={query_encoded}&tag={AMAZON_TAG}"

    prompt = f"""
    Actúa como un ingeniero jefe de hardware y analista de laboratorio tecnológico.
    NAVEGACIÓN EN TIEMPO REAL REQUERIDA: Debes buscar en tiempo real los datos técnicos completos de lanzamiento, manuales técnicos y fichas de laboratorio del dispositivo exacto: "{producto['busqueda']}".

    TU TAREA ES GENERAR UNA FICHA TÉCNICA ULTRA-COMPLETA Y EXHAUSTIVA.
    Cada categoría técnica DEBE contener entre 4 y 7 viñetas hiperespecíficas usando estrictamente el formato "Parámetro: Valor/Explicación detallada".

    EJEMPLO DEL NIVEL DE DETALLE EXIGIDO PARA CADA SECCIÓN:
    - Pantalla:
      "Panel: LTPO 2.0 AMOLED circular de 1,5 pulgadas."
      "Resolución: 466 × 466 píxeles (310 ppp)."
      "Brillo Máximo: 3.500 nits picos de visibilidad plena a sol directo."
      "Tecnología: Refresco adaptativo 1 Hz a 60 Hz y Always-On Display (AOD)."
      "Protección: Cristal de zafiro sintético de alta dureza."
    - Batería:
      "Capacidad: 867 mAh de alta densidad."
      "Procesador: Dual-core especializado con gestión energética adaptativa."
      "Autonomía: Hasta 14 días en uso típico, 40 horas continuas con GPS activo."
      "Carga: Carga rápida magnética (0 a 100% en 60 min, 15 min equivalen a 1 día)."
    - Conectividad:
      "NFC: Sí (pagos móviles y tarjetas de acceso)."
      "Red Móvil: Compatibilidad eSIM / 4G LTE para uso independiente."
      "Sistemas Inalámbricos: Wi-Fi dual-band, Bluetooth 5.3 y Chip UWB."
      "Posicionamiento GPS: GNSS de doble frecuencia L1+L5 (GPS, GLONASS, Galileo, BeiDou, QZSS)."
    - Sensores:
      "Salud: Pulsómetro óptico continuo, SpO2, sensor de ECG certificado y temperatura cutánea."
      "Entorno: Altímetro barométrico, brújula digital, profundímetro con temperatura de agua."
      "Seguridad: Acelerómetro de alta fuerza G para detección de caídas y colisiones."
    - Deportes:
      "Modos: Más de 100 modalidades deportivas con métricas avanzadas (VO2 Max, Potencia, SWOLF)."
      "Buceo: Certificación para inmersiones hasta 100 m / 150 m (EN 13319 / ISO 22810)."
      "Navegación: Mapas topográficos 3D offline, waypoints y función Backtrack."
    - Construcción:
      "Chasis: Titanio de Grado 5 / Metal Líquido a base de Circonio."
      "Bisel y Fondo: Cerámica nanocristalina y cristal de zafiro."
      "Resistencia: 10 ATM / 20 ATM, IP68, IP69K y norma militar MIL-STD-810H."
      "Dimensiones y Peso: 48,5 × 48,5 × 13 mm / 80 gramos."

    Devuelve ÚNICAMENTE un objeto JSON válido con esta estructura exacta y sin texto adicional afuera:
    {{
      "badge": "ETIQUETA EN MAYÚSCULAS (ej: REY DEL BUCEO Y MONTAÑA)",
      "resumen_ejecutivo": "Redacción técnica y profesional de 150 a 220 palabras analizando el impacto del reloj en el mercado, sus materiales prémium, público objetivo y rendimiento real.",
      "specs": {{
        "pantalla": [
          "Panel: ...",
          "Resolución: ...",
          "Brillo Máximo: ...",
          "Tecnología: ...",
          "Protección: ..."
        ],
        "bateria": [
          "Capacidad: ...",
          "Procesador: ...",
          "Autonomía: ...",
          "Carga: ..."
        ],
        "conectividad": [
          "Red Móvil / eSIM: ...",
          "NFC: ...",
          "Sistemas Inalámbricos: ...",
          "Posicionamiento (GPS): ...",
          "Audio y Micrófonos: ..."
        ],
        "sensores": [
          "Monitor de Salud Continuo: ...",
          "Electrocardiograma (ECG): ...",
          "Temperatura: ...",
          "Movimiento y Entorno: ...",
          "Inmersión y Altitud: ..."
        ],
        "deportes": [
          "Modos Deportivos: ...",
          "Buceo / Resistencia al Agua: ...",
          "Navegación y Mapas: ...",
          "Métricas Avanzadas: ..."
        ],
        "construccion": [
          "Caja: ...",
          "Bisel y Fondo: ...",
          "Resistencia y Certificaciones: ...",
          "Dimensiones y Peso: ...",
          "Control e Interacción: ..."
        ]
      }},
      "pros": [
        "Punto fuerte 1 con explicación detallada de valor real (mínimo 15 palabras)",
        "Punto fuerte 2 detallando especificaciones concretas",
        "Punto fuerte 3 sobre rendimiento o materiales",
        "Punto fuerte 4 adicional",
        "Punto fuerte 5 adicional"
      ],
      "contras": [
        "Punto negativo 1 redactado con criterio técnico",
        "Punto negativo 2 sobre ergonomía, precio o ecosistema",
        "Punto negativo 3 adicional",
        "Punto negativo 4 adicional"
      ],
      "puntuacion": 9.4
    }}
    """

    print(f"🌐 Extrayendo ficha técnica masiva y datos de laboratorio para: {producto['titulo']}...")
    
    max_intentos = 3
    response = None
    for intento in range(1, max_intentos + 1):
        try:
            config = types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.1,  # Temperatura ultra baja para precisión máxima sin alucinaciones
                response_mime_type="application/json",
                max_output_tokens=5000  # Expandido a 5000 tokens para permitir JSONs extensos y detallados
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

    # Parseo estricto del JSON
    datos_ia = None
    if response and hasattr(response, 'text') and response.text:
        try:
            datos_ia = json.loads(response.text.strip())
        except json.JSONDecodeError as err:
            print(f"⚠️ Advertencia: Error analizando JSON en {producto['titulo']}: {err}")

    # Fallback contextual inteligente si la llamada remota falla
    if not datos_ia:
        print(f"💡 Aplicando respaldo estructurado para {producto['titulo']}...")
        datos_ia = {
            "badge": f"ANÁLISIS TÉCNICO {producto['marca'].upper()}",
            "resumen_ejecutivo": f"{producto['titulo']} representa una alternativa de ingeniería avanzada en el catálogo actual. Integra componentes de alta durabilidad y un paquete integral de sensores biométricos para deportistas exigentes.",
            "specs": {
                "pantalla": [f"Modelo: {producto['modelo_corto']}", "Panel: Pantalla táctil de alta visibilidad en exteriores.", "Protección: Cristal reforzado."],
                "bateria": ["Autonomía: Optimizada para uso continuo en modo multideporte y GPS.", f"Precio de referencia: {producto['precio']}"],
                "conectividad": ["Sistemas de posicionamiento: GPS / GNSS integrado.", "Inalámbrico: Bluetooth de alta velocidad."],
                "sensores": ["Biometría: Frecuencia cardíaca óptica y oxígeno en sangre (SpO2).", "Navegación: Altímetro barométrico y brújula."],
                "deportes": ["Modalidades: Perfiles multideporte y métricas de entrenamiento.", "Resistencia: Apto para uso deportivo intenso."],
                "construccion": [f"Fabricante: {producto['marca']}", f"Especificaciones base: {producto['especificaciones']}"]
            },
            "pros": ["Diseño resistente y materiales de primera línea.", "Precisión en mediciones deportivas.", "Buena visibilidad."],
            "contras": ["Dimensiones adaptadas a uso deportivo.", "Precio en rango de gama alta."],
            "puntuacion": 9.0
        }

    s = datos_ia['specs']

    # HTML profesional y dinámico con negritas automáticas
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

      <!-- Ficha Técnica Detallada -->
      <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin: 20px 0;">
        <h3 style="color: #0f172a; margin-top: 0; font-size: 1.1em; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; margin-bottom: 12px;">⚙️ Ficha Técnica Detallada</h3>
        
        <table style="width: 100%; border-collapse: collapse; border: none; font-size: 0.95em; color: #334155;">
          <tr style="border: none; border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 12px; font-weight: bold; width: 28%; vertical-align: top; border: none; background-color: #f1f5f9; border-top-left-radius: 6px;">📺 Pantalla</td>
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
