"""Rellena con sus videos de Vimeo las lecciones del Curso de Retratos que sigan pendientes.

Úsalo cuando el curso ya existe y llegan (o se corrigen) IDs de Vimeo: lee
retratos_videos.json y reescribe el contenido de las lecciones que corresponda,
sin tocar módulos ni el resto del curriculum.

Ejecutar: env/bin/python /workspace/map_videos_retratos.py
"""

import json
import os

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

VIDEOS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "retratos_videos.json")

# lección (name interno) -> número de video, según el curriculum de create_retratos.py
LECCION_A_NUM = {
    "retratos-1-1": "01",
    "retratos-1-2": "02",
    "retratos-2-1": "03",
    "retratos-2-2": "04",
    "retratos-2-3": "05",
    "retratos-3-2": "06",
    "retratos-3-3": "07",
    "retratos-3-4": "08",
    "retratos-3-5": "09",
    "retratos-4-1": "10",
    "retratos-4-2": "11",
    "retratos-4-3": "12",
    "retratos-4-4": "13",
    "retratos-4-5": "14",
    "retratos-5-1": "15",
    "retratos-6-1": "16",
    "retratos-7-1": "17",
    "retratos-7-2": "18",
    "retratos-9-2": "19",
    "retratos-9-3": "20",
    "retratos-9-4": "21",
    "retratos-9-5": "22",
    "retratos-9-6": "23",
    "retratos-9-7": "24",
    "retratos-9-8": "25",
    "retratos-10-1": "26",
    "retratos-10-2": "27",
    "retratos-10-3": "28",
    "retratos-10-4": "29",
    "retratos-11-1": "30",
    "retratos-11-3": "31",
    "retratos-11-4": "32",
    "retratos-11-5": "33",
    "retratos-11-6": "34",
    "retratos-11-7": "35",
    "retratos-11-8": "36",
    "retratos-11-9": "37",
    "retratos-11-10": "38",
    "retratos-11-11": "39",
    "retratos-11-12": "40",
    "retratos-11-13": "41",
    "retratos-11-14": "42",
    "retratos-11-15": "43",
    "retratos-11-16": "44",
    "retratos-11-17": "45",
    "retratos-11-18": "46",
    "retratos-11-19": "47",
    "retratos-11-20": "48",
}

with open(VIDEOS_JSON, encoding="utf-8") as fh:
    VIDEOS = json.load(fh)

actualizadas = 0
ya_estaban = 0
sin_id = []
no_existen = []

for lesson_name, num in LECCION_A_NUM.items():
    if not frappe.db.exists("Course Lesson", lesson_name):
        no_existen.append(lesson_name)
        continue

    video_id = VIDEOS.get(num)
    if not video_id:
        sin_id.append(num)
        continue

    actual = frappe.db.get_value("Course Lesson", lesson_name, "content") or ""
    if f"vimeo.com/{video_id}" in actual:
        ya_estaban += 1
        continue

    content = {
        "blocks": [
            {
                "id": lesson_name.replace("retratos-", "vid"),
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
        ]
    }
    frappe.db.set_value(
        "Course Lesson", lesson_name, "content", json.dumps(content), update_modified=True
    )
    title = frappe.db.get_value("Course Lesson", lesson_name, "title")
    print(f"OK {lesson_name} -> {video_id} | {title}")
    actualizadas += 1

frappe.db.commit()

print("---")
print("Actualizadas:", actualizadas, "| Ya tenían el video:", ya_estaban)
if sin_id:
    print("Sin ID en retratos_videos.json:", ", ".join(sin_id))
if no_existen:
    print("Lecciones que no existen (¿corriste create_retratos.py?):", ", ".join(no_existen))
