"""Inspecciona el contenido real de las lecciones sin video de Retratos.

Sirve para ver qué bloques de EditorJS tiene cada una y decidir cuáles pasan a
ser tareas (LMS Assignment) y cuáles quedan como descargas.

  env/bin/python /workspace/inspeccionar_lecciones.py
"""

import json

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

CURSO = "curso-de-retratos"

lecciones = frappe.get_all(
    "Course Lesson",
    filters={"course": CURSO},
    fields=["name", "title", "content"],
    order_by="chapter asc, idx asc",
)

print(f"{len(lecciones)} lecciones en {CURSO}\n")

for l in lecciones:
    tipos = []
    if l.content:
        try:
            for b in json.loads(l.content).get("blocks", []):
                tipos.append(b.get("type"))
        except Exception as e:  # contenido no-JSON (body markdown antiguo)
            tipos = [f"<error: {e}>"]
    # Solo interesan las que no tienen video embebido: son las candidatas a
    # tarea, examen o descarga.
    if "embed" not in tipos:
        print(f"--- {l.name} | {l.title}")
        print(f"    bloques: {tipos}")
        print(f"    {(l.content or '')[:400]}\n")

print("\n=== Assignments existentes ===")
for a in frappe.get_all("LMS Assignment", fields=["name", "title", "type", "course"]):
    print(f"  {a.name} | {a.title} | tipo={a.type} | curso={a.course}")

print("\n=== Quizzes existentes ===")
for q in frappe.get_all("LMS Quiz", fields=["name", "title"]):
    print(f"  {q.name} | {q.title}")
