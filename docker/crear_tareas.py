"""Convierte lecciones en tareas de entrega (LMS Assignment).

Patrón replicable para todos los cursos. Una "tarea" en Frappe LMS son dos
piezas:

  1. Un doc LMS Assignment con la consigna (title, question en HTML, type).
     type define QUÉ sube el alumno: Image, PDF, Document, URL o Text.
  2. Un bloque de EditorJS dentro del content de la lección:
     {"type": "assignment", "data": {"assignment": "ASG-00001"}}

Con eso el alumno ve un formulario embebido para subir su trabajo, se crea un
LMS Assignment Submission, y la lección NO se marca como completada hasta que
entregue (course_lesson.get_assignment_progress).

Idempotente: busca el assignment por (curso, título) antes de crear, y no
duplica el bloque si la lección ya lo tiene.

  env/bin/python /workspace/crear_tareas.py
"""

import json

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

# leccion -> definición de la tarea
TAREAS = {
    "retratos-8-1": {
        "titulo": "Desafío: elementos del rostro",
        "tipo": "Image",
        "intro": (
            "Es hora de poner a prueba lo que aprendiste. Practica cada elemento "
            "por separado y comparte tu hoja de ejercicios."
        ),
        "consigna": (
            "<p>En una sola hoja, dibuja al menos <b>un ejemplo de cada elemento</b> "
            "que vimos en los módulos anteriores:</p>"
            "<ul>"
            "<li>Un ojo con su mirada y brillo</li>"
            "<li>Una boca</li>"
            "<li>Una nariz</li>"
            "<li>Una oreja</li>"
            "<li>Un mechón de cabello</li>"
            "</ul>"
            "<p>Sube una foto de la hoja completa. Fíjate sobre todo en las sombras "
            "y en el volumen de cada elemento.</p>"
        ),
    },
    "retratos-8-2": {
        "titulo": "Desafío: proporciones del rostro",
        "tipo": "Image",
        "intro": (
            "El segundo desafío: demuestra que ya dominas las proporciones en las "
            "tres orientaciones."
        ),
        "consigna": (
            "<p>Boceta <b>un mismo rostro en las tres orientaciones</b> que vimos:</p>"
            "<ul>"
            "<li>De frente</li>"
            "<li>En 3/4</li>"
            "<li>De perfil</li>"
            "</ul>"
            "<p>No hace falta detallarlos: lo que se califica son las líneas guía y "
            "la ubicación correcta de los elementos. Sube una foto de los tres juntos.</p>"
        ),
    },
    "retratos-9-9": {
        "titulo": "Sube tu retrato a lápiz",
        "tipo": "Image",  # Image | PDF | Document | URL | Text
        "intro": (
            "Llegaste al final del primer proyecto. Ahora toca ver tu trabajo: "
            "sube una foto de tu retrato a lápiz terminado."
        ),
        "consigna": (
            "<p>Sube una <b>foto de tu retrato a lápiz terminado</b>.</p>"
            "<p>Para que se vea bien:</p>"
            "<ul>"
            "<li>Toma la foto con luz natural y sin sombras encima del papel.</li>"
            "<li>Encuadra solo el dibujo, de frente y sin inclinación.</li>"
            "<li>Formato JPG o PNG.</li>"
            "</ul>"
            "<p>No busques la perfección: lo importante es que apliques las "
            "proporciones y el sombreado que vimos en el módulo.</p>"
        ),
    },
    "retratos-11-21": {
        "titulo": "Comparte tu retrato en pintura",
        "tipo": "Image",
        "intro": (
            "Terminaste el curso completo. Queremos ver tu obra final: sube la foto "
            "de tu retrato en pintura."
        ),
        "consigna": (
            "<p>Sube una <b>foto de tu retrato en pintura terminado</b>.</p>"
            "<p>Para que los colores se vean fieles:</p>"
            "<ul>"
            "<li>Fotografía con luz natural, nunca con flash.</li>"
            "<li>Espera a que la pintura esté seca para evitar reflejos.</li>"
            "<li>Encuadra el lienzo completo, de frente.</li>"
            "</ul>"
            "<p>Cuéntanos en el foro de la lección qué fue lo que más te costó: "
            "es la mejor forma de que te demos retroalimentación útil.</p>"
        ),
    },
}


def bloque_assignment(assignment: str, block_id: str) -> dict:
    return {"id": block_id, "type": "assignment", "data": {"assignment": assignment}}


def parrafo(texto: str, block_id: str) -> dict:
    return {"id": block_id, "type": "paragraph", "data": {"text": texto}}


for leccion, cfg in TAREAS.items():
    if not frappe.db.exists("Course Lesson", leccion):
        print(f"AVISO: la lección {leccion} no existe, se omite.")
        continue

    curso = frappe.db.get_value("Course Lesson", leccion, "course")

    # 1. La consigna. El name lo genera Frappe (ASG-#####), así que la
    #    idempotencia va por (curso, título).
    existente = frappe.db.get_value(
        "LMS Assignment", {"course": curso, "title": cfg["titulo"]}, "name"
    )
    if existente:
        assignment = frappe.get_doc("LMS Assignment", existente)
        assignment.question = cfg["consigna"]
        assignment.type = cfg["tipo"]
        assignment.save(ignore_permissions=True)
        print(f"Actualizada la consigna {assignment.name} ({cfg['titulo']})")
    else:
        assignment = frappe.get_doc(
            {
                "doctype": "LMS Assignment",
                "title": cfg["titulo"],
                "type": cfg["tipo"],
                "question": cfg["consigna"],
                "course": curso,
            }
        ).insert(ignore_permissions=True)
        print(f"Creada la consigna {assignment.name} ({cfg['titulo']})")

    # 2. El bloque dentro de la lección.
    doc = frappe.get_doc("Course Lesson", leccion)
    contenido = json.loads(doc.content) if doc.content else {"blocks": []}
    bloques = contenido.get("blocks", [])

    ya_tiene = any(
        b.get("type") == "assignment" and b.get("data", {}).get("assignment") == assignment.name
        for b in bloques
    )
    if ya_tiene:
        print(f"  {leccion}: el bloque ya estaba, no se duplica.")
        continue

    # Quita el placeholder de "contenido por agregar" si sigue ahí.
    bloques = [
        b
        for b in bloques
        if not (b.get("type") == "paragraph" and "Contenido por agregar" in b.get("data", {}).get("text", ""))
    ]

    slug = leccion.replace("-", "")
    bloques.append(parrafo(cfg["intro"], f"{slug}intro"))
    bloques.append(bloque_assignment(assignment.name, f"{slug}tarea"))

    contenido["blocks"] = bloques
    doc.content = json.dumps(contenido, ensure_ascii=False)
    doc.save(ignore_permissions=True)
    print(f"  {leccion}: bloque de tarea añadido.")
    print(f"  content -> {doc.content}\n")

frappe.db.commit()
print("Listo.")
