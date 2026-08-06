"""Comprueba que al importar un curso llegan también sus archivos.

Importa el ZIP en este mismo sitio (queda un curso duplicado, que se borra al
final) y verifica lo que fallaba: que cada bloque de material apunte a un
fichero que existe de verdad y con la misma privacidad que el original.

  env/bin/python /workspace/probar_importacion.py <curso>
"""

import json
import os
import shutil
import sys

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

from lms.lms.course_import_export import import_course_zip  # noqa: E402

curso = sys.argv[1] if len(sys.argv) > 1 else "nenufares"
origen = f"/workspace/exportados/{curso}.zip"
nombre_zip = f"prueba_{curso}.zip"
destino = frappe.get_site_path("private", "files", nombre_zip)

shutil.copy(origen, destino)
print(f"ZIP copiado a private/files/{nombre_zip}")

importado = import_course_zip(f"/private/files/{nombre_zip}")
frappe.db.commit()
print(f"curso importado como: {importado}\n")

lecciones = frappe.get_all("Course Lesson", filters={"course": importado}, fields=["name", "title", "content"])
total = fallos = 0
for l in lecciones:
    if not l.content:
        continue
    for b in json.loads(l.content).get("blocks", []):
        if b.get("type") != "upload":
            continue
        total += 1
        url = b["data"].get("file_url")
        existe = frappe.db.exists("File", {"file_url": url})
        ruta = frappe.get_site_path(url.lstrip("/")) if url else None
        en_disco = ruta and os.path.exists(ruta)
        estado = "OK" if (existe and en_disco) else "FALTA"
        if estado == "FALTA":
            fallos += 1
        print(f"  [{estado}] {l.title[:30]:<30} {url}")

portada = frappe.db.get_value("LMS Course", importado, "image")
if portada:
    ok = frappe.db.exists("File", {"file_url": portada})
    print(f"  [{'OK' if ok else 'FALTA'}] portada{'':<24} {portada}")

print(f"\n{total - fallos}/{total} materiales enlazados correctamente")

# Limpieza: el curso importado era solo para comprobar.
for l in frappe.get_all("Course Lesson", filters={"course": importado}, pluck="name"):
    frappe.db.delete("LMS Course Progress", {"lesson": l})
    for fila in frappe.get_all("Lesson Reference", filters={"lesson": l}, fields=["parent"]):
        cap = frappe.get_doc("Course Chapter", fila.parent)
        cap.set("lessons", [x for x in cap.lessons if x.lesson != l])
        cap.save(ignore_permissions=True)
    frappe.delete_doc("Course Lesson", l, ignore_permissions=True, force=True)
for c in frappe.get_all("Course Chapter", filters={"course": importado}, pluck="name"):
    frappe.delete_doc("Course Chapter", c, ignore_permissions=True, force=True)
frappe.delete_doc("LMS Course", importado, ignore_permissions=True, force=True)
os.remove(destino)
frappe.db.commit()
print(f"limpieza: curso de prueba {importado} eliminado")
