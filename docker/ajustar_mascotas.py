"""Los dos retoques del Curso de Mascotas que hay que poder repetir.

1. Despega el capitulo "Proyecto #1 (Perrito en funda)" del curso, SIN borrar
   nada: se quita solo la fila de `chapters`, y el capitulo, sus nueve
   lecciones, sus videos y el progreso de quien ya las vio siguen ahi. Volver a
   colgarlo es anadir de nuevo la fila.

2. Asegura la leccion "Calca la imagen de referencia" en el Proyecto Final,
   justo despues de "¡Descarga la imagen de referencia!". Es el mismo video que
   ya usa Proyecto Rocky: sin ella la alumna descarga la imagen y lo siguiente
   que ve es "¡Empecemos con los tonos base!", sin que nadie le haya dicho como
   pasar el dibujo al lienzo.

Por que existe este guion y no se toca `construir_cursos.py`: aquel sigue
definiendo el perrito como modulo `m9` (linea 252) y sus docnames son
POSICIONALES (`curso-de-mascotas-10-3`), asi que quitarle un modulo renumera
todos los siguientes y le mete a cada leccion el contenido de su vecina. El
8-ago-2026 se comprobo que el capitulo habia reaparecido en produccion: no lo
resucito nadie, es que el 5-ago se reimportaron todos los cursos desde un export
del docker local y la reimportacion lo trajo de vuelta. Cada vez que eso pase,
hay que volver a pasar este guion.

Es autonomo a proposito —no lee `docker/materiales/` ni los JSON de Disco, que
no viajan en git— y resuelve todo POR TITULO, nunca por docname, porque en local
los nombres son `curso-de-mascotas-8-3` y en produccion son autonombrados
(`0381 ¡Descarga la imagen de referencia!`).

  local:      env/bin/python /workspace/ajustar_mascotas.py
  produccion: se pega entero en `bench --site <sitio> console`

Idempotente: si ya esta aplicado, no escribe nada.
"""

import json
import os

import frappe

from lms.lms.utils import recalculate_course_progress

CURSO = "curso-de-mascotas"

CAP_PERRITO = "🐩 Proyecto #1 (Perrito en funda)"
CAP_PROYECTO_FINAL = "💪🏼 Proyecto Final"

LECCION = "Calca la imagen de referencia"
LECCION_ANTERIOR = "¡Descarga la imagen de referencia!"

# El mismo video que la leccion homonima de Proyecto Rocky. En el inventario de
# Vimeo aparece como "FUNDAMENTOS-Transfiere tus imagenes" (3 min).
VIMEO = "1211793443"

CONTENIDO = json.dumps(
    {
        "blocks": [
            {
                "id": "mascotascalcab0",
                "type": "embed",
                "data": {
                    "service": "vimeo",
                    "source": f"https://vimeo.com/{VIMEO}",
                    "embed": f"https://player.vimeo.com/video/{VIMEO}",
                    "width": 580,
                    "height": 320,
                    "caption": "",
                },
            }
        ]
    },
    ensure_ascii=False,
)


def capitulo_por_titulo(titulo):
    """El docname del capitulo del curso cuyo `title` es `titulo`, o None."""
    for fila in frappe.get_doc("LMS Course", CURSO).chapters:
        if frappe.db.get_value("Course Chapter", fila.chapter, "title") == titulo:
            return fila.chapter
    return None


def capitulo_suelto(titulo):
    """Igual, pero busca entre TODOS los capitulos del curso, colgados o no."""
    for nombre in frappe.get_all("Course Chapter", filters={"course": CURSO}, pluck="name"):
        if frappe.db.get_value("Course Chapter", nombre, "title") == titulo:
            return nombre
    return None


def despegar_perrito(ensayo=False):
    cap = capitulo_por_titulo(CAP_PERRITO)
    if not cap:
        print(f"  ya despegado: '{CAP_PERRITO}' no cuelga del curso")
        return False

    if ensayo:
        lecciones = frappe.db.count("Lesson Reference", {"parent": cap})
        print(f"  se despegaria '{cap}' ({lecciones} lecciones, que NO se borran)")
        return True

    curso = frappe.get_doc("LMS Course", CURSO)
    curso.set("chapters", [f for f in curso.chapters if f.chapter != cap])
    curso.save(ignore_permissions=True)
    print(f"  despegado '{cap}' (sigue existiendo entero, solo deja de verse)")
    return True


def asegurar_calcado(ensayo=False):
    cap = capitulo_por_titulo(CAP_PROYECTO_FINAL)
    if not cap:
        print(f"  AVISO: no encuentro el capitulo '{CAP_PROYECTO_FINAL}'; no toco nada")
        return False

    capitulo = frappe.get_doc("Course Chapter", cap)
    titulos = {
        fila.lesson: frappe.db.get_value("Course Lesson", fila.lesson, "title")
        for fila in capitulo.lessons
    }
    if LECCION in titulos.values():
        print(f"  ya existe: '{LECCION}' en '{CAP_PROYECTO_FINAL}'")
        return False

    # La posicion se calcula, no se escribe a mano: va detras de la leccion de
    # descargar la imagen. Si esa no estuviera, se va al final antes que
    # adivinar un hueco.
    orden = [fila.lesson for fila in sorted(capitulo.lessons, key=lambda f: f.idx)]
    destino = len(orden)
    for pos, leccion in enumerate(orden):
        if titulos[leccion] == LECCION_ANTERIOR:
            destino = pos + 1
            break
    else:
        print(f"  AVISO: no encuentro '{LECCION_ANTERIOR}'; la pongo al final")

    if ensayo:
        print(f"  se crearia '{LECCION}' en la posicion {destino + 1} de '{cap}'")
        return True

    leccion = frappe.new_doc("Course Lesson")
    leccion.update(
        {
            "title": LECCION,
            "chapter": cap,
            "course": CURSO,
            "content": CONTENIDO,
        }
    )
    leccion.insert(ignore_permissions=True)

    orden.insert(destino, leccion.name)
    capitulo.set("lessons", [{"lesson": nombre} for nombre in orden])
    capitulo.save(ignore_permissions=True)

    print(f"  creada '{leccion.name}' en la posicion {destino + 1} de '{cap}'")
    return True


def recalcular_progreso():
    """Deja el porcentaje de cada alumna acorde al numero de lecciones de hoy.

    Hace falta porque `Course Lesson.after_insert` encola el recalculo ANTES de
    que exista el `Lesson Reference` de la leccion nueva: `get_lesson_count`
    cuenta las lecciones que el curso referencia en ese instante, asi que sin
    esto todo el mundo se queda dividido entre una leccion de menos. Se corrige
    solo la primera vez que la alumna completa algo, pero mientras tanto el
    porcentaje esta inflado.
    """
    inscripciones = frappe.get_all("LMS Enrollment", filters={"course": CURSO}, pluck="member")
    for miembro in inscripciones:
        recalculate_course_progress(CURSO, miembro)
    print(f"  progreso recalculado en {len(inscripciones)} inscripciones")


def ajustar():
    print(f"Ajustando '{CURSO}':")
    despegar_perrito()
    asegurar_calcado()
    recalcular_progreso()
    frappe.db.commit()

    curso = frappe.get_doc("LMS Course", CURSO)
    total = frappe.db.count("Lesson Reference", {"parent": ("in", [f.chapter for f in curso.chapters])})
    print(f"\nEl curso queda con {len(curso.chapters)} capitulos y {total} lecciones.")

    huerfano = capitulo_suelto(CAP_PERRITO)
    if huerfano:
        lecciones = frappe.db.count("Lesson Reference", {"parent": huerfano})
        print(f"El perrito sigue guardado en '{huerfano}' con sus {lecciones} lecciones.")


def ensayo():
    print(f"ENSAYO sobre '{CURSO}':")
    despegar_perrito(ensayo=True)
    asegurar_calcado(ensayo=True)
    inscripciones = frappe.db.count("LMS Enrollment", {"course": CURSO})
    print(f"  se recalcularia el progreso de {inscripciones} inscripciones")
    print("\nEnsayo. No se ha escrito nada.")


if __name__ == "__main__":
    # Dentro de `bench console` el sitio ya viene conectado; ejecutado como
    # guion suelto, no. `frappe.local.site` no existe hasta que se inicia —
    # consultarlo sin red revienta con AttributeError, no devuelve None.
    if not getattr(frappe.local, "site", None):
        frappe.init(site=os.environ.get("SITIO", "lms.localhost"))
        frappe.connect()
    frappe.set_user("Administrator")

    import sys

    if "--ensayo" in sys.argv or os.environ.get("ENSAYO") == "1":
        ensayo()
    else:
        ajustar()
