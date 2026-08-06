# -*- coding: utf-8 -*-
"""Saca las preguntas del formulario de Tally que hacía de quizz en Disco.

La lección "Quizz | Colores en las mascotas" no tenía cuestionario propio: era
un enlace a https://tally.so/r/3lEPEv. El formulario pide el correo antes de
enseñar nada, pero Tally deja el esquema completo en el __NEXT_DATA__ de la
página, así que basta con bajar el HTML y leerlo de ahí:

  curl -s -A "Mozilla/5.0" https://tally.so/r/3lEPEv -o _tally.html
  python extraer_tally.py

La respuesta correcta no viene marcada: se deduce de la lógica condicional, que
suma puntos (CALCULATE) cuando eliges la opción buena.
"""
import io, json, re

html = io.open("_tally.html", encoding="utf-8").read()
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
datos = json.loads(m.group(1))
bloques = datos["props"]["pageProps"]["blocks"]


def texto(payload):
    partes = []
    for x in (payload or {}).get("safeHTMLSchema") or []:
        if isinstance(x, list):
            if x and isinstance(x[0], str):
                partes.append(x[0])
        elif isinstance(x, str):
            partes.append(x)
    return re.sub(r"[ \t]+", " ", "".join(partes)).strip()


# Las opciones que suman puntos son las correctas.
buenas = set()
for b in bloques:
    if b["type"] != "CONDITIONAL_LOGIC":
        continue
    if not any(a.get("type") == "CALCULATE" for a in b["payload"].get("actions") or []):
        continue
    for c in b["payload"].get("conditionals") or []:
        v = (c.get("payload") or {}).get("value")
        if isinstance(v, str):
            buenas.add(v)

paginas = [[]]
for b in bloques:
    if b["type"] == "CONDITIONAL_LOGIC":
        continue
    if b["type"] == "PAGE_BREAK":
        paginas.append([])
    else:
        paginas[-1].append(b)

salida = []
for i, pg in enumerate(paginas):
    ops = [b for b in pg if b["type"] == "MULTIPLE_CHOICE_OPTION"]
    tex = [texto(b["payload"]) for b in pg if b["type"] in ("TEXT", "TITLE", "HEADING_2")]
    tex = [t for t in tex if t]
    ims = [im["url"] for b in pg if b["type"] == "IMAGE" for im in b["payload"].get("images") or []]
    salida.append({
        "pagina": i,
        "textos": tex,
        "imagenes": ims,
        "opciones": [{"texto": o["payload"]["text"].strip(), "correcta": o["uuid"] in buenas} for o in ops],
    })

io.open("tally_quiz_mascotas.json", "w", encoding="utf-8").write(json.dumps(salida, ensure_ascii=False, indent=2))
preguntas = [p for p in salida if p["opciones"]]
print(f"{len(paginas)} paginas, {len(preguntas)} preguntas")
for p in preguntas:
    ok = [o["texto"] for o in p["opciones"] if o["correcta"]]
    print(f"  pag {p['pagina']:>2}  {len(p['opciones'])} opciones  correcta={ok}")
