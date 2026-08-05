"""Genera el script de PowerShell que sube a Vimeo una tanda de videos.

Toma el escaneo de Disco y la plantilla scratchpad/subir-vimeo.ps1, y sustituye
la lista $VIDEOS por la de este curso. Evita escribir a mano veinte bloques.

  python docker/generar_subida.py
"""

import json
import os
import re
import unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = (
    r"C:\Users\RAZER\AppData\Local\Temp\claude"
    r"\C--Users-RAZER-documents-github-taar-lms"
    r"\47d3eaeb-1f0f-4be9-a9a5-4465326b0a6b\scratchpad"
)

CARPETA_VIMEO = "/users/261186210/projects/29945889"  # Mascotas
# Índices del Proyecto #1 (perrito en funda); el resto son del #2 (gato).
PROYECTO_1 = {28, 30, 31, 32, 33, 34, 35}
DESDE = 28  # las lecciones anteriores ya estaban en Vimeo
NUMERO_INICIAL = 21  # la carpeta ya tiene 21 videos


def slug(texto: str) -> str:
    limpio = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", limpio.lower()).strip("-")[:40]


with open(os.path.join(BASE, "mascotas_disco.json"), encoding="utf-8") as fh:
    datos = json.load(fh)

bloques = []
numero = NUMERO_INICIAL
for leccion in datos["lecciones"]:
    if leccion["i"] < DESDE or not leccion["video"]:
        continue
    numero += 1
    proyecto = "P1" if leccion["i"] in PROYECTO_1 else "P2"
    nombre = f"{numero:02d}. Mascotas {proyecto} - {leccion['titulo']}".replace('"', "")
    archivo = f"mascotas-{leccion['i']:02d}-{slug(leccion['titulo'])}.mp4"
    bloques.append(
        '    @{ Archivo = "$Base\\' + archivo + '"\n'
        f'       Nombre  = "{nombre}"\n'
        f'       Carpeta = "{CARPETA_VIMEO}" '
        "}"
    )

lista = "$VIDEOS = @(\n" + ",\n".join(bloques) + "\n)"

with open(os.path.join(SCRATCH, "subir-vimeo.ps1"), encoding="utf-8") as fh:
    plantilla = fh.read()

# re.sub interpretaría \c, \m... del reemplazo como escapes: se parte a mano.
inicio = plantilla.index("$VIDEOS = @(")
fin = plantilla.index("\n)", inicio) + 2
nuevo = plantilla[:inicio] + lista + plantilla[fin:]

destino = os.path.join(SCRATCH, "subir-mascotas.ps1")
with open(destino, "w", encoding="utf-8", newline="\r\n") as fh:
    fh.write(nuevo)

print(f"{len(bloques)} videos en {destino}")
for b in bloques[:3]:
    print(b.splitlines()[1].strip())
