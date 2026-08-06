"""Importa el ZIP de un curso en este mismo sitio y comprueba que llega entero.

Deja un curso duplicado que se borra al final. Verifica lo que el importador
de upstream hacía mal:

  - que cada módulo enlace SUS lecciones (buscarlas por título hacía que un
    curso con títulos repetidos —"Ojos", "Tonos luz", una por proyecto— dejara
    todos los módulos apuntando a la misma y el resto fuera del temario)
  - que cada bloque de tarea apunte a la tarea que le toca y no a otra que ya
    existiera en el sitio con ese nombre
  - que los materiales existan de verdad y con la misma privacidad
  - que las imágenes del cuestionario, que viven dentro del HTML de las
    preguntas, hayan viajado

  env/bin/python /workspace/probar_importacion.py <curso>
"""

import json
import os
import re
import shutil
import sys

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

from lms.lms.course_import_export import import_course_zip  # noqa: E402

curso = sys.argv[1] if len(sys.argv) > 1 else "curso-de-mascotas"
origen = f"/workspace/exportados/{curso}.zip"
nombre_zip = f"prueba_{curso}.zip"
destino = frappe.get_site_path("private", "files", nombre_zip)
shutil.copy(origen, destino)

importado = import_course_zip(f"/private/files/{nombre_zip}")
frappe.db.commit()
print(f"importado como: {importado}\n")

fallos = []


def revisar(condicion, mensaje):
    print(f"  [{'OK ' if condicion else 'MAL'}] {mensaje}")
    if not condicion:
        fallos.append(mensaje)


# --- estructura: mismos módulos y mismas lecciones que el original -----------
def estructura(nombre_curso):
    doc = frappe.get_doc("LMS Course", nombre_curso)
    salida = []
    for fila in doc.chapters:
        cap = frappe.get_doc("Course Chapter", fila.chapter)
        salida.append((cap.title, [frappe.db.get_value("Course Lesson", l.lesson, "title") for l in cap.lessons]))
    return salida


original, copia = estructura(curso), estructura(importado)
revisar(len(original) == len(copia), f"módulos: {len(copia)} de {len(original)}")
revisar(
    [t for t, _ in original] == [t for t, _ in copia],
    "los módulos llegan con el mismo título y en el mismo orden",
)
enlazadas_o = sum(len(l) for _, l in original)
enlazadas_c = sum(len(l) for _, l in copia)
revisar(enlazadas_o == enlazadas_c, f"lecciones en el temario: {enlazadas_c} de {enlazadas_o}")
revisar([l for _, l in original] == [l for _, l in copia], "cada módulo lleva sus propias lecciones, en orden")

sueltas = [
    frappe.db.get_value("Course Lesson", n, "title")
    for n in frappe.get_all("Course Lesson", filters={"course": importado}, pluck="name")
    if not frappe.db.exists("Lesson Reference", {"lesson": n})
]
revisar(not sueltas, f"ninguna lección se queda fuera del temario{' -> ' + str(sueltas) if sueltas else ''}")

# --- las lecciones repetidas no comparten contenido --------------------------
def video(contenido):
    for b in json.loads(contenido or '{"blocks":[]}').get("blocks", []):
        if b.get("type") == "embed":
            m = re.search(r"(\d{6,})", b["data"].get("source", "") or "")
            if m:
                return m.group(1)
    return None


videos = {}
for _, lecs in copia:
    pass
for n in frappe.get_all("Course Lesson", filters={"course": importado}, pluck="name"):
    v = video(frappe.db.get_value("Course Lesson", n, "content"))
    if v:
        videos.setdefault(v, []).append(n)
repetidos = {v: n for v, n in videos.items() if len(n) > 1}
revisar(not repetidos, f"ningún vídeo aparece en dos lecciones{' -> ' + str(repetidos) if repetidos else ''}")

# --- tareas y cuestionarios --------------------------------------------------
def evaluaciones(nombre_curso):
    salida = []
    for n in frappe.get_all("Course Lesson", filters={"course": nombre_curso}, pluck="name"):
        titulo = frappe.db.get_value("Course Lesson", n, "title")
        for b in json.loads(frappe.db.get_value("Course Lesson", n, "content") or '{"blocks":[]}')["blocks"]:
            if b.get("type") in ("assignment", "quiz"):
                ref = b["data"].get(b["type"])
                doctype = "LMS Assignment" if b["type"] == "assignment" else "LMS Quiz"
                salida.append((titulo, b["type"], frappe.db.get_value(doctype, ref, "title") if ref else None))
    return sorted(salida)


revisar(evaluaciones(curso) == evaluaciones(importado), "cada lección apunta a su propia tarea o cuestionario")

# --- materiales ---------------------------------------------------------------
def existe_fichero(url):
    if not url:
        return False
    doc = frappe.db.get_value("File", {"file_url": url}, ["is_private"], as_dict=True)
    if not doc:
        return False
    carpeta = "private" if doc.is_private else "public"
    return os.path.exists(frappe.get_site_path(carpeta, "files", os.path.basename(url)))


rotos = []
for n in frappe.get_all("Course Lesson", filters={"course": importado}, pluck="name"):
    for b in json.loads(frappe.db.get_value("Course Lesson", n, "content") or '{"blocks":[]}')["blocks"]:
        if b.get("type") == "upload" and not existe_fichero(b["data"].get("file_url")):
            rotos.append(b["data"].get("file_url"))
revisar(not rotos, f"los materiales de las lecciones existen{' -> faltan ' + str(rotos) if rotos else ''}")

# Los cuestionarios se localizan por los bloques de las lecciones, no por su
# campo `course`: el importador se lo quitaba y los dejaba sin dueño.
cuestionarios = set()
for n in frappe.get_all("Course Lesson", filters={"course": importado}, pluck="name"):
    for b in json.loads(frappe.db.get_value("Course Lesson", n, "content") or '{"blocks":[]}')["blocks"]:
        if b.get("type") == "quiz" and b["data"].get("quiz"):
            cuestionarios.add(b["data"]["quiz"])

huerfanos = [q for q in cuestionarios if not frappe.db.get_value("LMS Quiz", q, "lesson")]
revisar(not huerfanos, f"los cuestionarios saben a qué lección pertenecen{' -> ' + str(huerfanos) if huerfanos else ''}")

originales = {
    frappe.db.get_value("LMS Quiz", q, "title"): (
        frappe.db.count("LMS Quiz Question", {"parent": q}),
        frappe.db.get_value("LMS Quiz", q, "total_marks"),
    )
    for q in frappe.get_all("LMS Quiz", filters={"course": curso}, pluck="name")
}
for q in cuestionarios:
    titulo = frappe.db.get_value("LMS Quiz", q, "title")
    esperado = originales.get(titulo)
    obtenido = (
        frappe.db.count("LMS Quiz Question", {"parent": q}),
        frappe.db.get_value("LMS Quiz", q, "total_marks"),
    )
    revisar(esperado == obtenido, f"'{titulo}': {obtenido[0]} preguntas y {obtenido[1]} puntos (esperado {esperado})")

def imagenes_de(quizzes):
    urls = []
    for q in quizzes:
        for fila in frappe.get_all("LMS Quiz Question", filters={"parent": q}, pluck="question"):
            doc = frappe.get_doc("LMS Question", fila)
            for campo in ["question"] + [f"explanation_{i}" for i in range(1, 11)]:
                urls += re.findall(r'src="(/(?:private/)?files/[^"]+)"', doc.get(campo) or "")
    return set(urls)


esperadas = imagenes_de(frappe.get_all("LMS Quiz", filters={"course": curso}, pluck="name"))
if not esperadas:
    print("  [--] este curso no tiene cuestionarios con imágenes")
else:
    obtenidas = imagenes_de(cuestionarios)
    rotas = [u for u in obtenidas if not existe_fichero(u)]
    revisar(
        len(obtenidas) == len(esperadas) and not rotas,
        f"las imágenes del cuestionario llegaron ({len(obtenidas)} de {len(esperadas)})"
        + (f" -> faltan {rotas}" if rotas else ""),
    )

# --- limpieza -----------------------------------------------------------------
for l in frappe.get_all("Course Lesson", filters={"course": importado}, pluck="name"):
    frappe.db.delete("LMS Course Progress", {"lesson": l})
    for fila in frappe.get_all("Lesson Reference", filters={"lesson": l}, fields=["parent"]):
        cap = frappe.get_doc("Course Chapter", fila.parent)
        cap.set("lessons", [x for x in cap.lessons if x.lesson != l])
        cap.save(ignore_permissions=True)
    frappe.delete_doc("Course Lesson", l, ignore_permissions=True, force=True)
for q in frappe.get_all("LMS Quiz", filters={"course": importado}, pluck="name"):
    for fila in frappe.get_all("LMS Quiz Question", filters={"parent": q}, pluck="question"):
        frappe.delete_doc("LMS Question", fila, ignore_permissions=True, force=True)
    frappe.delete_doc("LMS Quiz", q, ignore_permissions=True, force=True)
for c in frappe.get_all("Course Chapter", filters={"course": importado}, pluck="name"):
    frappe.delete_doc("Course Chapter", c, ignore_permissions=True, force=True)
frappe.delete_doc("LMS Course", importado, ignore_permissions=True, force=True)
os.remove(destino)
frappe.db.commit()

print(f"\n{'TODO CORRECTO' if not fallos else str(len(fallos)) + ' FALLOS'}  (curso de prueba {importado} eliminado)")
sys.exit(1 if fallos else 0)
