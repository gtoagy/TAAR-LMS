"""Recoge lo que deja el scraper del navegador: mueve el JSON y baja sus PDFs.

Chrome no sobrescribe las descargas (crea "nombre (1).json"), así que siempre se
coge la más reciente, no la de nombre limpio.

  python docker/importar_escaneo.py <json> <carpeta-materiales>
  python docker/importar_escaneo.py virales_disco.json virales
"""

import glob
import json
import os
import re
import sys
import urllib.parse
import urllib.request

DESCARGAS = os.path.expanduser("~/Downloads")
BASE = os.path.dirname(os.path.abspath(__file__))

nombre_json, carpeta = sys.argv[1], sys.argv[2]
raiz = os.path.splitext(nombre_json)[0]

candidatos = glob.glob(os.path.join(DESCARGAS, f"{raiz}*.json"))
if not candidatos:
    raise SystemExit(f"No encuentro ninguna descarga que empiece por {raiz}")
origen = max(candidatos, key=os.path.getmtime)
print(f"usando {os.path.basename(origen)}")

destino_json = os.path.join(BASE, nombre_json)
with open(origen, encoding="utf-8") as fh:
    datos = json.load(fh)
with open(destino_json, "w", encoding="utf-8") as fh:
    json.dump(datos, fh, ensure_ascii=False, indent=1)

destino = os.path.join(BASE, "materiales", carpeta)
os.makedirs(destino, exist_ok=True)
mapa = {}
for leccion in datos["lecciones"]:
    for url in leccion["archivos"]:
        ruta = urllib.parse.urlparse(url).path
        crudo = urllib.parse.unquote(ruta.split("/")[-1])
        # Disco añade un uuid al nombre del archivo; se quita para que quede legible.
        limpio = re.sub(
            r"_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(\.[A-Za-z0-9]+)$",
            r"\1",
            crudo,
        )
        archivo = f"{leccion['i']:02d}_{limpio}"
        salida = os.path.join(destino, archivo)
        if not os.path.exists(salida):
            peticion = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(peticion, timeout=120) as respuesta, open(salida, "wb") as fh:
                fh.write(respuesta.read())
        mapa[str(leccion["i"])] = archivo
        print(f"  {archivo} ({os.path.getsize(salida) // 1024} KB)")

with open(os.path.join(destino, "mapa.json"), "w", encoding="utf-8") as fh:
    json.dump(mapa, fh, ensure_ascii=False, indent=1)

print(f"\n{len(datos['lecciones'])} lecciones, {len(mapa)} archivos")
for m in datos.get("modulos") or []:
    print(f"  módulo: {m['modulo']} ({m['n']})")
for x in datos["lecciones"]:
    texto = re.sub("<[^>]+>", "", x["html"] or "").strip()
    tiene = "texto" if texto and "Write something" not in texto else "-"
    print(f"  {x['i']:>2} [{x['tipo']:<9}] {x['titulo'][:40]:<40} video={'si' if x['video'] else '-':<3} {tiene}")
