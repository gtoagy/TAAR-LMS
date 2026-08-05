"""Pone como portada de cada curso la imagen que usa Disco en su catálogo.

Las portadas se descargan con el scraper (materiales/portadas/) y aquí se
redimensionan y se suben. Van como archivo PÚBLICO: la portada se ve en el
catálogo, que es accesible sin iniciar sesión.

  env/bin/python /workspace/aplicar_portadas.py
"""

import io
import json
import os

import frappe
from PIL import Image

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

PORTADAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "materiales", "portadas")

# La original de Mascotas pesa 23 MB; a este ancho ninguna pasa de ~300 KB y se
# ve igual de bien en la tarjeta del catálogo.
ANCHO_MAXIMO = 1600

# archivo descargado -> curso del LMS
MAPA = {
    "teoria-del-color.png": "teoria-del-color",
    "mascotas.jpeg": "curso-de-mascotas",
    "retratos.png": "curso-de-retratos",
    "proyecto-rocky-perrito-en-lienzo.png": "proyecto-rocky",
    "proyecto-retrato-en-funda.jpeg": "retrato-en-fundas",
    "workshop-lolo-perrito-pelo-corto-funda.png": "workshop-perrito-pelo-corto",
    "el-angel-caido.png": "el-angel-caido",
    "la-noche-estrellada.png": "la-noche-estrellada",
    "encuentra-el-valor-de-tu-arte.png": "workshop-el-valor-de-tu-obra",
    "creacion-de-videos-virales.png": "workshop-videos-virales",
    "arte-en-fundas.png": "resina-en-fundas",
    "nenufares.png": "nenufares",
    "workshop-pelaje.png": "workshop-pelaje",
}


def optimizar(ruta: str) -> tuple:
    """Devuelve (bytes, nombre) de la imagen lista para subir."""
    img = Image.open(ruta)
    if img.mode in ("RGBA", "P", "LA"):
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        fondo.paste(img, mask=img.convert("RGBA").split()[-1])
        img = fondo
    elif img.mode != "RGB":
        img = img.convert("RGB")

    if img.width > ANCHO_MAXIMO:
        alto = round(img.height * ANCHO_MAXIMO / img.width)
        img = img.resize((ANCHO_MAXIMO, alto), Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    nombre = os.path.splitext(os.path.basename(ruta))[0] + ".jpg"
    return buffer.getvalue(), nombre


for archivo, curso in MAPA.items():
    ruta = os.path.join(PORTADAS, archivo)
    if not os.path.exists(ruta):
        print(f"AVISO: falta {archivo}")
        continue
    if not frappe.db.exists("LMS Course", curso):
        print(f"AVISO: el curso {curso} no existe")
        continue

    datos, nombre = optimizar(ruta)

    existente = frappe.db.get_value(
        "File", {"file_name": nombre, "attached_to_name": curso}, "file_url"
    )
    if existente:
        url = existente
    else:
        url = (
            frappe.get_doc(
                {
                    "doctype": "File",
                    "file_name": nombre,
                    "content": datos,
                    "is_private": 0,
                    "attached_to_doctype": "LMS Course",
                    "attached_to_name": curso,
                    "attached_to_field": "image",
                }
            )
            .insert(ignore_permissions=True)
            .file_url
        )

    frappe.db.set_value("LMS Course", curso, "image", url, update_modified=False)
    titulo = frappe.db.get_value("LMS Course", curso, "title")
    print(f"{titulo:<34} <- {nombre} ({len(datos) // 1024} KB)")

frappe.db.commit()
print("\nListo.")
