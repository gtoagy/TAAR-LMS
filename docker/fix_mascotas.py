"""Repara el Curso de Mascotas: vincula los módulos al curso e inscribe miembros."""

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

course_name = frappe.db.get_value("LMS Course", {"title": "Curso de Mascotas"})
if not course_name:
    raise SystemExit("NO_EXISTE el curso")

course = frappe.get_doc("LMS Course", course_name)

chapters = frappe.get_all(
    "Course Chapter",
    filters={"course": course_name},
    fields=["name", "title", "creation"],
    order_by="creation asc",
)
existing = {row.chapter for row in course.chapters}
for ch in chapters:
    if ch.name not in existing:
        course.append("chapters", {"chapter": ch.name})
course.save(ignore_permissions=True)

from taar_lms.membership import enroll_active_members_in_course

enroll_active_members_in_course(course_name)
frappe.db.commit()

course.reload()
print("CURSO:", course_name, "| published:", course.published)
for row in course.chapters:
    ch_title = frappe.db.get_value("Course Chapter", row.chapter, "title")
    lessons = frappe.get_all(
        "Lesson Reference", filters={"parent": row.chapter}, fields=["lesson"], order_by="idx"
    )
    titles = [frappe.db.get_value("Course Lesson", l.lesson, "title") for l in lessons]
    print(f"  Módulo: {ch_title} -> {titles}")
enrolled = frappe.get_all("LMS Enrollment", filters={"course": course_name}, pluck="member")
print("INSCRITOS:", enrolled)
