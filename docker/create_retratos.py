"""Crea el Curso de Retratos con el curriculum real de Disco.

11 módulos / 56 lecciones (48 con video de Vimeo, 8 sin video: descargas de
referencia, exámenes y ejercicios de entrega).

Los IDs de Vimeo se leen de retratos_videos.json (número de video -> id), que
genera el script de subida. Las lecciones cuyo video aún no esté en ese archivo
quedan con el texto de pendiente y se pueden rellenar después con
map_videos_retratos.py sin tocar nada más.

Ejecutar con el python del bench:
  env/bin/python /workspace/create_retratos.py
"""

import json
import os

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

COURSE_TITLE = "Curso de Retratos"
SHORT_INTRO = (
    "Aprende a dibujar y pintar retratos desde cero: proporciones, "
    "cada elemento del rostro y dos proyectos completos."
)
DESCRIPTION = (
    "<p>Aprende a dibujar y pintar retratos desde cero. Empezamos por las "
    "proporciones del rostro de frente, en 3/4 y de perfil, y luego dominamos "
    "cada elemento por separado: ojos, bocas, nariz, orejas y cabello.</p>"
    "<p>Con esas bases pintarás dos proyectos completos paso a paso: un retrato "
    "a lápiz y un retrato en pintura, incluyendo las técnicas clave de tonos "
    "piel, degradados y trazos finos.</p>"
)
INSTRUCTOR = "instructor@taar.test"
# Mismo patrón que los 8 cursos migrados: publicado, sin precio propio y el
# acceso lo da la membresía (taar_incluido_en_membresia).
INCLUIDO_EN_MEMBRESIA = 1

PENDIENTE = "Contenido por agregar — sube el video a Vimeo y pega el enlace aquí."

VIDEOS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "retratos_videos.json")


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


# (título del módulo, [(título de la lección, número de video o None), ...])
# El número es el prefijo del título en Vimeo ("07" -> "07. Retratos - ...").
CURRICULUM = [
    (
        "👩🏻‍🎨 Introducción al curso",
        [
            ("Bienvenido al mundo de los retratos", "01"),
            ("Lista de materiales", "02"),
            ("¡Completa tu perfil!", None),
        ],
    ),
    (
        "👱🏼‍♀️ Bocetaje de proporciones y orientación",
        [
            ("Rostro de frente", "03"),
            ("Rostro en 3/4 usando el método de Loomis", "04"),
            ("Rostro de perfil", "05"),
        ],
    ),
    (
        "👀 Ojos",
        [
            ("Descarga las imágenes de referencia", None),
            ("El ojo a profundidad", "06"),
            ("Diferentes tipos de ojos", "07"),
            ("Ojos en 3/4 y perfil", "08"),
            ("Pestañas y cejas", "09"),
        ],
    ),
    (
        "👄 Bocas",
        [
            ("La boca a detalle", "10"),
            ("Sonrisa y dientes", "11"),
            ("Boca en 3/4", "12"),
            ("Mueca", "13"),
            ("Boca de perfil", "14"),
        ],
    ),
    (
        "👃🏼 Nariz",
        [
            ("La nariz simplificada", "15"),
        ],
    ),
    (
        "👂🏾 Orejas",
        [
            ("Las orejas a detalle", "16"),
        ],
    ),
    (
        "👩🏻‍🦱 Cabello",
        [
            ("Cabello lacio, ondulado y rizado", "17"),
            ("¡Juntemos los mechones!", "18"),
        ],
    ),
    (
        "💪🏼 Desafío TanArtistic",
        [
            ("Elementos del rostro", None),
            ("Proporciones del rostro", None),
        ],
    ),
    (
        "✏ Proyecto #1 (retrato a lápiz)",
        [
            ("¡Descarga la imagen de referencia!", None),
            ("Empecemos bocetando la estructura básica", "19"),
            ("Damos forma a los elementos", "20"),
            ("Sombras y mirada", "21"),
            ("Dale volumen a la nariz", "22"),
            ("Textura y forma a la boca", "23"),
            ("Movimiento en el cabello", "24"),
            ("Toques finales", "25"),
            ("¡Sube tu retrato!", None),
        ],
    ),
    (
        "🎨 Técnicas clave en pintura",
        [
            ("Tonos piel y sus variaciones", "26"),
            ("Ejercicio de tonos piel", "27"),
            ("Degradados y volumen", "28"),
            ("Técnica para trazos finos", "29"),
        ],
    ),
    (
        "👩🏽 Proyecto #2 (retrato en pintura)",
        [
            ("Introducción al proyecto final", "30"),
            ("¡Descarga la imagen de referencia!", None),
            ("¡Prepara tu lienzo!", "31"),
            ("Boceto usando el método de Loomis", "32"),
            ("Ubiquemos los elementos del retrato", "33"),
            ("Color de fondo", "34"),
            ("Creación del tono base", "35"),
            ("Primera capa de la cara parte 1", "36"),
            ("Primera capa de la cara parte 2", "37"),
            ("Primera capa del cuerpo", "38"),
            ("Primera capa del cabello", "39"),
            ("Tonos sombra de la cara", "40"),
            ("Tonos sombra del cuerpo", "41"),
            ("Tonos luz generales", "42"),
            ("Ojos", "43"),
            ("Pestañas y cejas", "44"),
            ("Labios", "45"),
            ("Cabello", "46"),
            ("Toques finales", "47"),
            ("¡Felicidades artista!", "48"),
            ("¡Lo lograste! Comparte tu resultado final", None),
        ],
    ),
]

if os.path.exists(VIDEOS_JSON):
    with open(VIDEOS_JSON, encoding="utf-8") as fh:
        VIDEOS = json.load(fh)
else:
    VIDEOS = {}
    print("AVISO: no encontré retratos_videos.json, todas las lecciones quedarán pendientes.")

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
        "paid_course": 0,
        "taar_incluido_en_membresia": INCLUIDO_EN_MEMBRESIA,
    }
)
course.append("instructors", {"instructor": INSTRUCTOR})
course.insert(ignore_permissions=True)

chapter_names = []
con_video = 0
sin_video = 0

for m_idx, (module_title, lessons) in enumerate(CURRICULUM, start=1):
    chapter = frappe.new_doc("Course Chapter")
    chapter.update({"course": course.name, "title": module_title})
    # "Proyecto #1" rompe el autoname (format:{####} {title}); nombre explícito.
    chapter.insert(ignore_permissions=True, set_name=f"retratos-m{m_idx}")
    chapter_names.append(chapter.name)

    for l_idx, (lesson_title, num) in enumerate(lessons, start=1):
        block_id = f"taar{m_idx}x{l_idx}"
        video_id = VIDEOS.get(num) if num else None
        if video_id:
            blocks = [vimeo_block(video_id, block_id)]
            con_video += 1
        else:
            blocks = [paragraph_block(PENDIENTE, block_id)]
            sin_video += 1

        lesson = frappe.new_doc("Course Lesson")
        lesson.update(
            {
                "chapter": chapter.name,
                "course": course.name,
                "title": lesson_title,
                "content": json.dumps({"blocks": blocks}),
                "include_in_preview": 1 if (m_idx, l_idx) == (1, 1) else 0,
            }
        )
        lesson.insert(ignore_permissions=True, set_name=f"retratos-{m_idx}-{l_idx}")
        chapter.append("lessons", {"lesson": lesson.name})

    chapter.save(ignore_permissions=True)

# Los hooks de las lecciones tocan el curso; recargar antes del guardado final
course.reload()
for name in chapter_names:
    course.append("chapters", {"chapter": name})
course.save(ignore_permissions=True)

# El hook on_update encola sync_course_access; lo corremos aquí en directo para
# no depender del worker en background y poder reportar los inscritos.
from taar_lms.membership import sync_course_access

sync_course_access(course.name)

frappe.db.commit()

enrolled = frappe.get_all("LMS Enrollment", filters={"course": course.name}, pluck="member")
print("CURSO_CREADO:", course.name)
print("MODULOS:", len(chapter_names), "| LECCIONES:", con_video + sin_video)
print("CON VIDEO:", con_video, "| SIN VIDEO:", sin_video)
print("INSCRITOS:", len(enrolled))

course.reload()
for row in course.chapters:
    title = frappe.db.get_value("Course Chapter", row.chapter, "title")
    n = frappe.db.count("Lesson Reference", {"parent": row.chapter})
    print(f"  {row.idx}. {title} ({n} lecciones)")
