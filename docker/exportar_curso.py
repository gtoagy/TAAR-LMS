"""Exporta un curso completo a un ZIP, listo para importarlo en producción.

El LMS ya trae exportación e importación de cursos (course_import_export.py):
el ZIP lleva el curso, sus capítulos, lecciones, archivos, cuestionarios y
tareas. Así el contenido viaja a producción por la interfaz, sin patches ni
desplegar código.

La función que expone el LMS sirve el ZIP como descarga del navegador y lo
borra a los 10 minutos; aquí se usan sus piezas internas para dejarlo en disco.

  env/bin/python /workspace/exportar_curso.py <curso> [<curso> ...]
"""

import os
import sys

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

from lms.lms.course_import_export import (  # noqa: E402
    build_course_zip,
    get_chapters_for_export,
    get_course_assessments,
    get_course_assets,
    get_course_evaluator,
    get_course_instructors,
    get_lessons_for_export,
)

DESTINO = "/workspace/exportados"
os.makedirs(DESTINO, exist_ok=True)

cursos = sys.argv[1:] or frappe.get_all("LMS Course", pluck="name")

for nombre in cursos:
    if not frappe.db.exists("LMS Course", nombre):
        print(f"AVISO: no existe el curso {nombre}")
        continue

    curso = frappe.get_doc("LMS Course", nombre)
    capitulos = get_chapters_for_export(curso.chapters)
    lecciones = get_lessons_for_export(nombre)
    instructores = get_course_instructors(curso)
    evaluador = get_course_evaluator(curso)
    evaluaciones, preguntas, casos = get_course_assessments(lecciones)
    activos = get_course_assets(curso, lecciones, instructores, evaluador, evaluaciones, preguntas)

    ruta = os.path.join(DESTINO, f"{nombre}.zip")
    build_course_zip(
        ruta,
        curso,
        capitulos,
        lecciones,
        activos,
        evaluaciones,
        preguntas,
        casos,
        instructores,
        evaluador,
    )
    tam = os.path.getsize(ruta) // 1024
    print(
        f"{curso.title[:34]:<34} -> {os.path.basename(ruta):<32} "
        f"{len(capitulos):>2} módulos, {len(lecciones):>3} lecciones, "
        f"{len(activos):>2} archivos, {tam} KB"
    )
