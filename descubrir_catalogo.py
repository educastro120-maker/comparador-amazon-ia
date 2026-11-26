"""
DESCUBRIR CATÁLOGO (versión con Tavily, 100 % gratuita)
=======================================================
Rellena la cola de productos (data/cola_catalogo.json) que luego publica auto_publisher.py.

Cómo funciona:
  1. Por cada categoría (smartphone, smartwatch) coge la SIGUIENTE marca de una lista y busca en internet
     con Tavily (plan gratuito: 1.000 créditos al mes, sin tarjeta) los modelos de esa marca a la venta en España.
  2. Le pasa a Gemini SOLO ese texto (sin herramienta de búsqueda: así es gratis) y le pide la ficha en JSON.
  3. Comprueba MECÁNICAMENTE que la ficha no se inventa nada:
       - el nombre del modelo aparece en el texto encontrado,
       - al menos el 80 % de las cifras de la ficha (mAh, pulgadas, Hz, gramos...) aparecen en ese texto,
       - hay indicios de venta en España (menciona España, Amazon.es o precios en euros),
       - el precio solo se acepta si aparece en el texto; si no, queda "Consultar".
     Lo que no pasa estos filtros se descarta.
  4. Guarda lo que pasa en la cola con estado "pendiente", con las direcciones web de las fuentes.

MODOS (variable DESCUBRIR_MODO):
  - "prueba": hace todo y lo muestra por pantalla, pero NO guarda nada (para la primera vez).
  - "si"    : guarda en la cola.

LÍMITES (léelos):
  - Tavily devuelve fragmentos de páginas, no fichas completas: las fichas serán más cortas que las de un catálogo
    hecho a mano. Las entradas se crean en borrador: revísalas.
  - No obtiene imágenes ni enlaces de afiliado (se rellenan en data/enlaces_manual.csv).
  - Gasto de créditos: por defecto 2 créditos por marca (búsqueda "advanced"). Se frena sola al llegar a TAVILY_MAX_MES.
"""

import os
import categorias
import re
import sys
import json
import time
import unicodedata
from datetime import date
import requests
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "").strip()
if not GEMINI_API_KEY:
    sys.exit("❌ Falta la variable de entorno GEMINI_API_KEY.")
if not TAVILY_API_KEY:
    print("ℹ️ No hay TAVILY_API_KEY (secreto de GitHub): se omite el descubrimiento de productos nuevos.")
    sys.exit(0)

client = genai.Client(api_key=GEMINI_API_KEY, http_options={"timeout": int(os.environ.get("GEMINI_TIMEOUT_MS", "120000"))})

# ==========================================
# AJUSTES
# ==========================================
CARPETA_DATOS = os.environ.get("CARPETA_DATOS", "data")
RUTA_COLA = os.path.join(CARPETA_DATOS, "cola_catalogo.json")
RUTA_PUBLICADOS = os.path.join(CARPETA_DATOS, "publicados.json")
RUTA_ESTADO = os.path.join(CARPETA_DATOS, "estado_descubrimiento.json")

MODO_PRUEBA = os.environ.get("DESCUBRIR_MODO", "si").strip().lower() == "prueba"
TAVILY_URL = os.environ.get("TAVILY_URL", "https://api.tavily.com/search")
TAVILY_PROFUNDIDAD = os.environ.get("TAVILY_PROFUNDIDAD", "advanced")      # "basic" = 1 crédito, "advanced" = 2 créditos (más texto)
TAVILY_MAX_RESULTADOS = int(os.environ.get("TAVILY_MAX_RESULTADOS", "8"))
TAVILY_MAX_MES = int(os.environ.get("TAVILY_MAX_MES", "900"))               # tope de seguridad (el plan gratuito da 1.000)

# Para ESTRUCTURAR texto (no hace falta el modelo más potente): primero los lite.
MODELOS = [m.strip() for m in os.environ.get("DISCOVERY_MODELS", "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.8-flash").split(",") if m.strip()]
COLA_MINIMA = int(os.environ.get("COLA_MINIMA", "12"))   # si una categoría ya tiene tantos pendientes, no se busca más (modo automático)
MARCAS_POR_EJECUCION = int(os.environ.get("MARCAS_POR_EJECUCION", "1"))
MODELOS_POR_MARCA = int(os.environ.get("MODELOS_POR_MARCA", "6"))
MAX_FALLOS_MARCA = 3
# Qué productos buscar: "mixto" (los que haya a la venta, como hasta ahora), "novedades" (lanzados hace menos de MESES_NOVEDAD meses)
# o "antiguos" (lanzados hace más de MESES_ANTIGUO meses y que aún se venden). Si la fuente no dice la fecha, no se descarta.
ENFOQUE = os.environ.get("DESCUBRIR_ENFOQUE", "mixto").strip().lower()
if ENFOQUE not in ("mixto", "novedades", "antiguos"):
    ENFOQUE = "mixto"
MESES_NOVEDAD = int(os.environ.get("MESES_NOVEDAD", "9"))
MESES_ANTIGUO = int(os.environ.get("MESES_ANTIGUO", "12"))
# Gama de precio a buscar (opcional): economica | media | alta. Solo se aceptan productos cuyo precio aparezca en las fuentes y caiga en el tramo.
GAMA = os.environ.get("DESCUBRIR_GAMA", "").strip().lower().replace("é", "e").replace("ó", "o")
if GAMA not in ("economica", "media", "alta"):
    GAMA = ""
RANGOS_GAMA = {   # euros: (mínimo, máximo); los mismos tramos que tus etiquetas de precio
    "smartphone": {"economica": (0, 200), "media": (200, 500), "alta": (500, 10**9)},
    "smartwatch": {"economica": (0, 100), "media": (100, 300), "alta": (300, 10**9)},
}
def consultas_gama(categoria, d, gama):
    """Búsquedas por precio (sin marca) para rellenar una gama concreta."""
    lo, hi = RANGOS_GAMA[categoria][gama]
    if gama == "economica":
        return [f"mejores {d} baratos por menos de {int(hi)} euros", f"{d} económicos Amazon.es más vendidos menos de {int(hi)} €",
                f"{d} baratos calidad precio hasta {int(hi * 0.75)} euros", f"mejores {d} por menos de {int(hi * 0.6)} euros",
                f"{d} gama de entrada menos de {int(hi)} euros análisis", f"{d} baratos Xiaomi Redmi Poco Samsung Galaxy A Motorola moto g precio"]
    if gama == "media":
        return [f"mejores {d} gama media entre {int(lo)} y {int(hi)} euros", f"{d} calidad precio {int(lo)} {int(hi)} euros Amazon.es",
                f"mejores {d} por menos de {int(hi)} euros", f"{d} gama media más vendidos España",
                f"{d} gama media Samsung Galaxy A5 Xiaomi Redmi Note Poco Motorola Edge precio", f"{d} gama media análisis y precio"]
    return [f"mejores {d} gama alta más de {int(lo)} euros", f"{d} premium más vendidos España precio"]


TEXTO_GAMA = {"economica": "económicos baratos precio bajo", "media": "gama media calidad precio", "alta": "gama alta premium"}
MIN_CARACTERES_FICHA = int(os.environ.get("MIN_CARACTERES_FICHA", "300"))
MIN_PORCENTAJE_CIFRAS = float(os.environ.get("MIN_PORCENTAJE_CIFRAS", "0.8"))
MIN_CIFRAS_FICHA = 4
MAX_CONTEXTO = 16000
_pedidas = [c.strip().lower() for c in os.environ.get("DESCUBRIR_CATEGORIAS", "").split(",") if c.strip()]
if not _pedidas or _pedidas == ["todas"]:
    CATEGORIAS_ACTIVAS = [k for k, v in categorias.cargar().items() if v.get("activa", True)]   # las activas de data/categorias.json
else:
    CATEGORIAS_ACTIVAS = _pedidas   # a mano: cualquier categoría, esté o no en el archivo (incluso pausada)

class SinCupo(Exception):
    """Tavily no permite más búsquedas (límite del plan o clave no válida)."""


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


# ---------- Verificación mecánica de cifras ----------
def _normalizar_cifra(c):
    c = c.replace(",", ".")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", c):   # 5.000 -> 5000 (separador de miles)
        c = c.replace(".", "")
    return c.rstrip(".")


def cifras_de(texto):
    """Números de al menos 2 caracteres (los de 1 dígito, como el '5' de 5G, no demuestran nada)."""
    brutas = re.findall(r"\d+(?:[.,]\d+)*", str(texto))
    return {n for n in (_normalizar_cifra(b) for b in brutas) if len(n) >= 2}


def verificar_ficha(producto, contexto):
    """Devuelve (True, '') si la ficha se apoya en el texto encontrado; si no, (False, motivo)."""
    palabras_contexto = set(slugify(contexto).split("-"))
    palabras_modelo = {w for w in slugify(f"{producto['marca']} {producto['modelo_corto']}").split("-") if w}
    if not palabras_modelo <= palabras_contexto:
        return False, "el nombre del modelo no aparece en el texto encontrado"
    ficha = cifras_de(producto["especificaciones"])
    if len(ficha) < MIN_CIFRAS_FICHA:
        return False, f"la ficha trae pocas cifras ({len(ficha)})"
    en_texto = cifras_de(contexto)
    verificadas = ficha & en_texto
    ratio = len(verificadas) / len(ficha)
    if ratio < MIN_PORCENTAJE_CIFRAS:
        sin = sorted(ficha - en_texto)[:6]
        return False, f"solo {ratio:.0%} de las cifras están en las fuentes (sin respaldo: {', '.join(sin)})"
    ctx = contexto.lower()
    if not any(k in ctx for k in ("españa", "espana", "amazon.es", "€", " eur")):
        return False, "las fuentes no indican venta en España"
    return True, ""


# ---------- Tavily ----------
def _creditos_por_busqueda():
    return 2 if TAVILY_PROFUNDIDAD == "advanced" else 1


def buscar_tavily(consulta, estado):
    """Una búsqueda. Devuelve la lista de resultados [{title, url, content}]. Lanza SinCupo si ya no se puede."""
    mes = date.today().strftime("%Y-%m")
    uso = estado.setdefault("tavily", {})
    if uso.get("mes") != mes:
        uso.update({"mes": mes, "creditos": 0})
    if uso["creditos"] + _creditos_por_busqueda() > TAVILY_MAX_MES:
        raise SinCupo(f"tope mensual propio alcanzado ({uso['creditos']}/{TAVILY_MAX_MES} créditos)")

    cuerpo = {"query": consulta, "search_depth": TAVILY_PROFUNDIDAD, "max_results": TAVILY_MAX_RESULTADOS,
              "include_answer": False, "include_raw_content": False}
    if TAVILY_PROFUNDIDAD == "advanced":
        cuerpo["chunks_per_source"] = 3
    cabeceras = {"Authorization": f"Bearer {TAVILY_API_KEY}", "Content-Type": "application/json"}
    r = None
    for intento in (1, 2):
        try:
            r = requests.post(TAVILY_URL, headers=cabeceras, json=cuerpo, timeout=60)
        except requests.RequestException as err:
            print(f"   ⚠️ Error de conexión con Tavily: {err}")
            return None
        if r.status_code == 400 and intento == 1:   # por si algún parámetro opcional no lo acepta tu plan: se repite con lo mínimo
            cuerpo = {"query": consulta, "max_results": TAVILY_MAX_RESULTADOS}
            continue
        break
    if r.status_code in (401, 403):
        raise SinCupo("la clave TAVILY_API_KEY no es válida (revisa el secreto de GitHub)")
    if r.status_code in (429, 432, 433):
        raise SinCupo(f"Tavily indica que no quedan créditos o se ha superado el límite ({r.status_code})")
    if r.status_code != 200:
        print(f"   ⚠️ Tavily respondió {r.status_code}: {r.text[:200]}")
        return None
    uso["creditos"] += _creditos_por_busqueda()
    try:
        return r.json().get("results", [])
    except ValueError:
        return None


def construir_contexto(resultados):
    trozos, total = [], 0
    for i, res in enumerate(resultados, 1):
        texto = f"[{i}] {res.get('title', '')}\nURL: {res.get('url', '')}\n{str(res.get('content', ''))[:1800]}\n"
        if total + len(texto) > MAX_CONTEXTO:
            break
        trozos.append(texto)
        total += len(texto)
    return "\n".join(trozos)


# ---------- Gemini (SIN búsqueda: gratis) ----------
def estructurar_con_gemini(descripcion, marca, conocidos, contexto, por_tema=False):
    hoy = date.today().strftime("%d/%m/%Y")
    lista_conocidos = "\n".join(f"- {c}" for c in conocidos[:80]) or "- (ninguno todavía)"
    sobre = (f'el tema "{marca}" (categoría: {descripcion})' if por_tema else f'la marca "{marca}" (categoría: {descripcion})')
    de_quien = "los modelos de la categoría (de cualquier marca)" if por_tema else "los modelos de la marca"
    enfoque_prompt = {"novedades": f"Da prioridad a los modelos lanzados en los últimos {MESES_NOVEDAD} meses. ",
                      "antiguos": f"Da prioridad a modelos lanzados hace más de {MESES_ANTIGUO} meses que el texto presente como todavía a la venta. "}.get(ENFOQUE, "")
    prompt = f"""Hoy es {hoy}. Tienes TEXTO ENCONTRADO EN INTERNET sobre {sobre}. Usa EXCLUSIVAMENTE ese texto; no uses nada de memoria.

Extrae {de_quien} que el texto presenta como a la venta en España (o con precio en euros). Excluye los que ya tengo:
{lista_conocidos}

{enfoque_prompt}Devuelve como máximo {MODELOS_POR_MARCA} modelos. No incluyas rumores ni productos sin lanzar. Si el texto no permite un producto con datos concretos, no lo incluyas. Si no hay modelos nuevos, devuelve una lista vacía.

Responde ÚNICAMENTE con un JSON válido con esta forma:
{{"productos": [{{"marca": "...", "modelo_corto": "...", "busqueda": "...", "titulo": "...", "especificaciones": "...", "precio_eur": 0, "disponible_en_espana": true, "fecha_lanzamiento": "AAAA-MM"}}]}}

Reglas:
- modelo_corto: nombre del modelo SIN la marca (por ejemplo "Galaxy A57 5G").
- busqueda: marca + modelo + variante principal, para buscar en Amazon.es.
- titulo: título descriptivo en español al estilo de Amazon.es (marca, modelo y 2-3 características clave del texto).
- especificaciones: ficha en español de 300 a 1200 caracteres, redactada con tus palabras (NO copies frases del texto) y con SOLO cifras que aparezcan literalmente en el texto. Si un dato no está en el texto, omítelo. No inventes ni redondees cifras.
- precio_eur: precio en euros SOLO si aparece en el texto (número). Si no, 0.
- disponible_en_espana: true solo si el texto lo indica (España, Amazon.es o precio en euros).
- fecha_lanzamiento: AAAA-MM si aparece en el texto; si no, "".

TEXTO ENCONTRADO:
{contexto}"""
    for ronda in (1, 2):
        sobrecarga = False
        for modelo in MODELOS:
            try:
                print(f"   🤖 Estructurando con {modelo}...")
                r = client.models.generate_content(
                    model=modelo, contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1, max_output_tokens=8192))
                productos = json_desde_texto(r.text).get("productos", [])
                if not isinstance(productos, list):
                    raise ValueError("'productos' no es una lista")
                return productos
            except Exception as e:
                txt = str(e)
                print(f"   ⚠️ Fallo con {modelo}: {type(e).__name__} -> {txt[:200]}")
                if "503" in txt or "UNAVAILABLE" in txt:
                    sobrecarga = True
                time.sleep(3)   # 404, 429, 503...: se prueba el siguiente modelo
        if ronda == 1 and sobrecarga:
            print("   ⏳ Los modelos están saturados (503): se espera 45 segundos y se reintenta una vez.")
            time.sleep(45)
        else:
            break
    return None


def validar(p, hoy, contexto, categoria=None):
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
    if m and ENFOQUE != "mixto":
        meses = (hoy.year - int(m.group(1))) * 12 + (hoy.month - int(m.group(2)))
        if ENFOQUE == "novedades" and meses > MESES_NOVEDAD:
            return None, f"no es una novedad (lanzado en {fecha}, hace {meses} meses)"
        if ENFOQUE == "antiguos" and meses < MESES_ANTIGUO:
            return None, f"es demasiado reciente para el enfoque «antiguos» (lanzado en {fecha})"
    ok, motivo = verificar_ficha(p, contexto)
    if not ok:
        return None, motivo
    try:
        precio = float(p.get("precio_eur") or 0)
    except (TypeError, ValueError):
        precio = 0
    if precio > 0 and _normalizar_cifra(f"{precio:g}") not in cifras_de(contexto) and _normalizar_cifra(f"{precio:.2f}") not in cifras_de(contexto):
        precio = 0   # un precio que no está en las fuentes no se acepta
    rango = RANGOS_GAMA.get(categoria or "", {}).get(GAMA) if GAMA else None
    if rango:
        if precio <= 0:
            return None, f"el precio no aparece en las fuentes y se busca la gama {GAMA}"
        if not (rango[0] <= precio < rango[1]):
            return None, f"precio {precio:g} € fuera de la gama {GAMA}"
    return {
        "marca": str(p["marca"]).strip(),
        "modelo_corto": str(p["modelo_corto"]).strip(),
        "busqueda": str(p["busqueda"]).strip(),
        "titulo": str(p["titulo"]).strip(),
        "especificaciones": str(p["especificaciones"]).strip(),
        "precio": f"{precio:.2f}€" if precio > 0 else "Consultar",
        "fecha_lanzamiento": fecha if m else "",   # AAAA-MM; alimenta la página de novedades
    }, ""


def main():
    hoy = date.today()
    estado = cargar_json(RUTA_ESTADO, {})
    cola = cargar_json(RUTA_COLA, [])
    publicados = cargar_json(RUTA_PUBLICADOS, {})
    ids_conocidos = set(publicados.keys()) | {slugify(f"{c['marca']} {c['modelo_corto']}") for c in cola}
    total_nuevos = 0
    if MODO_PRUEBA:
        print("🧪 MODO PRUEBA: se muestra todo pero NO se guarda nada.\n")

    try:
        for categoria in CATEGORIAS_ACTIVAS:
            cfg = categorias.info(categoria)   # si no está en el archivo: categoría genérica con búsquedas libres
            pendientes_cat = sum(1 for c in cola if c.get("categoria") == categoria and c.get("estado", "pendiente") == "pendiente")
            minimo = int(cfg.get("cola_minima") or COLA_MINIMA)
            if not _pedidas and pendientes_cat >= minimo:   # automático: no se gastan créditos si ya hay suficiente cola
                print(f"⏭️ [{categoria}] ya hay {pendientes_cat} productos pendientes en la cola (mínimo {minimo}): no se busca hoy.")
                continue
            marcas = list(cfg.get("marcas") or [])
            por_tema = not marcas
            if por_tema:   # sin marcas: búsquedas libres (de data/categorias.json o genéricas)
                d = cfg["descripcion"]
                marcas = list(cfg.get("consultas") or [f"mejores {d} calidad precio", f"{d} más vendidos Amazon.es",
                                                      f"{d} novedades", f"{d} gama alta", f"{d} económicos"])
            clave_estado = categoria
            if GAMA and categoria in RANGOS_GAMA:   # con gama: búsquedas por precio, sin depender de marcas
                marcas, por_tema = consultas_gama(categoria, cfg["descripcion"], GAMA), True
                clave_estado = f"{categoria}:{GAMA}"
            st = estado.setdefault(clave_estado, {"indice": 0, "fallos": 0, "vueltas": 0})

            for _ in range(int(os.environ.get('DESCUBRIR_MARCAS') or cfg.get('marcas_por_ejecucion') or MARCAS_POR_EJECUCION)):
                marca = marcas[st["indice"] % len(marcas)]
                print(f"\n🔎 [{categoria}] Marca: {marca}  (posición {st['indice'] % len(marcas) + 1}/{len(marcas)})")

                conocidos = [f"{c['marca']} {c['modelo_corto']}" for c in cola if c.get("categoria") == categoria]
                conocidos += [f"{r['marca']} {r['modelo']}" for r in publicados.values() if isinstance(r, dict) and r.get("categoria") == categoria]

                if ENFOQUE == "novedades":
                    extra = f"últimos lanzamientos novedades {hoy.year}"
                elif ENFOQUE == "antiguos":
                    extra = f"modelos de {hoy.year - 3} {hoy.year - 2} {hoy.year - 1} generaciones anteriores todavía a la venta rebajados"
                else:
                    extra = str(hoy.year)
                if GAMA and categoria in RANGOS_GAMA:
                    extra = f"{extra} {TEXTO_GAMA[GAMA]}"
                consulta = (f"{marca} España precio características técnicas {extra}" if por_tema
                            else f"{marca} {cfg['descripcion']} modelos disponibles en España precio características técnicas {extra}")
                resultados = buscar_tavily(consulta, estado)
                productos, contexto = None, ""
                if resultados:
                    contexto = construir_contexto(resultados)
                    print(f"   🌐 Tavily: {len(resultados)} resultados, {len(contexto)} caracteres de texto "
                          f"(créditos este mes: {estado['tavily']['creditos']}/{TAVILY_MAX_MES}).")
                    productos = estructurar_con_gemini(cfg["descripcion"], marca, conocidos, contexto, por_tema)
                else:
                    print("   ⚠️ Tavily no devolvió resultados.")

                if productos is None:
                    st["fallos"] += 1
                    print(f"   ❌ Sin resultados válidos para {marca} (fallo {st['fallos']}/{MAX_FALLOS_MARCA}).")
                    if st["fallos"] < MAX_FALLOS_MARCA:
                        break   # se reintenta la misma marca en la próxima ejecución
                    print("   ➡️ Se pasa a la siguiente marca.")
                else:
                    fuentes = [r.get("url", "") for r in resultados if r.get("url")][:6]
                    añadidos = 0
                    for p in productos:
                        entrada, motivo = validar(p, hoy, contexto, categoria)
                        if not entrada:
                            print(f"   ⏭️ Descartado '{p.get('modelo_corto', '?')}': {motivo}")
                            continue
                        pid = slugify(f"{entrada['marca']} {entrada['modelo_corto']}")
                        if pid in ids_conocidos:
                            print(f"   ⏭️ Ya conocido: {entrada['marca']} {entrada['modelo_corto']}")
                            continue
                        entrada.update({
                            "categoria": categoria, "link_afiliado": "", "asin": "", "imagen": "",
                            "estado": "pendiente", "fuentes": fuentes, "descubierto_el": hoy.isoformat(),
                            "verificar": True,
                        })
                        cola.append(entrada)
                        ids_conocidos.add(pid)
                        añadidos += 1
                        print(f"   ✅ {'(prueba) ' if MODO_PRUEBA else ''}Añadido a la cola: {entrada['marca']} {entrada['modelo_corto']} ({entrada['precio']})")
                        if MODO_PRUEBA:
                            print(f"      Ficha: {entrada['especificaciones'][:400]}")
                    total_nuevos += añadidos
                    print(f"   📥 {añadidos} productos nuevos de {marca}.")

                st["fallos"] = 0
                st["indice"] += 1
                if st["indice"] % len(marcas) == 0:
                    st["vueltas"] += 1
                st["ultima_ejecucion"] = hoy.isoformat()
    except SinCupo as err:
        print(f"🛑 Se detiene el descubrimiento: {err}. Se reintentará en la próxima ejecución.")
    finally:
        if MODO_PRUEBA:
            print("\n🧪 Prueba terminada: no se ha guardado nada.")
        else:
            guardar_json(RUTA_COLA, cola)
            guardar_json(RUTA_ESTADO, estado)
    pendientes = sum(1 for c in cola if c.get("estado", "pendiente") == "pendiente")
    print(f"\n📊 Productos nuevos {'detectados' if MODO_PRUEBA else 'añadidos'}: {total_nuevos} | Pendientes de publicar en la cola: {pendientes}")


if __name__ == "__main__":
    main()
