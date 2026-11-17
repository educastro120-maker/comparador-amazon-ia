"""
DESCUBRIR CATÁLOGO
==================
Rellena AUTOMÁTICAMENTE la cola de productos (data/cola_catalogo.json) que luego publica auto_publisher.py.

Cómo funciona:
  1. Por cada categoría (smartphone, smartwatch...) coge la SIGUIENTE marca de una lista y le pide a
     Gemini, con búsqueda de Google en tiempo real, los modelos de esa marca que se venden hoy en España.
  2. Descarta lo que ya conoce (publicado o ya en la cola) para no repetir nada.
  3. Aplica filtros de calidad: sin fuentes de búsqueda no entra nada, y se descartan rumores, productos
     no vendidos en España, fechas de lanzamiento futuras y fichas demasiado pobres.
  4. Guarda los productos nuevos en la cola con estado "pendiente".

Cada ejecución avanza una marca por categoría, así que el mercado se va completando marca a marca,
con muy pocas llamadas (una por categoría y ejecución).

NO inventa productos "de memoria": si la búsqueda no devuelve fuentes, no añade nada.

LÍMITES (léelos):
  - Necesita la herramienta de búsqueda de Google de Gemini. En algunos modelos o cuentas gratuitas puede
    no estar disponible; el programa lo detecta, no añade nada e imprime el motivo.
  - No obtiene imágenes ni enlaces de afiliado: esos campos quedan vacíos (ver data/pendientes_manual.csv).
  - Revisa de vez en cuando la cola: una IA con búsqueda puede equivocarse con precios o variantes.
"""

import os
import re
import sys
import json
import unicodedata
from datetime import datetime, date
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if not GEMINI_API_KEY:
    sys.exit("❌ Falta la variable de entorno GEMINI_API_KEY.")

client = genai.Client(api_key=GEMINI_API_KEY, http_options={"timeout": int(os.environ.get("GEMINI_TIMEOUT_MS", "120000"))})

# ==========================================
# AJUSTES
# ==========================================
CARPETA_DATOS = os.environ.get("CARPETA_DATOS", "data")
RUTA_COLA = os.path.join(CARPETA_DATOS, "cola_catalogo.json")
RUTA_PUBLICADOS = os.path.join(CARPETA_DATOS, "publicados.json")
RUTA_ESTADO = os.path.join(CARPETA_DATOS, "estado_descubrimiento.json")

# Modelos con búsqueda de Google, por orden. Compruébalos en Google AI Studio y cámbialos con la
# variable DISCOVERY_MODELS (separados por comas) si alguno no existe.
MODELOS = [m.strip() for m in os.environ.get("DISCOVERY_MODELS", "gemini-3-flash-preview,gemini-3.1-flash-lite").split(",") if m.strip()]
MARCAS_POR_EJECUCION = int(os.environ.get("MARCAS_POR_EJECUCION", "1"))
MODELOS_POR_MARCA = int(os.environ.get("MODELOS_POR_MARCA", "12"))
MAX_FALLOS_MARCA = 3          # tras 3 errores seguidos con una marca, se pasa a la siguiente
MIN_CARACTERES_FICHA = 300    # fichas más cortas se descartan por pobres
CATEGORIAS_ACTIVAS = [c.strip() for c in os.environ.get("DESCUBRIR_CATEGORIAS", "smartphone,smartwatch").split(",") if c.strip()]

# Categorías y marcas a recorrer. Para añadir marcas, añádelas a la lista. Solo smartphone y smartwatch
# tienen prompt y tabla en auto_publisher.py: no actives monitores, TV, etc. hasta que lo tenga.
CATEGORIAS = {
    "smartphone": {
        "descripcion": "smartphones (móviles)",
        "marcas": ["Apple", "Samsung", "Xiaomi", "POCO", "Redmi", "Google Pixel", "Motorola", "OnePlus", "OPPO", "vivo",
                   "realme", "Honor", "Huawei", "Nothing", "ASUS", "Sony", "HMD", "ZTE nubia", "Tecno", "Infinix"],
    },
    "smartwatch": {
        "descripcion": "smartwatches y relojes deportivos con GPS",
        "marcas": ["Apple", "Samsung", "Garmin", "Huawei", "Xiaomi", "Amazfit", "COROS", "Suunto", "Polar", "Google Pixel Watch",
                   "Honor", "OnePlus", "Withings", "Mibro", "CMF by Nothing", "OPPO", "realme", "Fossil", "Casio", "Fitbit"],
    },
}


def slugify(texto):
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def cargar_json(ruta, defecto):
    if not os.path.exists(ruta):
        return defecto
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as err:
        print(f"⚠️ No se pudo leer {ruta} ({err}).")
        return defecto


def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2)


def json_desde_texto(texto):
    texto = (texto or "").strip()
    a, b = texto.find("{"), texto.rfind("}")
    if a == -1 or b == -1:
        raise ValueError("la respuesta no contiene JSON")
    return json.loads(texto[a:b + 1])


def fuentes_de_busqueda(respuesta):
    """Webs que Google Search ha usado. Si no hay ninguna, la respuesta no está respaldada por la búsqueda."""
    try:
        chunks = respuesta.candidates[0].grounding_metadata.grounding_chunks or []
        return sorted({(c.web.title or c.web.uri) for c in chunks if c.web and (c.web.title or c.web.uri)})
    except Exception:
        return []


def pedir_modelos(descripcion, marca, conocidos):
    """Una llamada con búsqueda en tiempo real. Devuelve (lista_de_productos, fuentes) o (None, [])."""
    hoy = date.today().strftime("%d/%m/%Y")
    lista_conocidos = "\n".join(f"- {c}" for c in conocidos[:80]) or "- (ninguno todavía)"
    prompt = f"""Hoy es {hoy}. Usa Google Search AHORA (haz varias búsquedas si hace falta) para listar los modelos de la marca "{marca}" en la categoría "{descripcion}" que se VENDEN actualmente en España y que son relevantes para un comparador de compra (lanzados en los últimos 3 años, o anteriores que sigan siendo muy vendidos o recomendados).

Excluye estos modelos, que ya tengo:
{lista_conocidos}

Devuelve como máximo {MODELOS_POR_MARCA} modelos NUEVOS, priorizando los más vendidos o recomendados y los lanzamientos recientes. No incluyas rumores, modelos sin lanzar ni modelos que no se vendan en España. Si no hay más modelos nuevos, devuelve una lista vacía.

Responde ÚNICAMENTE con un JSON válido (sin ``` ni texto extra) con esta forma:
{{"productos": [{{"marca": "...", "modelo_corto": "...", "busqueda": "...", "titulo": "...", "especificaciones": "...", "precio_eur": 0, "disponible_en_espana": true, "fecha_lanzamiento": "AAAA-MM"}}]}}

Reglas de cada campo:
- modelo_corto: nombre del modelo SIN la marca (por ejemplo "Galaxy A57 5G").
- busqueda: texto para buscar el producto en Amazon.es (marca + modelo + variante principal).
- titulo: título descriptivo en español al estilo de Amazon.es (marca, modelo y 2-3 características clave).
- especificaciones: ficha técnica densa en español, de 800 a 1500 caracteres, con CIFRAS REALES comprobadas en las fuentes (en móviles: pantalla, procesador, RAM y almacenamiento, cámaras, batería y carga, conectividad, peso, sistema operativo y años de actualizaciones; en relojes: pantalla, batería, GPS, sensores, resistencia al agua, compatibilidad). No inventes ningún dato: omite lo que no encuentres.
- precio_eur: precio actual o PVP en España en euros, como número. Pon 0 si no lo encuentras.
- disponible_en_espana: true solo si las fuentes confirman que se vende en España.
- fecha_lanzamiento: mes de lanzamiento en formato AAAA-MM."""

    for modelo in MODELOS:
        try:
            print(f"   🤖 Buscando con {modelo}...")
            r = client.models.generate_content(
                model=modelo, contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.2))
            fuentes = fuentes_de_busqueda(r)
            if not fuentes:
                print("   ⚠️ La respuesta no viene respaldada por fuentes de búsqueda: se descarta.")
                return None, []
            datos = json_desde_texto(r.text)
            productos = datos.get("productos", [])
            if not isinstance(productos, list):
                raise ValueError("'productos' no es una lista")
            return productos, fuentes
        except Exception as e:
            txt = str(e)
            print(f"   ⚠️ Fallo con {modelo}: {type(e).__name__} -> {txt[:300]}")
            if "404" in txt or "NOT_FOUND" in txt:
                continue   # el modelo no existe: se prueba el siguiente
            if "429" in txt or "RESOURCE_EXHAUSTED" in txt:
                print("   🛑 Cuota agotada. Se detiene el descubrimiento; se reintentará en la próxima ejecución.")
                raise SystemExit(0)
            if "google_search" in txt.lower() or "tool" in txt.lower() or "400" in txt or "403" in txt:
                print("   ℹ️ Puede que este modelo o tu cuenta no permitan la búsqueda de Google (en el nivel gratuito suele no estar "
                      "disponible para los modelos más nuevos). Revisa los límites en Google AI Studio.")
    return None, []


def validar(p, hoy):
    """Filtros de calidad. Devuelve (producto_normalizado | None, motivo_si_se_descarta)."""
    for campo in ("marca", "modelo_corto", "busqueda", "titulo", "especificaciones"):
        if not str(p.get(campo, "")).strip():
            return None, f"falta {campo}"
    if p.get("disponible_en_espana") is not True:
        return None, "no confirmado a la venta en España"
    if len(str(p["especificaciones"]).strip()) < MIN_CARACTERES_FICHA:
        return None, "ficha técnica demasiado corta"
    fecha = str(p.get("fecha_lanzamiento", "")).strip()
    m = re.match(r"^(\d{4})-(\d{2})$", fecha)
    if m and (int(m.group(1)), int(m.group(2))) > (hoy.year, hoy.month):
        return None, f"fecha de lanzamiento futura ({fecha}): posible rumor"
    try:
        precio = float(p.get("precio_eur") or 0)
    except (TypeError, ValueError):
        precio = 0
    return {
        "marca": str(p["marca"]).strip(),
        "modelo_corto": str(p["modelo_corto"]).strip(),
        "busqueda": str(p["busqueda"]).strip(),
        "titulo": str(p["titulo"]).strip(),
        "especificaciones": str(p["especificaciones"]).strip(),
        "precio": f"{precio:.2f}€" if precio > 0 else "Consultar",
    }, ""


def main():
    hoy = date.today()
    estado = cargar_json(RUTA_ESTADO, {})
    cola = cargar_json(RUTA_COLA, [])
    publicados = cargar_json(RUTA_PUBLICADOS, {})
    ids_conocidos = set(publicados.keys()) | {slugify(f"{c['marca']} {c['modelo_corto']}") for c in cola}
    total_nuevos = 0

    try:
        for categoria in CATEGORIAS_ACTIVAS:
            cfg = CATEGORIAS.get(categoria)
            if not cfg:
                print(f"⚠️ Categoría desconocida: {categoria}")
                continue
            marcas = cfg["marcas"]
            st = estado.setdefault(categoria, {"indice": 0, "fallos": 0, "vueltas": 0})

            for _ in range(MARCAS_POR_EJECUCION):
                marca = marcas[st["indice"] % len(marcas)]
                print(f"\n🔎 [{categoria}] Marca: {marca}  (posición {st['indice'] % len(marcas) + 1}/{len(marcas)})")

                conocidos_marca = [f"{c['marca']} {c['modelo_corto']}" for c in cola if c.get("categoria") == categoria]
                conocidos_marca += [f"{r['marca']} {r['modelo']}" for r in publicados.values() if isinstance(r, dict) and r.get("categoria") == categoria]
                productos, fuentes = pedir_modelos(cfg["descripcion"], marca, conocidos_marca)

                if productos is None:
                    st["fallos"] += 1
                    print(f"   ❌ Sin resultados válidos para {marca} (fallo {st['fallos']}/{MAX_FALLOS_MARCA}).")
                    if st["fallos"] < MAX_FALLOS_MARCA:
                        break   # se reintenta la misma marca en la próxima ejecución
                    print("   ➡️ Se pasa a la siguiente marca.")
                else:
                    añadidos = 0
                    for p in productos:
                        entrada, motivo = validar(p, hoy)
                        if not entrada:
                            print(f"   ⏭️ Descartado '{p.get('modelo_corto', '?')}': {motivo}")
                            continue
                        pid = slugify(f"{entrada['marca']} {entrada['modelo_corto']}")
                        if pid in ids_conocidos:
                            print(f"   ⏭️ Ya conocido: {entrada['marca']} {entrada['modelo_corto']}")
                            continue
                        entrada.update({
                            "categoria": categoria, "link_afiliado": "", "asin": "", "imagen": "",
                            "estado": "pendiente", "fuentes": fuentes[:6], "descubierto_el": hoy.isoformat(),
                        })
                        cola.append(entrada)
                        ids_conocidos.add(pid)
                        añadidos += 1
                        print(f"   ✅ Añadido a la cola: {entrada['marca']} {entrada['modelo_corto']} ({entrada['precio']})")
                    total_nuevos += añadidos
                    print(f"   📥 {añadidos} productos nuevos de {marca}.")

                st["fallos"] = 0
                st["indice"] += 1
                if st["indice"] % len(marcas) == 0:
                    st["vueltas"] += 1
                st["ultima_ejecucion"] = hoy.isoformat()

    finally:
        # Se guarda siempre, incluso si se detiene por falta de cuota, para no perder lo ya descubierto
        guardar_json(RUTA_COLA, cola)
        guardar_json(RUTA_ESTADO, estado)
    pendientes = sum(1 for c in cola if c.get("estado", "pendiente") == "pendiente")
    print(f"\n📊 Productos nuevos añadidos: {total_nuevos} | Pendientes de publicar en la cola: {pendientes}")


if __name__ == "__main__":
    main()
