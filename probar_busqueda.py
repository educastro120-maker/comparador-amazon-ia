"""
PRUEBA DE BÚSQUEDA (no publica nada, no toca WordPress)
Comprueba, modelo por modelo, qué pasa con tu clave de Gemini:
  A) llamada SIN búsqueda  -> si funciona, la clave y el modelo están bien.
  B) llamada CON Google Search (sin JSON) -> si falla aquí, el problema es la búsqueda, no el modelo ni el formato.
Imprime el error COMPLETO (el registro normal lo recortaba).
"""
import os
from google import genai
from google.genai import types

clave = os.environ.get("GEMINI_API_KEY", "").strip()
if not clave:
    raise SystemExit("Falta GEMINI_API_KEY")
client = genai.Client(api_key=clave)
MODELOS = [m.strip() for m in os.environ.get("PROBAR_MODELOS", "gemini-3.8-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite").split(",") if m.strip()]
PREGUNTA = "Busca en Google los 3 smartwatches más recientes lanzados en España este año y dame su nombre, precio y la fuente."


def fuentes(r):
    try:
        gm = r.candidates[0].grounding_metadata
        return [c.web.uri for c in (gm.grounding_chunks or []) if getattr(c, "web", None)]
    except Exception:
        return []


for modelo in MODELOS:
    print("\n" + "=" * 70 + f"\nMODELO: {modelo}")
    try:
        r = client.models.generate_content(model=modelo, contents="Responde solo: OK")
        print(f"A) SIN búsqueda: funciona -> {str(r.text).strip()[:60]!r}")
    except Exception as e:
        print(f"A) SIN búsqueda: ERROR -> {e}")
        continue
    try:
        r = client.models.generate_content(
            model=modelo, contents=PREGUNTA,
            config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())], temperature=0.2))
        f = fuentes(r)
        print(f"B) CON búsqueda: funciona. Fuentes de búsqueda devueltas: {len(f)}")
        for u in f[:5]:
            print("   -", u)
        print("   Texto:", str(r.text)[:600].replace("\n", " "))
    except Exception as e:
        print(f"B) CON búsqueda: ERROR COMPLETO -> {e}")
