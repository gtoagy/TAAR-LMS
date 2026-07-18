"""Reemplaza el curriculum del Curso de Mascotas con el curriculum real de Disco.

8 módulos / 28 lecciones (sin Proyecto #1 ni Proyecto #2). Ejecutar:
  env/bin/python /workspace/rebuild_mascotas.py
"""

import json

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

COURSE = "curso-de-mascotas"


def vimeo_block(video_id, block_id):
    return {
        "id": block_id,
        "type": "embed",
        "data": {
            "service": "vimeo",
            "source": f"https://vimeo.com/{video_id}",
            "embed": f"https://player.vimeo.com/video/{video_id}",
            "width": 580,
            "height": 320,
            "caption": "",
        },
    }


def paragraph_block(text, block_id):
    return {"id": block_id, "type": "paragraph", "data": {"text": text}}


PENDIENTE = "Contenido por agregar — sube el video a Vimeo y pega el enlace aquí."

# (módulo, [(lección, vimeo_id o None), ...]) — curriculum de Disco sin Proyecto #1/#2
CURRICULUM = [
    (
        "🐾 ¡Bienvenid@ al curso de Mascotas!",
        [
            ("Introducción al curso de Mascotas", "1210950170"),
            ("Lista de materiales", None),
            ("Descarga e imprime el Workbook", None),
            ("¡Completa tu perfil!", None),
        ],
    ),
    (
        "🧅 Método por capas",
        [
            ('Introducción a las "Capas"', "1210950171"),
        ],
    ),
    (
        "✍🏼 Todo acerca de los pelitos",
        [
            ("Errores más comunes al pintar pelitos y como corregirlos", "1210950173"),
            ("Ejercicio #1 | Trazos", "1210950674"),
        ],
    ),
    (
        "🎨 Colores vivos",
        [
            ("Introducción al color en las mascotas", None),
            ("Quizz | Colores en las mascotas", None),
            ("Ejercicio #2 | Creando colores con vida", None),
            ("Ejercicio #3 | Reto colores con vida", None),
        ],
    ),
    (
        "🤩 Tips de realismo",
        [
            ("Mis secretos para darle vida a tus obras peludas", None),
        ],
    ),
    (
        "🦁 Ejercicios de pelaje",
        [
            ("Introducción a la creación del pelaje", None),
            ("Ejercicio #4 | Pelaje corto", None),
            ("Ejercicio #5 | Pelaje negro", None),
            ("Ejercicio #6 | Pelaje blanco", None),
            ("Ejercicio #7 | Pelaje rizado", None),
        ],
    ),
    (
        "✏️ Bocetaje",
        [
            ("Técnica para bocetar", None),
        ],
    ),
    (
        "💪🏼 Proyecto Final",
        [
            ("Introducción al proyecto", None),
            ("Prepara tus materiales 🎨", None),
            ("¡Descarga la imagen de referencia!", None),
            ("¡Empecemos con los tonos base!", None),
            ("Tonos sombra", None),
            ("Ojos", None),
            ("Tonos luz", None),
            ("Nariz", None),
            ("Últimos detalles", None),
            ("¡Sube tu resultado final!", None),
        ],
    ),
]

course = frappe.get_doc("LMS Course", COURSE)

# 1) Vaciar el curriculum actual
course.set("chapters", [])
course.save(ignore_permissions=True)

old_chapters = frappe.get_all("Course Chapter", filters={"course": COURSE}, pluck="name")
old_lessons = frappe.get_all("Course Lesson", filters={"course": COURSE}, pluck="name")
frappe.db.delete("LMS Course Progress", {"course": COURSE})
for lesson in old_lessons:
    frappe.delete_doc("Course Lesson", lesson, ignore_permissions=True, force=True)
for chapter in old_chapters:
    frappe.delete_doc("Course Chapter", chapter, ignore_permissions=True, force=True)

# 2) Crear el curriculum de Disco
chapter_names = []
lesson_count = 0
for m_idx, (module_title, lessons) in enumerate(CURRICULUM, start=1):
    chapter = frappe.new_doc("Course Chapter")
    chapter.update({"course": COURSE, "title": module_title})
    chapter.insert(ignore_permissions=True)
    chapter_names.append(chapter.name)

    for l_idx, (lesson_title, vimeo_id) in enumerate(lessons, start=1):
        block_id = f"taar{m_idx}x{l_idx}"
        blocks = (
            [vimeo_block(vimeo_id, block_id)]
            if vimeo_id
            else [paragraph_block(PENDIENTE, block_id)]
        )
        lesson = frappe.new_doc("Course Lesson")
        lesson.update(
            {
                "chapter": chapter.name,
                "course": COURSE,
                "title": lesson_title,
                "content": json.dumps({"blocks": blocks}),
                "include_in_preview": 1 if (m_idx, l_idx) == (1, 1) else 0,
            }
        )
        # El "#" de los títulos rompe el autoname (format:{####} {title});
        # nombre interno explícito, el título visible queda intacto.
        lesson.insert(ignore_permissions=True, set_name=f"mascotas-{m_idx}-{l_idx}")
        chapter.append("lessons", {"lesson": lesson.name})
        lesson_count += 1

    chapter.save(ignore_permissions=True)

course.reload()
for name in chapter_names:
    course.append("chapters", {"chapter": name})
course.save(ignore_permissions=True)

frappe.db.commit()

print("OK:", len(chapter_names), "módulos |", lesson_count, "lecciones")
course.reload()
for row in course.chapters:
    title = frappe.db.get_value("Course Chapter", row.chapter, "title")
    n = frappe.db.count("Lesson Reference", {"parent": row.chapter})
    print(f"  {row.idx}. {title} ({n} lecciones)")
