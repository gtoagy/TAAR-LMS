"""Crea el Curso de Mascotas con su curriculum completo (módulos + lecciones).

Los 4 videos ya subidos a Vimeo quedan embebidos en sus lecciones; el resto
son lecciones vacías listas para llenar. Ejecutar con el python del bench:
  env/bin/python /workspace/create_mascotas.py
"""

import json

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

COURSE_TITLE = "Curso de Mascotas"
SHORT_INTRO = (
    "¡El tema favorito de los estudiantes! Aprende a crear obras "
    "maestras peludas con mi método de 4 pasos."
)
DESCRIPTION = (
    "<p>¡El tema favorito de los estudiantes! Aprende a crear obras maestras "
    "peludas con mi método de 4 pasos.</p>"
    "<p>Partimos desde las bases: materiales, boceto y proporciones, y avanzamos "
    "hasta dominar el pelaje, los rasgos y los detalles que le dan vida a tu "
    "retrato. Al final pintarás a tu propia mascota paso a paso y podrás "
    "compartir tu obra con la comunidad.</p>"
)
INSTRUCTOR = "instructor@taar.test"


def vimeo_block(video_id: str, block_id: str) -> dict:
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


def paragraph_block(text: str, block_id: str) -> dict:
    return {"id": block_id, "type": "paragraph", "data": {"text": text}}


PLACEHOLDER = "Contenido por agregar — sube el video a Vimeo y pega el enlace aquí."

# (título de módulo, [(título de lección, vimeo_id o None), ...])
CURRICULUM = [
    (
        "Bienvenida",
        [
            ("Introducción", "1210950170"),
            ("Overview: el método de 4 pasos", "1210950171"),
        ],
    ),
    (
        "Materiales y preparación",
        [
            ("Materiales que necesitarás", None),
            ("Boceto y proporciones", None),
        ],
    ),
    (
        "Todo sobre pelos",
        [
            ("Todo sobre pelos — Parte 1", "1210950173"),
            ("Todo sobre pelos — Parte 2", "1210950674"),
            ("Volumen del pelaje", None),
        ],
    ),
    (
        "Rasgos y detalles",
        [
            ("Ojos llenos de vida", None),
            ("Nariz y hocico", None),
            ("Orejas y bigotes", None),
        ],
    ),
    (
        "Proyecto final",
        [
            ("Pinta a tu mascota paso a paso", None),
            ("Reto final: comparte tu obra", None),
        ],
    ),
]

if frappe.db.exists("LMS Course", {"title": COURSE_TITLE}):
    print("YA_EXISTE: el curso ya está creado, no se hace nada.")
    raise SystemExit(0)

course = frappe.new_doc("LMS Course")
course.update(
    {
        "title": COURSE_TITLE,
        "short_introduction": SHORT_INTRO,
        "description": DESCRIPTION,
        "published": 1,
        "paid_course": 1,
        "course_price": 999,
        "currency": "MXN",
    }
)
course.append("instructors", {"instructor": INSTRUCTOR})
course.insert(ignore_permissions=True)

lesson_count = 0
chapter_names = []
for module_idx, (module_title, lessons) in enumerate(CURRICULUM, start=1):
    chapter = frappe.new_doc("Course Chapter")
    chapter.update({"course": course.name, "title": module_title})
    chapter.insert(ignore_permissions=True)
    chapter_names.append(chapter.name)

    for lesson_idx, (lesson_title, vimeo_id) in enumerate(lessons, start=1):
        block_id = f"taar{module_idx}x{lesson_idx}"
        if vimeo_id:
            blocks = [vimeo_block(vimeo_id, block_id)]
        else:
            blocks = [paragraph_block(PLACEHOLDER, block_id)]
        lesson = frappe.new_doc("Course Lesson")
        lesson.update(
            {
                "chapter": chapter.name,
                "course": course.name,
                "title": lesson_title,
                "content": json.dumps({"blocks": blocks}),
                "include_in_preview": 1 if module_idx == 1 and lesson_idx == 1 else 0,
            }
        )
        lesson.insert(ignore_permissions=True)
        chapter.append("lessons", {"lesson": lesson.name})
        lesson_count += 1

    chapter.save(ignore_permissions=True)

# Los hooks de las lecciones tocan el curso; recargar antes del guardado final
course.reload()
for name in chapter_names:
    course.append("chapters", {"chapter": name})
course.save(ignore_permissions=True)

# Inscribir ya a los miembros activos (sin esperar el job en background)
from taar_lms.membership import enroll_active_members_in_course

enroll_active_members_in_course(course.name)

frappe.db.commit()

enrolled = frappe.get_all("LMS Enrollment", filters={"course": course.name}, pluck="member")
print("CURSO_CREADO:", course.name)
print("MODULOS:", len(CURRICULUM), "| LECCIONES:", lesson_count)
print("INSCRITOS:", enrolled)
