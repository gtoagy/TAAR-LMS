import json
import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

MAPA = {
    "mascotas-5-1": "1210966469",  # 11. Tips de realismo
    "mascotas-6-5": "1210966571",  # 10.1 Ejercicio pelaje 4 (rizado)
}
for lesson_name, vimeo_id in MAPA.items():
    content = {"blocks": [{"id": lesson_name.replace("mascotas-", "vid"), "type": "embed", "data": {
        "service": "vimeo", "source": f"https://vimeo.com/{vimeo_id}",
        "embed": f"https://player.vimeo.com/video/{vimeo_id}", "width": 580, "height": 320, "caption": ""}}]}
    frappe.db.set_value("Course Lesson", lesson_name, "content", json.dumps(content), update_modified=True)
    print("OK", lesson_name, "->", vimeo_id, "|", frappe.db.get_value("Course Lesson", lesson_name, "title"))
frappe.db.commit()
