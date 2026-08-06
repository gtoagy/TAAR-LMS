"""Vuelca la estructura real de los cursos: capitulo -> lecciones en orden.

Cada leccion se identifica por su video de Vimeo (unico) o, si no tiene, por una
huella del contenido. Sirve para cotejar produccion, donde las lecciones con el
mismo titulo se pisaron al importar.
"""

import hashlib
import io
import json
import re

import frappe

frappe.init(site="lms.localhost")
frappe.connect()


def huella(contenido: str) -> str:
    if not contenido:
        return "vacio"
    bloques = json.loads(contenido).get("blocks", [])
    for b in bloques:
        if b.get("type") == "embed":
            m = re.search(r"(\d{6,})", b["data"].get("source", "") or "")
            if m:
                return f"vimeo:{m.group(1)}"
    texto = json.dumps(bloques, ensure_ascii=False, sort_keys=True)
    return "hash:" + hashlib.sha1(texto.encode()).hexdigest()[:12]


salida = {}
for curso in sorted(frappe.get_all("LMS Course", pluck="name")):
    doc = frappe.get_doc("LMS Course", curso)
    capitulos = []
    for fila in doc.chapters:
        cap = frappe.get_doc("Course Chapter", fila.chapter)
        lecs = []
        for f in cap.lessons:
            l = frappe.db.get_value("Course Lesson", f.lesson, ["title", "content"], as_dict=True)
            if l:
                lecs.append({"titulo": l.title, "huella": huella(l.content)})
        capitulos.append({"titulo": cap.title, "lecciones": lecs})
    salida[curso] = capitulos

io.open("/workspace/exportados/estructura_local.json", "w", encoding="utf-8").write(
    json.dumps(salida, ensure_ascii=False, separators=(",", ":"))
)
total = sum(len(c["lecciones"]) for caps in salida.values() for c in caps)
print(f"{len(salida)} cursos, {sum(len(c) for c in salida.values())} capitulos, {total} lecciones")
duplicados = 0
for curso, caps in salida.items():
    vistos = {}
    for c in caps:
        for l in c["lecciones"]:
            vistos.setdefault(l["titulo"], set()).add(l["huella"])
    repes = {t: h for t, h in vistos.items() if len(h) > 1}
    if repes:
        duplicados += len(repes)
        print(f"  {curso}: {len(repes)} titulos repetidos con contenido distinto -> {list(repes)[:6]}")
print(f"total de titulos ambiguos: {duplicados}")
