"""Coloca los videos de Vimeo ya subidos en sus lecciones del Curso de Mascotas.

Ejecutar: env/bin/python /workspace/map_videos_mascotas.py
"""

import json

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

# lección (name interno) -> vimeo_id
MAPA = {
    "mascotas-4-1": "1210955092",  # 5. Colores vivos
    "mascotas-4-3": "1210955455",  # 6. Colores vivos 2
    "mascotas-6-1": "1210955541",  # 7. Introducción Ejercicios de Pelajes
    "mascotas-6-2": "1210955664",  # 8. Ejercicio pelaje 1
    "mascotas-6-3": "1210955711",  # 9. Ejercicio pelaje 2
    "mascotas-6-4": "1210955751",  # 10. Ejercicio pelaje 3
    "mascotas-7-1": "1210956552",  # 12. Bocetaje
    "mascotas-8-1": "1210956625",  # 13. PF introduccion
    "mascotas-8-4": "1210956641",  # 14. PF Tono base
    "mascotas-8-5": "1210956727",  # 15. PF Tonos sombra
    "mascotas-8-6": "1210956731",  # 16. PF Ojos
    "mascotas-8-7": "1210957190",  # 17. PF tonos luz
    "mascotas-8-8": "1210957360",  # 18. PF Nariz
    "mascotas-8-9": "1210957778",  # 19. PF Ultimos detalles
    "mascotas-8-10": "1210957869",  # 20. Outro
}

for lesson_name, vimeo_id in MAPA.items():
    content = {
        "blocks": [
            {
                "id": lesson_name.replace("mascotas-", "vid"),
                "type": "embed",
                "data": {
                    "service": "vimeo",
                    "source": f"https://vimeo.com/{vimeo_id}",
                    "embed": f"https://player.vimeo.com/video/{vimeo_id}",
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
    print("OK", lesson_name, "->", vimeo_id, "|", title)

frappe.db.commit()
print("TOTAL:", len(MAPA), "lecciones actualizadas")
