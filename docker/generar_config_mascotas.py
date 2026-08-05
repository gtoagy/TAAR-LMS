"""Escribe el bloque de configuración de Mascotas para construir_cursos.py.

Son 52 lecciones y 41 videos; a mano es inviable sin equivocarse. Los videos de
los módulos 1-8 ya estaban en Vimeo (mapeo manual, verificado por título) y los
de los dos proyectos nuevos se leen del resultado de la subida.

  python docker/generar_config_mascotas.py
"""

import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = (
    r"C:\Users\RAZER\AppData\Local\Temp\claude"
    r"\C--Users-RAZER-documents-github-taar-lms"
    r"\47d3eaeb-1f0f-4be9-a9a5-4465326b0a6b\scratchpad"
)

# Índice de la lección en Disco -> video que ya estaba en Vimeo.
YA_EN_VIMEO = {
    0: "1210950170", 4: "1210950171", 5: "1210950173", 6: "1210950674",
    7: "1210955092", 9: "1210955455", 11: "1210966469", 12: "1210955541",
    13: "1210955664", 14: "1210955711", 15: "1210955751", 16: "1210966571",
    17: "1210956552", 18: "1210956625", 21: "1210956641", 22: "1210956727",
    23: "1210956731", 24: "1210957190", 25: "1210957360", 26: "1210957778",
}

# (título limpio del módulo, índices de sus lecciones). Se omite el 3, que es
# el "¡Completa tu perfil!" nativo de Disco.
MODULOS = [
    ("🐾 ¡Bienvenid@ al curso de Mascotas!", [0, 1, 2]),
    ('🧅 Método por capas', [4]),
    ("✍🏼 Todo acerca de los pelitos", [5, 6]),
    ("🎨 Colores vivos", [7, 8, 9, 10]),
    ("🤩 Tips de realismo", [11]),
    ("🦁 Ejercicios de pelaje", [12, 13, 14, 15, 16]),
    ("✏️ Bocetaje", [17]),
    ("💪🏼 Proyecto Final", [18, 19, 20, 21, 22, 23, 24, 25, 26, 27]),
    ("🐩 Proyecto #1 (Perrito en funda)", list(range(28, 37))),
    ("🐈 Proyecto #2 (Gato en lienzo)", list(range(37, 52))),
]

with open(os.path.join(BASE, "mascotas_disco.json"), encoding="utf-8") as fh:
    disco = json.load(fh)
por_titulo = {x["i"]: x["titulo"] for x in disco["lecciones"]}
tiene_video = {x["i"]: bool(x["video"]) for x in disco["lecciones"]}

# PowerShell escribe el JSON con BOM y además con los acentos doblemente
# codificados ("IntroducciÃ³n"): en Vimeo el nombre está bien, solo el volcado
# local viene roto, así que se deshace aquí.
with open(os.path.join(SCRATCH, "videos_nuevos.json"), encoding="utf-8-sig") as fh:
    subidos = json.load(fh)


def arreglar(texto: str) -> str:
    # cp1252, no latin-1: la "Ú" queda como "Ãš" y el 0x9A solo existe en cp1252.
    for codec in ("cp1252", "latin-1"):
        try:
            return texto.encode(codec).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return texto


subidos = {arreglar(k): v for k, v in subidos.items()}

# Los nombres en Vimeo son "NN. Mascotas P1 - <título de la lección>". Hay
# títulos repetidos entre los dos proyectos ("Ojos", "Tonos sombra"...), así que
# el prefijo P1/P2 es lo que decide a qué lección corresponde cada uno.
RANGOS = {"P1": range(28, 37), "P2": range(37, 52)}
nuevos = {}
for nombre, vid in subidos.items():
    m = re.match(r"^\d+\.\s*Mascotas (P[12])\s*-\s*(.+)$", nombre)
    if not m:
        continue
    proyecto, limpio = m.group(1), m.group(2).strip()
    for indice in RANGOS[proyecto]:
        if indice in nuevos:
            continue
        if (por_titulo.get(indice) or "").strip() == limpio:
            nuevos[indice] = vid
            break

faltan = [i for i, v in tiene_video.items() if v and i not in YA_EN_VIMEO and i not in nuevos]
if faltan:
    raise SystemExit(f"Sin video asignado: {faltan}")

lineas = []
for titulo, indices in MODULOS:
    partes = []
    for i in indices:
        vid = YA_EN_VIMEO.get(i) or nuevos.get(i)
        partes.append(f'{{"i": {i}, "vimeo": "{vid}"}}' if vid else f'{{"i": {i}}}')
    lineas.append(f'            ("{titulo}", [\n                ' + ",\n                ".join(partes) + "\n            ]),")

bloque = (
    '    {\n'
    '        "name": "curso-de-mascotas",\n'
    '        "title": "Curso de Mascotas",\n'
    '        "conservar_datos": True,\n'
    '        "datos": "mascotas_disco.json",\n'
    '        "materiales": "mascotas",\n'
    '        "modulos": [\n' + "\n".join(lineas) + "\n        ],\n"
    "    },"
)

destino = os.path.join(BASE, "_config_mascotas.txt")
with open(destino, "w", encoding="utf-8") as fh:
    fh.write(bloque)

print(f"{len(nuevos)} videos nuevos emparejados, {len(YA_EN_VIMEO)} ya estaban")
print(f"config en {destino}")
