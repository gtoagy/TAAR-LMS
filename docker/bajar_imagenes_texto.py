"""Descarga las imágenes que van incrustadas dentro del texto de las lecciones.

No son adjuntos: son <img> dentro del cuerpo, y sin ellas el conversor deja un
bloque "imagen_pendiente" que el editor no sabe pintar.

  python docker/bajar_imagenes_texto.py <json> <carpeta-materiales>
  python docker/bajar_imagenes_texto.py mascotas_disco.json mascotas
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
nombre_json, carpeta = sys.argv[1], sys.argv[2]

with open(os.path.join(BASE, nombre_json), encoding="utf-8") as fh:
    datos = json.load(fh)

destino = os.path.join(BASE, "materiales", carpeta, "img")
os.makedirs(destino, exist_ok=True)

mapa = {}
for leccion in datos["lecciones"]:
    urls = re.findall(r'<img[^>]+src="([^"]+)"', leccion.get("html") or "")
    if not urls:
        continue
    archivos = []
    for orden, url in enumerate(urls, start=1):
        ruta = urllib.parse.urlparse(url).path
        crudo = urllib.parse.unquote(ruta.split("/")[-1])
        extension = os.path.splitext(crudo)[1] or ".jpg"
        archivo = f"{leccion['i']:02d}_{orden}{extension}"
        salida = os.path.join(destino, archivo)
        if not os.path.exists(salida):
            peticion = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(peticion, timeout=120) as respuesta, open(salida, "wb") as fh:
                fh.write(respuesta.read())
        archivos.append(archivo)
        print(f"  {archivo} ({os.path.getsize(salida) // 1024} KB)  <- {leccion['titulo'][:32]}")
    mapa[str(leccion["i"])] = archivos

with open(os.path.join(destino, "mapa.json"), "w", encoding="utf-8") as fh:
    json.dump(mapa, fh, ensure_ascii=False, indent=1)

print(f"\n{sum(len(v) for v in mapa.values())} imágenes en {len(mapa)} lecciones")
