"""Verifica que cada lección del Curso de Retratos tenga el video que le toca."""

import json
import os
import re

import frappe

frappe.init(site="lms.localhost")
frappe.connect()

base = os.path.dirname(os.path.abspath(__file__))
VIDEOS = json.load(open(os.path.join(base, "retratos_videos.json"), encoding="utf-8"))

import ast

src = open(os.path.join(base, "map_videos_retratos.py"), encoding="utf-8").read()
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "LECCION_A_NUM":
        LECCION_A_NUM = ast.literal_eval(node.value)

course = frappe.get_doc("LMS Course", "curso-de-retratos")
print("Curso:", course.title, "| publicado:", course.published, "| membresía:", course.taar_incluido_en_membresia)
print("Inscritos:", frappe.db.count("LMS Enrollment", {"course": course.name}))
print()

problemas = []
con_video = 0
sin_video = 0

for cap in course.chapters:
    chapter = frappe.get_doc("Course Chapter", cap.chapter)
    for ref in chapter.lessons:
        lname = ref.lesson
        titulo = frappe.db.get_value("Course Lesson", lname, "title")
        content = frappe.db.get_value("Course Lesson", lname, "content") or ""
        m = re.search(r"vimeo\.com/(\d+)", content)
        esperado_num = LECCION_A_NUM.get(lname)

        if esperado_num is None:
            if m:
                problemas.append(f"{lname} ({titulo}): tiene video pero no debería")
            else:
                sin_video += 1
            continue

        esperado_id = VIDEOS.get(esperado_num)
        if not m:
            problemas.append(f"{lname} ({titulo}): falta el video {esperado_num}")
        elif m.group(1) != esperado_id:
            problemas.append(f"{lname} ({titulo}): tiene {m.group(1)}, esperaba {esperado_id} (#{esperado_num})")
        else:
            con_video += 1

print("Lecciones con el video correcto:", con_video)
print("Lecciones sin video (correctamente):", sin_video)
if problemas:
    print("\nPROBLEMAS:")
    for p in problemas:
        print("  -", p)
else:
    print("\nSIN PROBLEMAS: las 56 lecciones están como deben.")

ids = [m for m in (re.search(r"vimeo\.com/(\d+)", frappe.db.get_value("Course Lesson", l, "content") or "") for l in LECCION_A_NUM) if m]
vals = [m.group(1) for m in ids]
dups = {v for v in vals if vals.count(v) > 1}
print("IDs de Vimeo repetidos entre lecciones:", dups or "ninguno")
