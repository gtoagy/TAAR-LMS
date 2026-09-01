"""Arma el curso del Proyecto Mar: los cuatro videos, sus textos y la entrega.

El curso ya existia publicado en produccion con su portada, su introduccion y
sus banderas de venta revisadas — pero por dentro estaba vacio, sin un solo
capitulo. Esto lo llena.

Se separa de `construir_cursos.py` a proposito, aunque copie su forma. Aquel
lee el contenido de los JSON raspados de Disco y de la carpeta `materiales/`,
que **no viaja en git**: en produccion no existe ninguna de las dos cosas. Este
es autonomo — el texto vive aqui dentro y las imagenes se bajan de la CDN de
Vimeo—, asi que corre igual en el docker de local que en la consola del
servidor, que es donde hace falta hoy.

  local:      env/bin/python /workspace/construir_proyecto_mar.py
  produccion: se pega entero en `bench --site <sitio> console`

Es idempotente: los nombres son deterministas (`proyecto-mar-m1`,
`proyecto-mar-1-1`), asi que volver a pasarlo actualiza en vez de duplicar.

  OJO: reescribe el `content` entero de cada leccion. En cuanto el dueno edite
  los textos desde el LMS, volver a pasarlo se los lleva por delante. A partir
  de ese momento se toca a mano lo que falte, no se repite el guion a ciegas.
"""

import base64
import json
import os
import urllib.request

import frappe

CURSO = "proyecto-mar"

# Los cuatro videos, ya en Vimeo y ocultos en vimeo.com (solo se ven embebidos).
VIDEOS = {
    "intro": "1222247616",
    "colores": "1222247615",
    "mar": "1222247614",
    "textura": "1222247613",
}

# Un fotograma de cada video, en el momento en que la obra queda como debe
# quedar al terminar esa parte. Se eligieron mirando el video entero: el final
# de verdad no sirve —ahi ya esta la despedida hablando a camara— y lo que la
# alumna necesita ver es el lienzo desde arriba y sin manos encima.
#
# Se bajan de la CDN de Vimeo, que sirve sin credenciales. Asi el guion se
# puede pegar en una consola remota sin que viaje ni un byte de imagen.
CAPTURAS = {
    "referencia": "https://i.vimeocdn.com/video/2195954436-6385c3aeb521634bba2e4bacc758828d37aa9cf2e87793cb47fff54fa84a30db-d_1920x1080?&r=pad&region=us",
    "colores": "https://i.vimeocdn.com/video/2195954471-4337e60f6670e76540230f86af08403938523c360d4dfbfb2722464273c8dcef-d_1920x1080?&r=pad&region=us",
    "mar": "https://i.vimeocdn.com/video/2195954491-3d626022fef382c1815a097f3c732403b0295b9559449b66b49d90821cfbc759-d_1920x1080?&r=pad&region=us",
    "final": "https://i.vimeocdn.com/video/2195954511-98c6df32501ed5dbbb31cfdf7eaae5d900e57607251b1ba03b882968023e978f-d_1920x1080?&r=pad&region=us",
}


# --------------------------------------------------------------------------
# Bloques de EditorJS
# --------------------------------------------------------------------------


def video(clave: str) -> dict:
    vid = VIDEOS[clave]
    return {
        "type": "embed",
        "data": {
            "service": "vimeo",
            "source": f"https://vimeo.com/{vid}",
            "embed": f"https://player.vimeo.com/video/{vid}",
            "width": 580,
            "height": 320,
            "caption": "",
        },
    }


def p(texto: str) -> dict:
    return {"type": "paragraph", "data": {"text": texto}}


def h(texto: str, nivel: int = 3) -> dict:
    return {"type": "header", "data": {"text": texto, "level": nivel}}


def lista(items: list, ordenada: bool = False) -> dict:
    # El editor usa @editorjs/nested-list: cada punto es un dict. Con cadenas
    # sueltas cada vinyeta sale como "undefined".
    return {
        "type": "list",
        "data": {
            "style": "ordered" if ordenada else "unordered",
            "items": [{"content": i, "items": []} for i in items],
        },
    }


def imagen(clave: str) -> dict:
    """Marcador: se cambia por el bloque `upload` real al construir la leccion."""
    return {"type": "_captura", "data": {"clave": clave}}


# --------------------------------------------------------------------------
# El curso
# --------------------------------------------------------------------------

MATERIALES = [
    "Lienzo de 30x30 cm",
    "Pinturas acrílicas: azul cobalto, rojo, amarillo y blanco",
    "Gesso",
    "Polvo de mármol de grano fino",
    "Resistol o pegamento blanco",
    "Un recipiente mediano y dos chicos",
    "Pinceles (abajo te digo cuáles)",
    "Agua y papel",
    "Godete",
    "Espátula",
]

PINCELES = [
    "De cerda natural: no. 10, no. 22 y no. 2 (opcional)",
    "Redondo suave: no. 8 y no. 5 (opcional)",
    "Uno plano, o una esponja",
]

MODULOS = [
    (
        "🌊 Prepárate para pintar el mar",
        [
            {
                "titulo": "Lista de materiales",
                "bloques": [
                    h("🎨 Todo lo que necesitas para pintar el mar"),
                    p(
                        "¡Hola artista! Antes de empezar, junta todo lo que vas a "
                        "usar. Así te sientas a pintar y ya no te levantas ✨"
                    ),
                    lista(MATERIALES, ordenada=True),
                    h("🖌 Los pinceles"),
                    lista(PINCELES),
                    p(
                        "Y si te falta alguno, no te detengas por eso: con lo que "
                        "tengas a la mano se puede. Lo importante es empezar 💙"
                    ),
                ],
            },
            {
                "titulo": "1. Empecemos",
                "bloques": [
                    video("intro"),
                    p(
                        "Aquí te cuento de qué va el Proyecto Mar y te enseño la foto "
                        "que vamos a interpretar: una orilla vista desde arriba, con "
                        "la espuma rompiendo sobre la arena."
                    ),
                    p(
                        "También repaso los materiales uno por uno y qué pincel "
                        "conviene para cada cosa. Si todavía no tienes todo, este "
                        "video te ayuda a decidir qué comprar."
                    ),
                    p("Esta es la referencia que vamos a pintar 👇🏼"),
                    imagen("referencia"),
                ],
            },
        ],
    ),
    (
        "🖌 Pintemos el mar",
        [
            {
                "titulo": "2. Los colores base",
                "bloques": [
                    video("colores"),
                    p(
                        "Empezamos por el fondo: preparamos el lienzo con gesso y "
                        "montamos la playa entera antes de meternos con los detalles."
                    ),
                    p(
                        "Aquí ves cómo mezclar el tono de la arena, cómo llevarlo "
                        "hacia el azul sin que se corte, y el truco de la esponja "
                        "para que el degradado quede suavecito."
                    ),
                    p(
                        "Tómate tu tiempo con esta parte. Si la base queda bien, "
                        "todo lo demás cae solo."
                    ),
                    p("Así debe quedar al terminar 👇🏼"),
                    imagen("colores"),
                ],
            },
            {
                "titulo": "3. El mar",
                "bloques": [
                    video("mar"),
                    p(
                        "Ahora le damos vida al agua. Trabajamos los azules por capas "
                        "para crear profundidad: la parte honda, el bajo donde el agua "
                        "se aclara, y las manchas de espuma que se ven desde arriba."
                    ),
                    p(
                        "Es la parte donde el cuadro empieza a parecer mar de verdad 🌊"
                    ),
                    p("Así debe quedar al terminar 👇🏼"),
                    imagen("mar"),
                ],
            },
            {
                "titulo": "4. Textura y toques finales",
                "bloques": [
                    video("textura"),
                    p(
                        "Llegó lo mejor: la espuma en relieve. Mezclamos el polvo de "
                        "mármol con el pegamento y la vamos poniendo con la espátula, "
                        "para que la ola se sienta al tocarla."
                    ),
                    p(
                        "Cerramos con los últimos detalles y tu obra queda lista para "
                        "colgarse."
                    ),
                    p("Así queda terminada 👇🏼"),
                    imagen("final"),
                ],
            },
        ],
    ),
    (
        "🐚 ¡Obra terminada!",
        [
            {
                "titulo": "Comparte tu resultado",
                "tarea": "Sube tu Proyecto Mar",
                "bloques": [
                    p(
                        "¡Lo lograste!! 🎉 Sube aquí la foto de tu obra terminada "
                        "para que podamos verla."
                    ),
                    p(
                        "Cada quien lo interpreta a su manera y esa es la mejor parte: "
                        "ningún mar sale igual que otro 💙"
                    ),
                ],
            },
        ],
    ),
]

CONSIGNA = "<p>Sube aquí la foto de tu obra terminada para que podamos verla.</p>"


# --------------------------------------------------------------------------
# Construccion
# --------------------------------------------------------------------------


def bajar(url: str) -> bytes:
    peticion = urllib.request.Request(url, headers={"User-Agent": "taar-lms"})
    with urllib.request.urlopen(peticion, timeout=60) as r:
        return r.read()


def subir_captura(clave: str, leccion: str) -> dict:
    """Guarda el fotograma como adjunto de la leccion, una sola vez."""
    nombre = f"proyecto-mar-{clave}.jpg"
    existente = frappe.db.get_value(
        "File", {"file_name": nombre, "attached_to_name": leccion}, "file_url"
    )
    if existente:
        return {"file_url": existente, "file_type": "jpg", "quizzes": []}

    doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": nombre,
            "content": base64.b64encode(bajar(CAPTURAS[clave])).decode(),
            "decode": True,
            "is_private": 1,
            "attached_to_doctype": "Course Lesson",
            "attached_to_name": leccion,
            "attached_to_field": "content",
        }
    ).insert(ignore_permissions=True)
    return {"file_url": doc.file_url, "file_type": "jpg", "quizzes": []}


def tarea(titulo: str) -> str:
    campos = {
        "title": titulo,
        "type": "Image or PDF",
        "question": CONSIGNA,
        "course": CURSO,
    }
    existente = frappe.db.get_value("LMS Assignment", {"course": CURSO, "title": titulo}, "name")
    if existente:
        doc = frappe.get_doc("LMS Assignment", existente)
        doc.update(campos)
        doc.save(ignore_permissions=True)
        return doc.name
    return frappe.get_doc({"doctype": "LMS Assignment", **campos}).insert(
        ignore_permissions=True
    ).name


def construir():
    if not frappe.db.exists("LMS Course", CURSO):
        frappe.throw(f"El curso {CURSO} no existe. Este guion llena uno que ya está creado.")

    # No se toca nada del curso: portada, introduccion, precio y banderas de
    # venta ya estan revisados en produccion. Solo se le cuelga la estructura.
    capitulos = []

    for m_idx, (titulo_modulo, lecciones) in enumerate(MODULOS, start=1):
        cap_name = f"{CURSO}-m{m_idx}"
        if frappe.db.exists("Course Chapter", cap_name):
            capitulo = frappe.get_doc("Course Chapter", cap_name)
            capitulo.title = titulo_modulo
        else:
            capitulo = frappe.new_doc("Course Chapter")
            capitulo.update({"title": titulo_modulo, "course": CURSO})
        capitulo.set("lessons", [])
        if capitulo.is_new():
            capitulo.insert(ignore_permissions=True, set_name=cap_name)
        else:
            capitulo.save(ignore_permissions=True)

        for l_idx, definicion in enumerate(lecciones, start=1):
            lec_name = f"{CURSO}-{m_idx}-{l_idx}"

            if frappe.db.exists("Course Lesson", lec_name):
                leccion = frappe.get_doc("Course Lesson", lec_name)
            else:
                leccion = frappe.new_doc("Course Lesson")

            # El content arranca con "blocks" vacio, no con "{}": el hook
            # save_lesson_details_in_quiz itera content["blocks"] al guardar y
            # revienta con None si la clave no esta.
            leccion.update(
                {
                    "title": definicion["titulo"],
                    "chapter": cap_name,
                    "course": CURSO,
                    "content": '{"blocks": []}',
                }
            )
            if leccion.is_new():
                leccion.insert(ignore_permissions=True, set_name=lec_name)
            else:
                leccion.save(ignore_permissions=True)

            # Las capturas necesitan que la leccion exista para colgarse de ella.
            bloques = []
            for bloque in definicion["bloques"]:
                if bloque["type"] == "_captura":
                    bloques.append(
                        {"type": "upload", "data": subir_captura(bloque["data"]["clave"], lec_name)}
                    )
                else:
                    bloques.append(bloque)

            if definicion.get("tarea"):
                bloques.append({"type": "assignment", "data": {"assignment": tarea(definicion["tarea"])}})

            for pos, b in enumerate(bloques):
                b.setdefault("id", f"{lec_name.replace('-', '')}b{pos}")
            leccion.content = json.dumps({"blocks": bloques}, ensure_ascii=False)
            leccion.save(ignore_permissions=True)

            capitulo.append("lessons", {"lesson": lec_name})
            resumen = ", ".join(sorted({b["type"] for b in bloques}))
            print(f"  {lec_name:<20} {definicion['titulo'][:34]:<34} -> {resumen}")

        capitulo.save(ignore_permissions=True)
        capitulos.append(cap_name)
        print(f"  {cap_name}  {titulo_modulo}")

    # El curso se guarda al final: hacerlo dentro del bucle choca con las
    # escrituras de capitulos y lecciones (TimestampMismatchError).
    doc = frappe.get_doc("LMS Course", CURSO)
    doc.set("chapters", [{"chapter": c} for c in capitulos])
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    propias = frappe.db.count("Course Lesson", {"course": CURSO})
    # Solo las de este curso: el fallo que se busca es la leccion que existe sin
    # colgar de ningun capitulo, y ahi no puede verla nadie. Contar las de todo
    # el sitio no dice nada.
    enlazadas = frappe.db.count(
        "Lesson Reference", {"parenttype": "Course Chapter", "parent": ["in", capitulos]}
    )
    print(f"\nListo. {propias} lecciones del curso, {len(capitulos)} capítulos.")
    print(f"Enlazadas desde un capítulo: {enlazadas}", end="")
    print("  (todas)" if enlazadas == propias else "  ¡FALTAN, hay lecciones invisibles!")


def ensayo():
    """Dice lo que va a pasar, sin escribir nada.

    Antes de tocar produccion importan tres cosas y ninguna se ve desde aqui:
    que el curso este donde creemos, que no vayamos a pisar lecciones que ya
    tengan progreso de alumnas, y que el servidor pueda bajarse las imagenes de
    la CDN de Vimeo — si esa maquina no sale a internet, el guion se planta a
    mitad y deja el curso en obras.
    """
    if not frappe.db.exists("LMS Course", CURSO):
        print(f"✗ El curso {CURSO} NO existe. El guion no lo crea: se pararia aqui.")
        return

    curso = frappe.get_doc("LMS Course", CURSO)
    print(f"Curso: {curso.title}  (publicado={curso.published})")
    print(f"Ahora mismo tiene {len(curso.chapters)} capítulos y ", end="")
    print(f"{frappe.db.count('Course Lesson', {'course': CURSO})} lecciones.\n")

    for m_idx, (titulo_modulo, lecciones) in enumerate(MODULOS, start=1):
        cap_name = f"{CURSO}-m{m_idx}"
        estado = "actualiza" if frappe.db.exists("Course Chapter", cap_name) else "CREA"
        print(f"  {estado:<9} {cap_name:<18} {titulo_modulo}")
        for l_idx, definicion in enumerate(lecciones, start=1):
            lec_name = f"{CURSO}-{m_idx}-{l_idx}"
            existe = frappe.db.exists("Course Lesson", lec_name)
            estado = "actualiza" if existe else "CREA"
            aviso = ""
            if existe:
                # Si alguien ya la vio, reescribirla no es gratis: se avisa.
                vistas = frappe.db.count("LMS Course Progress", {"lesson": lec_name})
                if vistas == 1:
                    aviso = "  ← ojo: 1 alumna ya la tiene vista"
                elif vistas:
                    aviso = f"  ← ojo: {vistas} alumnas ya la tienen vista"
            print(f"    {estado:<9} {lec_name:<18} {definicion['titulo']}{aviso}")

    print("\n¿El servidor alcanza las imágenes de Vimeo?")
    for clave, url in CAPTURAS.items():
        try:
            peticion = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "taar-lms"})
            with urllib.request.urlopen(peticion, timeout=30) as r:
                print(f"  ✓ {clave:<12} {r.status}  {r.headers.get('Content-Length', '?')} bytes")
        except Exception as e:  # noqa: BLE001 — cualquier fallo aquí importa igual
            print(f"  ✗ {clave:<12} {e}")

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
        construir()
