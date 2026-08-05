"""Vuelca en el LMS el contenido real de las lecciones tal como está en Disco.

Fuentes:
  retratos_disco.json          -> texto de cada lección ya convertido a bloques
                                  de EditorJS (lo genera el scraper del navegador)
  materiales/retratos/*.pdf    -> PDFs e imágenes descargados del CDN de Disco
  materiales/retratos/mapa.json-> índice de Disco -> archivo local

Reconstruye el content de cada lección en este orden:
  1. el video de Vimeo que ya estaba (no se toca)
  2. el texto de Disco (cabeceras, párrafos, listas)
  3. el PDF o la imagen adjunta, donde corresponda
  4. el bloque de entrega, si en Disco es EXAMEN o EJERCICIO

Idempotente: reconstruye desde cero cada lección que toca, así que correrlo dos
veces deja el mismo resultado. Solo altera las lecciones presentes en el JSON.

  env/bin/python /workspace/aplicar_disco.py
"""

import base64
import json
import os

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

BASE = os.path.dirname(os.path.abspath(__file__))
DISCO = os.path.join(BASE, "retratos_disco.json")
MATERIALES = os.path.join(BASE, "materiales", "retratos")

# Disco deja este texto en las lecciones que nunca se editaron: no es contenido.
PLACEHOLDER = "Write something or type '/' for commands..."

# Cuántas lecciones tiene cada módulo del curso, en orden. Permite pasar del
# índice plano de Disco (0-55) al nombre de la lección (retratos-<mod>-<lec>).
LECCIONES_POR_MODULO = [3, 3, 5, 5, 1, 1, 2, 2, 9, 4, 21]

# En Disco el tipo de la lección define si lleva entrega.
CON_ENTREGA = {"EXAMEN", "EJERCICIO"}

# Índices de Disco que no se traen: son widgets de la propia plataforma
# ("¡Completa tu perfil!" incrusta su formulario de perfil dentro de la
# lección) y aquí no tienen equivalente ni aportan nada. La lección ya se borró
# con borrar_lecciones.py; esto evita que vuelva a llenarse.
OMITIR = {2}

CONSIGNAS = {
    "EXAMEN": "<p>Sube aquí una foto de tu examen resuelto para que podamos revisarlo.</p>",
    "EJERCICIO": "<p>Sube aquí tu trabajo terminado para que podamos revisarlo.</p>",
}


def normalizar_lista(bloque: dict) -> dict:
    """El editor usa @editorjs/nested-list, que espera cada punto como objeto.

    Una lista de cadenas ("items": ["a", "b"]) se renderiza como "undefined" en
    cada viñeta, así que hay que envolverlas en {"content": ..., "items": []}.
    """
    if bloque.get("type") != "list":
        return bloque
    items = bloque["data"].get("items") or []
    bloque["data"]["items"] = [
        {"content": i, "items": []} if isinstance(i, str) else i for i in items
    ]
    return bloque


def nombres_de_leccion() -> list:
    salida = []
    for modulo, total in enumerate(LECCIONES_POR_MODULO, start=1):
        for leccion in range(1, total + 1):
            salida.append(f"retratos-{modulo}-{leccion}")
    return salida


def subir_archivo(ruta: str, leccion: str) -> dict:
    """Sube el archivo a Frappe y devuelve los datos del bloque upload."""
    nombre = os.path.basename(ruta)
    extension = nombre.rsplit(".", 1)[-1].lower()
    # upload.js decide cómo pintar el bloque con file_type: "PDF" exacto abre el
    # visor; cualquier otra cosa que no sea video o audio se pinta como imagen.
    file_type = "PDF" if extension == "pdf" else extension

    existente = frappe.db.get_value(
        "File", {"file_name": nombre, "attached_to_name": leccion}, ["file_url"], as_dict=True
    )
    if existente:
        return {"file_url": existente.file_url, "file_type": file_type, "quizzes": []}

    with open(ruta, "rb") as fh:
        contenido = base64.b64encode(fh.read()).decode()

    doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": nombre,
            "content": contenido,
            "decode": True,
            # Privado: el material es de pago. get_lesson reescribe la URL a
            # serve_resource, que valida la inscripción antes de servirlo.
            "is_private": 1,
            "attached_to_doctype": "Course Lesson",
            "attached_to_name": leccion,
            "attached_to_field": "content",
        }
    ).insert(ignore_permissions=True)
    return {"file_url": doc.file_url, "file_type": file_type, "quizzes": []}


def assignment_para(leccion: str, curso: str, titulo: str, tipo: str) -> str:
    """Crea (o actualiza) la consigna de entrega y devuelve su name."""
    existente = frappe.db.get_value("LMS Assignment", {"course": curso, "title": titulo}, "name")
    datos = {
        "title": titulo,
        # Tipo añadido en nuestro fork: los exámenes se resuelven en papel y
        # cada alumno los entrega como puede, con foto o escaneados en PDF.
        "type": "Image or PDF",
        "question": CONSIGNAS[tipo],
        "course": curso,
    }
    if existente:
        doc = frappe.get_doc("LMS Assignment", existente)
        doc.update(datos)
        doc.save(ignore_permissions=True)
        return doc.name
    return frappe.get_doc({"doctype": "LMS Assignment", **datos}).insert(ignore_permissions=True).name


def limpiar_assignments_viejos(curso: str, conservar: set):
    """Borra las consignas que inventamos antes de tener el contenido de Disco."""
    for a in frappe.get_all("LMS Assignment", filters={"course": curso}, pluck="name"):
        if a in conservar:
            continue
        if frappe.db.exists("LMS Assignment Submission", {"assignment": a}):
            print(f"  AVISO: {a} tiene entregas de alumnos, no se borra.")
            continue
        frappe.delete_doc("LMS Assignment", a, ignore_permissions=True, force=True)
        print(f"  Eliminada la consigna obsoleta {a}")


def main():
    with open(DISCO, encoding="utf-8") as fh:
        disco = json.load(fh)

    mapa_path = os.path.join(MATERIALES, "mapa.json")
    materiales = {}
    if os.path.exists(mapa_path):
        with open(mapa_path, encoding="utf-8") as fh:
            materiales = json.load(fh)

    lecciones = nombres_de_leccion()
    if len(lecciones) != len(disco):
        frappe.throw(f"Disco trae {len(disco)} lecciones y el curso tiene {len(lecciones)}.")

    # Un desfase de una sola posición metería el examen en la lección
    # equivocada, así que se comprueba el emparejamiento antes de escribir nada.
    desajustes = []
    for indice, nombre in enumerate(lecciones):
        if indice in OMITIR:
            continue
        esperado = frappe.db.get_value("Course Lesson", nombre, "title")
        real = disco[str(indice)]["titulo"]
        if esperado and esperado.strip() != real.strip():
            desajustes.append(f"  {indice:>2} {nombre}: LMS='{esperado}' vs Disco='{real}'")
    if desajustes:
        print("El orden de las lecciones no coincide con Disco:")
        print("\n".join(desajustes))
        frappe.throw("Abortado: revisa LECCIONES_POR_MODULO antes de escribir nada.")

    curso = frappe.db.get_value("Course Lesson", lecciones[0], "course")
    assignments_vigentes = set()
    tocadas = 0

    for indice in range(len(lecciones)):
        if indice in OMITIR:
            continue
        nombre = lecciones[indice]
        origen = disco[str(indice)]

        if not frappe.db.exists("Course Lesson", nombre):
            print(f"AVISO: falta la lección {nombre} ({origen['titulo']}), se omite.")
            continue

        doc = frappe.get_doc("Course Lesson", nombre)
        contenido = json.loads(doc.content) if doc.content else {"blocks": []}
        previos = contenido.get("blocks", [])

        # 1. El video se conserva tal cual: ya está verificado contra Vimeo.
        bloques = [b for b in previos if b.get("type") == "embed"]
        tras_el_video = len(bloques)

        # 2. El texto de Disco (o el nuestro, si allí era un widget de Disco).
        pendiente_de_imagen = []
        for bloque in origen["bloques"]:
            if bloque["type"] == "imagen_pendiente":
                pendiente_de_imagen.append(len(bloques))
                continue
            if bloque["data"].get("text") == PLACEHOLDER:
                continue
            bloques.append(normalizar_lista(bloque))

        # 3. El archivo. Las imágenes van intercaladas en el texto, donde
        #    estaban en Disco; los PDFs son adjuntos y allí se muestran justo
        #    debajo del video, encima del texto.
        archivo = materiales.get(str(indice))
        if archivo:
            ruta = os.path.join(MATERIALES, archivo)
            if os.path.exists(ruta):
                datos = subir_archivo(ruta, nombre)
                bloque_archivo = {"type": "upload", "data": datos}
                posicion = pendiente_de_imagen[0] if pendiente_de_imagen else tras_el_video
                bloques.insert(posicion, bloque_archivo)
            else:
                print(f"AVISO: no encuentro {ruta}")

        # 4. La entrega.
        if origen["tipo"] in CON_ENTREGA:
            asg = assignment_para(nombre, curso, origen["titulo"], origen["tipo"])
            assignments_vigentes.add(asg)
            bloques.append({"type": "assignment", "data": {"assignment": asg}})

        for posicion, bloque in enumerate(bloques):
            bloque.setdefault("id", f"{nombre.replace('-', '')}b{posicion}")

        # Course Lesson.validate pasa el content por sanitize_editorjs, así que
        # hay que comparar contra el resultado ya saneado o el script creería
        # que hay cambios en cada pasada.
        from lms.lms.utils import sanitize_editorjs

        nuevo = sanitize_editorjs(json.dumps({"blocks": bloques}, ensure_ascii=False))
        if nuevo != (doc.content or ""):
            doc.content = nuevo
            doc.save(ignore_permissions=True)
            tocadas += 1
            resumen = ", ".join(sorted({b["type"] for b in bloques}))
            print(f"{nombre:<16} [{origen['tipo']:<9}] {origen['titulo'][:38]:<38} -> {resumen}")

    limpiar_assignments_viejos(curso, assignments_vigentes)
    frappe.db.commit()
    print(f"\n{tocadas} lecciones actualizadas.")


main()
