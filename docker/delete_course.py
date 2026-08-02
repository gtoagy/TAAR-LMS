"""Borra un curso del LMS con todas sus dependencias, en el orden que funciona.

El botón Eliminar del SPA falla en silencio por LinkExistsError: hay que soltar
primero progreso/inscripciones, luego los quizzes, y romper el ciclo
capítulo↔lección vaciando las tablas hijas antes de borrar los documentos.

Uso:  ../env/bin/python /workspace/delete_course.py <slug-del-curso>
"""

import sys

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

if len(sys.argv) < 2:
    print("Falta el slug del curso. Ej: delete_course.py a-guide-to-frappe-learning")
    raise SystemExit(1)

COURSE = sys.argv[1]

if not frappe.db.exists("LMS Course", COURSE):
    print(f"NO_EXISTE: {COURSE} — no hay nada que borrar.")
    raise SystemExit(0)

titulo = frappe.db.get_value("LMS Course", COURSE, "title")
print(f"Borrando: {titulo} ({COURSE})")

chapters = frappe.get_all("Course Chapter", filters={"course": COURSE}, pluck="name")
lessons = frappe.get_all("Course Lesson", filters={"course": COURSE}, pluck="name")
print(f"  {len(chapters)} capítulos | {len(lessons)} lecciones")

# 1) Datos de alumnos que apuntan al curso
for dt in (
    "LMS Course Progress",
    "LMS Enrollment",
    "LMS Course Review",
    "LMS Certificate",
):
    if frappe.db.exists("DocType", dt):
        n = frappe.db.count(dt, {"course": COURSE})
        if n:
            frappe.db.delete(dt, {"course": COURSE})
            print(f"  - {dt}: {n} borrados")

# 2) Datos que apuntan a las lecciones
for dt, campo in (("LMS Lesson Note", "lesson"), ("LMS Video Watch Duration", "lesson")):
    if frappe.db.exists("DocType", dt) and lessons:
        n = frappe.db.count(dt, {campo: ("in", lessons)})
        if n:
            frappe.db.delete(dt, {campo: ("in", lessons)})
            print(f"  - {dt}: {n} borrados")

# 3) Quizzes referenciados por las lecciones
quizzes = set()
for lesson in lessons:
    for fld in ("quiz_id",):
        val = frappe.db.get_value("Course Lesson", lesson, fld) if frappe.db.has_column("Course Lesson", fld) else None
        if val:
            quizzes.add(val)
for quiz in quizzes:
    if frappe.db.exists("DocType", "LMS Quiz Submission"):
        frappe.db.delete("LMS Quiz Submission", {"quiz": quiz})
    frappe.delete_doc("LMS Quiz", quiz, ignore_permissions=True, force=True)
    print(f"  - quiz borrado: {quiz}")

# 4) Romper el ciclo capítulo -> lección vaciando la tabla hija
for chapter in chapters:
    doc = frappe.get_doc("Course Chapter", chapter)
    doc.set("lessons", [])
    doc.save(ignore_permissions=True)

# 5) Lecciones
for lesson in lessons:
    frappe.delete_doc("Course Lesson", lesson, ignore_permissions=True, force=True)
print(f"  - {len(lessons)} lecciones borradas")

# 6) Vaciar chapters del curso, borrar capítulos y el curso
course = frappe.get_doc("LMS Course", COURSE)
course.set("chapters", [])
course.save(ignore_permissions=True)
for chapter in chapters:
    frappe.delete_doc("Course Chapter", chapter, ignore_permissions=True, force=True)
print(f"  - {len(chapters)} capítulos borrados")

frappe.delete_doc("LMS Course", COURSE, ignore_permissions=True, force=True)
frappe.db.commit()

print(f"BORRADO: {titulo}")
print("Cursos restantes:", frappe.db.count("LMS Course"))
