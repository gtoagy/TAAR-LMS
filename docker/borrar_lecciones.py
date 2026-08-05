"""Borra lecciones sueltas de un curso, con su rastro.

Se usa para las lecciones que en Disco eran widgets de la propia plataforma
("¡Completa tu perfil!") y aquí no aportan nada.

Hay que quitar antes la fila de la tabla hija del capítulo: si se borra la
lección directamente, el capítulo queda apuntando a un enlace roto.

  env/bin/python /workspace/borrar_lecciones.py
"""

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

LECCIONES = [
    "retratos-1-3",  # ¡Completa tu perfil! — widget nativo de Disco
    # Restos de la estructura vieja de Mascotas: quedaron fuera de todos los
    # capítulos al rehacer el curso y solo las conservaba un registro de
    # progreso de nuestras propias pruebas en local.
    "mascotas-1-2",
    "mascotas-4-4",
    "mascotas-8-2",
]

# Todo lo que apunta a una lección y hay que limpiar antes de borrarla.
DEPENDENCIAS = [
    ("LMS Course Progress", "lesson"),
    ("LMS Lesson Note", "lesson"),
    ("LMS Assignment Submission", "lesson"),
    ("LMS Video Watch Duration", "lesson"),
]

for leccion in LECCIONES:
    if not frappe.db.exists("Course Lesson", leccion):
        print(f"{leccion}: ya no existe.")
        continue

    titulo = frappe.db.get_value("Course Lesson", leccion, "title")

    for doctype, campo in DEPENDENCIAS:
        if not frappe.db.exists("DocType", doctype):
            continue
        cuantos = frappe.db.count(doctype, {campo: leccion})
        if cuantos:
            frappe.db.delete(doctype, {campo: leccion})
            print(f"  {cuantos} registros de {doctype} eliminados")

    # Saca la lección de la tabla de su capítulo.
    for fila in frappe.get_all("Lesson Reference", filters={"lesson": leccion}, fields=["parent"]):
        capitulo = frappe.get_doc("Course Chapter", fila.parent)
        capitulo.set("lessons", [l for l in capitulo.lessons if l.lesson != leccion])
        capitulo.save(ignore_permissions=True)
        print(f"  quitada del capítulo {capitulo.title}")

    frappe.delete_doc("Course Lesson", leccion, ignore_permissions=True, force=True)
    print(f"{leccion} ({titulo}) borrada.\n")

frappe.db.commit()
print("Listo.")
