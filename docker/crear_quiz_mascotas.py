"""Convierte el quizz de colores de Mascotas en un cuestionario nativo del LMS.

En Disco esta lección no tenía cuestionario: era un enlace a un formulario de
Tally más una tarea de "sube la foto de tu examen resuelto". El formulario ya no
hace falta — el LMS corrige solo y guarda el intento.

Las preguntas, sus opciones, cuál es la correcta y los textos de
retroalimentación se sacaron del propio formulario de Tally (extraer_tally.py
deja el volcado en tally_quiz_mascotas.json). Las imágenes se bajaron a
materiales/quiz_mascotas/.

El enunciado de una LMS Question es un Text Editor y el visor lo pinta con
v-html, así que la foto de cada pregunta va incrustada ahí. La explicación se
pintaba como texto plano y perdía la rueda cromática que acompañaba a cuatro de
ellas en Tally; Quiz.vue ahora la pinta igual que el enunciado, así que también
lleva su imagen.

Es idempotente: si el cuestionario ya existe, lo rehace en el sitio.

  env/bin/python /workspace/crear_quiz_mascotas.py
"""

import base64
import io
import json
import os

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

LECCION = "curso-de-mascotas-4-2"
QUIZ = "quizz-colores-en-las-mascotas"
TITULO = "Quizz | Colores en las mascotas"
MATERIALES = "/workspace/materiales/quiz_mascotas"
PUNTOS = 2  # Tally puntuaba sobre 18: nueve preguntas de dos puntos.

# Las páginas de Tally con la explicación que sigue a cada pregunta. El texto
# que arranca con "¡Sii" es el de acierto; el otro, el del fallo.
EXPLICACIONES = {1: None, 2: None, 3: 4, 5: 6, 7: None, 8: None, 9: 10, 11: None, 12: 13}

ANCHO = 1000


def optimizar(ruta: str) -> bytes:
    """Los PNG de Tally pesan hasta 190 KB; para un quiz sobra con menos."""
    from PIL import Image

    img = Image.open(ruta)
    if img.mode != "RGB":
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        fondo.paste(img, mask=img.convert("RGBA").split()[-1] if img.mode in ("RGBA", "P", "LA") else None)
        img = fondo
    if img.width > ANCHO:
        img = img.resize((ANCHO, round(img.height * ANCHO / img.width)), Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=82, optimize=True)
    return buffer.getvalue()


def subir(origen: str, nombre: str) -> str:
    """Sube la imagen como fichero público y devuelve su dirección."""
    existente = frappe.db.get_value("File", {"file_name": nombre, "is_private": 0}, "file_url")
    if existente:
        return existente
    doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": nombre,
            "content": base64.b64encode(optimizar(origen)).decode(),
            "decode": True,
            "is_private": 0,
        }
    ).insert(ignore_permissions=True)
    return doc.file_url


def borrar_anterior():
    """Deja el sitio limpio para poder volver a lanzar el script."""
    if not frappe.db.exists("LMS Quiz", QUIZ):
        return
    preguntas = frappe.get_all("LMS Quiz Question", filters={"parent": QUIZ}, pluck="question")
    for envio in frappe.get_all("LMS Quiz Submission", filters={"quiz": QUIZ}, pluck="name"):
        frappe.delete_doc("LMS Quiz Submission", envio, ignore_permissions=True, force=True)
    frappe.delete_doc("LMS Quiz", QUIZ, ignore_permissions=True, force=True)
    for pregunta in preguntas:
        if frappe.db.exists("LMS Question", pregunta):
            frappe.delete_doc("LMS Question", pregunta, ignore_permissions=True, force=True)
    print(f"  cuestionario anterior borrado ({len(preguntas)} preguntas)")


paginas = json.load(io.open("/workspace/tally_quiz_mascotas.json", encoding="utf-8"))
por_pagina = {p["pagina"]: p for p in paginas}

borrar_anterior()

filas = []
for orden, (pag, pag_explicacion) in enumerate(EXPLICACIONES.items(), start=1):
    datos = por_pagina[pag]
    enunciado = datos["textos"][0] if datos["textos"] else "¿Qué parte del gatito tiene mayor saturación?"

    url = subir(
        os.path.join(MATERIALES, datos["imagenes"][0].split("/")[-1]),
        f"quiz-colores-mascotas-{orden}.jpg",
    )
    html = f'<p>{enunciado}</p><p><img src="{url}" style="max-width:100%"></p>'

    acierto = fallo = None
    if pag_explicacion is not None:
        explica = por_pagina[pag_explicacion]
        # En Tally la misma rueda cromática acompañaba al acierto y al fallo.
        diagrama = ""
        if explica["imagenes"]:
            diagrama = '<img src="{}">'.format(
                subir(
                    os.path.join(MATERIALES, explica["imagenes"][0].split("/")[-1]),
                    f"quiz-colores-mascotas-{orden}-explicacion.jpg",
                )
            )
        for texto in explica["textos"]:
            limpio = texto.replace("&nbsp;", " ").strip() + diagrama
            if texto.strip().startswith("¡Sii"):
                acierto = limpio
            else:
                fallo = limpio

    pregunta = frappe.get_doc({"doctype": "LMS Question", "question": html, "type": "Choices"})
    for i, opcion in enumerate(datos["opciones"], start=1):
        pregunta.set(f"option_{i}", opcion["texto"])
        pregunta.set(f"is_correct_{i}", 1 if opcion["correcta"] else 0)
        explicacion = acierto if opcion["correcta"] else fallo
        if explicacion:
            pregunta.set(f"explanation_{i}", explicacion)
    pregunta.insert(ignore_permissions=True)

    correcta = next(o["texto"] for o in datos["opciones"] if o["correcta"])
    print(f"  {orden}. {pregunta.name}  {len(datos['opciones'])} opciones -> {correcta}")
    filas.append({"question": pregunta.name, "marks": PUNTOS, "type": "Choices"})

quiz = frappe.get_doc(
    {
        "doctype": "LMS Quiz",
        "title": TITULO,
        "lesson": LECCION,
        "course": "curso-de-mascotas",
        "show_answers": 1,
        "show_submission_history": 1,
        "max_attempts": 0,  # en Tally se podía repetir cuantas veces quisieras
        "passing_percentage": 0,  # el quizz es para practicar el ojo, no para aprobar
        "shuffle_questions": 0,
        "questions": filas,
    }
)
quiz.insert(ignore_permissions=True)
print(f"\ncuestionario {quiz.name}: {len(filas)} preguntas, {quiz.total_marks} puntos")

# La lección pierde el enlace al formulario y la tarea de subir la captura: el
# cuestionario ya corrige y guarda el resultado.
from lms.lms.utils import sanitize_editorjs  # noqa: E402

bloques = [
    {"type": "header", "data": {"text": "¡Es momento de poner a prueba ese ojo de artista! 👁🎨", "level": 2}, "id": "cursodemascotas42b0"},
    {
        "type": "paragraph",
        "data": {
            "text": "En este pequeño Quizz te encontrarás preguntas relacionadas al color y "
            "diferentes tonalidades en las mascotas. Entender lo que estamos viendo es crucial "
            "para pintar mascotas realistas."
        },
        "id": "cursodemascotas42b1",
    },
    {"type": "quiz", "data": {"quiz": quiz.name}, "id": "cursodemascotas42b2"},
]
contenido = sanitize_editorjs(json.dumps({"blocks": bloques}, ensure_ascii=False))
leccion = frappe.get_doc("Course Lesson", LECCION)
if leccion.content != contenido:
    leccion.content = contenido
    leccion.save(ignore_permissions=True)
    print(f"lección {LECCION} actualizada")
else:
    print(f"lección {LECCION} ya estaba al día")

if frappe.db.exists("LMS Assignment", "ASG-00144"):
    if frappe.db.count("LMS Assignment Submission", {"assignment": "ASG-00144"}):
        print("AVISO: ASG-00144 tiene entregas, no se borra")
    else:
        frappe.delete_doc("LMS Assignment", "ASG-00144", ignore_permissions=True, force=True)
        print("tarea ASG-00144 (subir foto del examen) borrada: ya no hace falta")

frappe.db.commit()
print("Listo.")
