"""Construye en el LMS los cursos que faltaban, con el contenido de Disco.

Cubre tres casos:
  - Arte en fundas: existe con 2 lecciones sueltas y se rehace con las 7 de Disco.
  - Nenúfares y Workshop Pelaje: no existían, se crean enteros.

El contenido sale de los JSON que deja el scraper del navegador
(fundas_disco.json, nenufares_disco.json); los videos ya están en Vimeo y los
PDFs en materiales/.

Los nombres de capítulo y lección son deterministas (<curso>-m<n>,
<curso>-<n>-<m>), así que volver a ejecutarlo actualiza en vez de duplicar.

  env/bin/python /workspace/construir_cursos.py
"""

import base64
import json
import os

import frappe
from bs4 import BeautifulSoup

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

BASE = os.path.dirname(os.path.abspath(__file__))
MATERIALES = os.path.join(BASE, "materiales")
INSTRUCTOR = "instructor@taar.test"
PLACEHOLDER = "Write something or type '/' for commands..."

CONSIGNAS = {
    "EXAMEN": "<p>Sube aquí una foto de tu examen resuelto para que podamos revisarlo.</p>",
    "EJERCICIO": "<p>Sube aquí tu trabajo terminado para que podamos revisarlo.</p>",
}


# --------------------------------------------------------------------------
# Conversión del HTML de Disco a bloques de EditorJS
# --------------------------------------------------------------------------

BLOQUE = ("p", "h1", "h2", "h3", "h4", "ul", "ol", "img")


def _inline(tag) -> str:
    """Deja solo el marcado que EditorJS entiende dentro de un bloque."""
    copia = BeautifulSoup(str(tag), "html.parser")
    for elemento in copia.find_all(["svg", "button", "noscript"]):
        elemento.decompose()
    for elemento in copia.find_all(True):
        if elemento.name == "strong":
            elemento.name = "b"
        elif elemento.name == "em":
            elemento.name = "i"
        elif elemento.name in ("span", "div"):
            elemento.unwrap()
            continue
        elif elemento.name == "img":
            elemento.replace_with("")
            continue
        if elemento.name not in ("b", "i", "u", "a", "br", "code"):
            elemento.attrs = {}
        else:
            elemento.attrs = {k: v for k, v in elemento.attrs.items() if k == "href"}
    raiz = copia.find()
    interior = raiz.decode_contents() if raiz else copia.decode_contents()
    return " ".join(interior.split()).strip()


def _vacio(texto: str) -> bool:
    """Un párrafo que solo trae saltos de línea o el aviso de Disco no es contenido."""
    limpio = BeautifulSoup(texto or "", "html.parser").get_text().replace("\xa0", " ").strip()
    return not limpio or limpio == PLACEHOLDER


def html_a_bloques(html: str) -> list:
    if not html:
        return []
    sopa = BeautifulSoup(html, "html.parser")
    for elemento in sopa.find_all(["svg", "button"]):
        elemento.decompose()

    bloques = []
    for tag in sopa.find_all(BLOQUE):
        # Solo los de primer nivel: los anidados los procesa su contenedor.
        if tag.find_parent(BLOQUE):
            continue
        if tag.name in ("h1", "h2", "h3", "h4"):
            texto = _inline(tag)
            if texto:
                bloques.append({"type": "header", "data": {"text": texto, "level": int(tag.name[1])}})
        elif tag.name in ("ul", "ol"):
            items = [_inline(li) for li in tag.find_all("li", recursive=False)]
            items = [{"content": i, "items": []} for i in items if i]
            if items:
                estilo = "unordered" if tag.name == "ul" else "ordered"
                bloques.append({"type": "list", "data": {"style": estilo, "items": items}})
        elif tag.name == "img":
            bloques.append({"type": "imagen_pendiente", "data": {}})
        else:
            texto = _inline(tag)
            if not _vacio(texto):
                bloques.append({"type": "paragraph", "data": {"text": texto}})
    return bloques


def normalizar(bloques: list) -> list:
    """Adapta bloques que ya venían convertidos por el scraper."""
    salida = []
    for b in bloques:
        if b.get("type") in ("paragraph", "header") and _vacio(b.get("data", {}).get("text")):
            continue
        if b.get("type") == "list":
            items = b["data"].get("items") or []
            b["data"]["items"] = [
                {"content": i, "items": []} if isinstance(i, str) else i for i in items
            ]
        salida.append(b)
    return salida


# --------------------------------------------------------------------------
# Definición de los cursos
# --------------------------------------------------------------------------

CURSOS = [
    {
        "name": "resina-en-fundas",  # ya existe; se conserva para no romper enlaces
        "title": "Arte en fundas",
        "intro": "Pinta y personaliza fundas de celular: hoja de oro, bordes limpios, calcado y acabado con resina.",
        "descripcion": (
            "<p>Convierte una funda de celular en una obra tuya. Empezamos por las "
            "técnicas que marcan la diferencia —colocar hoja de oro, dejar los bordes "
            "limpios y calcar tu imagen de referencia— y terminamos sellando el "
            "trabajo con resina para que dure.</p>"
        ),
        "portada": "arte-en-fundas.png",
        "datos": "fundas_disco.json",
        "materiales": "fundas",
        "rehacer": True,
        "modulos": [
            ("✨ ¡Inspírate con estos diseños!", [{"i": 0}]),
            (
                "👩🏻‍🎨 TanTips para crear en fundas",
                [{"i": 1, "vimeo": "1215896925"}, {"i": 2, "vimeo": "1215897285"}, {"i": 3, "vimeo": "1215897418"}],
            ),
            (
                "🫗 Uso de resina",
                [{"i": 4, "vimeo": "1212758587"}, {"i": 5}, {"i": 6, "vimeo": "1212758609"}],
            ),
        ],
    },
    {
        "name": "nenufares",
        "title": "Nenúfares",
        "intro": "Pinta tu versión de los Nenúfares de Monet en un workshop guiado paso a paso.",
        "descripcion": (
            "<p>Una sesión completa para pintar tu propia interpretación de los "
            "<b>Nenúfares de Monet</b>. Vas a trabajar el color, la pincelada suelta y "
            "los reflejos del agua que hicieron famosa la serie.</p>"
            "<p>Incluye la guía en PDF con el paso a paso y la lista de materiales.</p>"
        ),
        "portada": "nenufares.png",
        "datos": "nenufares_disco.json",
        "materiales": "nenufares",
        "modulos": [
            ("🪷 Prepárate para el Workshop", [{"i": 0}, {"i": 1}]),
            ('🎨 Pintemos los "Nenúfares" de Monet', [{"i": 3, "vimeo": "1215907657"}, {"i": 4, "vimeo": "1215907744"}]),
            ("🌸 ¡Obra terminada! Muestra tu resultado", [{"i": 5}]),
        ],
    },
    {
        # Ya publicado y con precio: solo se le rehace la estructura para
        # incorporar los 6 ejercicios y la guía que estaban solo en Disco.
        "name": "teoria-del-color",
        "title": "Teoría del color",
        "conservar_datos": True,
        "datos": "teoria_disco.json",
        "materiales": "teoria",
        "modulos": [
            (
                "👩🏻‍🎨 ¡Bienvenido artista!",
                [{"i": 0, "vimeo": "1211560985"}, {"i": 1}, {"i": 2, "vimeo": "1211560986"}, {"i": 3}],
            ),
            ("🌈 ¿Cómo funciona el color?", [{"i": 5, "vimeo": "1211560983"}, {"i": 6}]),
            (
                "🎨 El círculo cromático y las paletas de color",
                [{"i": 7, "vimeo": "1211560984"}, {"i": 8}, {"i": 9}],
            ),
            (
                "🖌 Crea sombras y luces realistas",
                [{"i": 10, "vimeo": "1211561163"}, {"i": 11}, {"i": 12, "vimeo": "1211561165"}, {"i": 13}],
            ),
            (
                "✨ Iguala tonos como un experto",
                [{"i": 14, "vimeo": "1211561566"}, {"i": 15, "vimeo": "1211561659"}, {"i": 16}],
            ),
            ("💛 Cierre con broche de oro", [{"i": 17, "vimeo": "1211561662"}]),
        ],
    },
    {
        "name": "curso-de-mascotas",
        "title": "Curso de Mascotas",
        "conservar_datos": True,
        "datos": "mascotas_disco.json",
        "materiales": "mascotas",
        "modulos": [
            ("🐾 ¡Bienvenid@ al curso de Mascotas!", [
                {"i": 0, "vimeo": "1210950170"},
                {"i": 1},
                {"i": 2}
            ]),
            ("🧅 Método por capas", [
                {"i": 4, "vimeo": "1210950171"}
            ]),
            ("✍🏼 Todo acerca de los pelitos", [
                {"i": 5, "vimeo": "1210950173"},
                {"i": 6, "vimeo": "1210950674"}
            ]),
            ("🎨 Colores vivos", [
                {"i": 7, "vimeo": "1210955092"},
                {"i": 8},
                {"i": 9, "vimeo": "1210955455"},
                {"i": 10}
            ]),
            ("🤩 Tips de realismo", [
                {"i": 11, "vimeo": "1210966469"}
            ]),
            ("🦁 Ejercicios de pelaje", [
                {"i": 12, "vimeo": "1210955541"},
                {"i": 13, "vimeo": "1210955664"},
                {"i": 14, "vimeo": "1210955711"},
                {"i": 15, "vimeo": "1210955751"},
                {"i": 16, "vimeo": "1210966571"}
            ]),
            ("✏️ Bocetaje", [
                {"i": 17, "vimeo": "1210956552"}
            ]),
            ("💪🏼 Proyecto Final", [
                {"i": 18, "vimeo": "1210956625"},
                {"i": 19},
                {"i": 20},
                {"i": 21, "vimeo": "1210956641"},
                {"i": 22, "vimeo": "1210956727"},
                {"i": 23, "vimeo": "1210956731"},
                {"i": 24, "vimeo": "1210957190"},
                {"i": 25, "vimeo": "1210957360"},
                {"i": 26, "vimeo": "1210957778"},
                {"i": 27}
            ]),
            ("🐩 Proyecto #1 (Perrito en funda)", [
                {"i": 28, "vimeo": "1215946355"},
                {"i": 29},
                {"i": 30, "vimeo": "1215946378"},
                {"i": 31, "vimeo": "1215946420"},
                {"i": 32, "vimeo": "1215946461"},
                {"i": 33, "vimeo": "1215946502"},
                {"i": 34, "vimeo": "1215946526"},
                {"i": 35, "vimeo": "1215946557"},
                {"i": 36}
            ]),
            ("🐈 Proyecto #2 (Gato en lienzo)", [
                {"i": 37, "vimeo": "1215946587"},
                {"i": 38},
                {"i": 39, "vimeo": "1215946618"},
                {"i": 40, "vimeo": "1215946646"},
                {"i": 41, "vimeo": "1215946682"},
                {"i": 42, "vimeo": "1215946804"},
                {"i": 43, "vimeo": "1215946947"},
                {"i": 44, "vimeo": "1215947141"},
                {"i": 45, "vimeo": "1215947290"},
                {"i": 46, "vimeo": "1215947526"},
                {"i": 47, "vimeo": "1215947639"},
                {"i": 48, "vimeo": "1215947768"},
                {"i": 49, "vimeo": "1215947873"},
                {"i": 50, "vimeo": "1215947986"},
                {"i": 51}
            ]),
        ],
    },
    {
        "name": "retrato-en-fundas",
        "title": "Retrato en fundas",
        "conservar_datos": True,
        "datos": "refu_disco.json",
        "materiales": "refu",
        "modulos": [
            ("🙌🏼 Introducción al proyecto", [{"i": 0, "vimeo": "1212761791"}, {"i": 1}, {"i": 2}]),
            (
                "🎨 Hora de dar color al proyecto",
                [
                    {"i": 4, "vimeo": "1212761980"},
                    {"i": 5, "vimeo": "1212760171"},
                    {"i": 6, "vimeo": "1212761130"},
                    {"i": 7, "vimeo": "1212760170"},
                    {"i": 8, "vimeo": "1212762171"},
                    {"i": 9, "vimeo": "1212760172"},
                    {"i": 10, "vimeo": "1212760173"},
                ],
            ),
            ("🎉 Cierre del proyecto: comparte tu arte", [{"i": 11}]),
        ],
    },
    {
        # El orden de Disco no coincide con el del LMS antiguo: el mapeo de
        # videos se verificó comparando duraciones, no títulos.
        "name": "proyecto-rocky",
        "title": "Proyecto Rocky",
        "conservar_datos": True,
        "datos": "rocky_disco.json",
        "materiales": "rocky",
        "modulos": [
            ("👩🏻‍🎨 Introducción al proyecto", [{"i": 0, "vimeo": "1211791441"}, {"i": 1}, {"i": 2}]),
            ("✏ Primero lo primero", [{"i": 4, "vimeo": "1211793151"}, {"i": 5, "vimeo": "1211793443"}]),
            (
                "🎨 Pintemos a Rocky capa por capa",
                [
                    {"i": 6, "vimeo": "1211792566"},
                    {"i": 7, "vimeo": "1211791297"},
                    {"i": 8, "vimeo": "1211791756"},
                    {"i": 9, "vimeo": "1211791296"},
                    {"i": 10, "vimeo": "1211791298"},
                ],
            ),
            ("🎊 Lo lograste: último paso del proyecto", [{"i": 11, "vimeo": "1211791299"}, {"i": 12}]),
        ],
    },
    {
        "name": "la-noche-estrellada",
        "title": "La Noche Estrellada",
        "conservar_datos": True,
        "datos": "noche_disco.json",
        "modulos": [
            (
                "✨ Introducción al proyecto",
                [
                    {"i": 0, "vimeo": "1212750289"},
                    {"i": 1, "vimeo": "1212750286"},
                    {"i": 2, "vimeo": "1212750288"},
                ],
            ),
            (
                '🌠 Empieza la magia: a pintar "La Noche Estrellada"',
                [
                    {"i": 4, "vimeo": "1212750287"},
                    {"i": 5, "vimeo": "1212750378"},
                    {"i": 6, "vimeo": "1212750402"},
                    {"i": 7, "vimeo": "1212750587"},
                    {"i": 8, "vimeo": "1212750769"},
                    {"i": 9, "vimeo": "1212750808"},
                    {"i": 10, "vimeo": "1212750966"},
                ],
            ),
            # Los dos videos de resina se reutilizan aquí: son los mismos que en
            # Arte en fundas, comprobado por duración (5 y 13 min).
            ("🫗 ¡Sella tu obra!", [{"i": 11, "vimeo": "1212758587"}, {"i": 12, "vimeo": "1212758609"}]),
            ("🖌️ ¡Lo lograste! Comparte tu resultado", [{"i": 13}]),
        ],
    },
    {
        "name": "el-angel-caido",
        "title": "El Ángel Caído",
        "conservar_datos": True,
        "datos": "angel_disco.json",
        "materiales": "angel",
        "modulos": [
            ("👼🏼 Introducción al proyecto", [{"i": 0, "vimeo": "1212755586"}, {"i": 1}]),
            (
                '🎨 ¡Manos a la obra con "El Ángel Caído"!',
                [
                    {"i": 3, "vimeo": "1212755589"},
                    {"i": 4, "vimeo": "1212755587"},
                    {"i": 5, "vimeo": "1212755676"},
                    {"i": 6, "vimeo": "1212755804"},
                    {"i": 7, "vimeo": "1212755983"},
                    {"i": 8, "vimeo": "1212757284"},
                    {"i": 9, "vimeo": "1212757822"},
                ],
            ),
            ("✨ Entrega final: comparte tu obra celestial", [{"i": 10, "vimeo": "1212755588"}, {"i": 11}]),
        ],
    },
    {
        "name": "workshop-videos-virales",
        "title": "Workshop: Videos virales",
        "conservar_datos": True,
        "datos": "virales_disco.json",
        "materiales": "virales",
        "modulos": [
            ("🤩 ¡Viraliza tu Arte!", [{"i": 0}, {"i": 1, "vimeo": "1212781788"}]),
            ("📸 Reto TanArtistic", [{"i": 2}]),
        ],
    },
    {
        "name": "workshop-el-valor-de-tu-obra",
        "title": "Workshop: El valor de tu obra",
        "conservar_datos": True,
        "datos": "valor_disco.json",
        "materiales": "valor",
        "modulos": [
            (
                "✨ Encuentra el valor de tu arte",
                [{"i": 0}, {"i": 1, "vimeo": "1212781993"}, {"i": 2, "vimeo": "1212781992"}],
            )
        ],
    },
    {
        "name": "workshop-perrito-pelo-corto",
        "title": "Workshop: Perrito pelo corto",
        "conservar_datos": True,
        "datos": "kira_disco.json",
        "materiales": "kira",
        "modulos": [
            ("✨ Prepárate para el workshop", [{"i": 0}, {"i": 1}, {"i": 2}]),
            (
                "🐶 Pintemos a un perrito en funda",
                [{"i": 4, "vimeo": "1212782292"}, {"i": 5, "vimeo": "1212782492"}],
            ),
        ],
    },
    {
        "name": "workshop-pelaje",
        "title": "Workshop Pelaje",
        "intro": "Aprende a pintar pelaje realista: capas, trazos, sombras y luces.",
        "descripcion": (
            "<p>La repetición completa del workshop en vivo de pelaje. Se trabaja el "
            "volumen y el detalle por capas, respetando sombras y luces, y la técnica "
            "de veladuras para unificar colores y suavizar contrastes.</p>"
        ),
        "portada": "workshop-pelaje.png",
        "modulos": [
            (
                "🐱 ¡Pintemos juntos un pelaje!",
                [{"titulo": "Repetición del Workshop en vivo", "tipo": "CLASE", "vimeo": "1215906996"}],
            )
        ],
    },
]


# --------------------------------------------------------------------------
# Construcción
# --------------------------------------------------------------------------


def bloque_vimeo(video_id: str) -> dict:
    return {
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


ANCHO_MAXIMO = 1600


def _optimizar(ruta: str) -> bytes:
    """Reduce las fotos que vienen directas de cámara (algunas de 13 MB)."""
    from io import BytesIO

    from PIL import Image

    img = Image.open(ruta)
    if img.mode in ("RGBA", "P", "LA"):
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        fondo.paste(img, mask=img.convert("RGBA").split()[-1])
        img = fondo
    elif img.mode != "RGB":
        img = img.convert("RGB")
    if img.width > ANCHO_MAXIMO:
        img = img.resize((ANCHO_MAXIMO, round(img.height * ANCHO_MAXIMO / img.width)), Image.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    return buffer.getvalue()


def subir(ruta: str, leccion: str) -> dict:
    nombre = os.path.basename(ruta)
    extension = nombre.rsplit(".", 1)[-1].lower()
    tipo = "PDF" if extension == "pdf" else extension
    existente = frappe.db.get_value("File", {"file_name": nombre, "attached_to_name": leccion}, "file_url")
    if existente:
        return {"file_url": existente, "file_type": tipo, "quizzes": []}

    if extension in ("jpg", "jpeg", "png", "webp") and os.path.getsize(ruta) > 1_500_000:
        contenido = base64.b64encode(_optimizar(ruta)).decode()
    else:
        with open(ruta, "rb") as fh:
            contenido = base64.b64encode(fh.read()).decode()
    doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": nombre,
            "content": contenido,
            "decode": True,
            "is_private": 1,
            "attached_to_doctype": "Course Lesson",
            "attached_to_name": leccion,
            "attached_to_field": "content",
        }
    ).insert(ignore_permissions=True)
    return {"file_url": doc.file_url, "file_type": tipo, "quizzes": []}


def asegurar_curso(cfg: dict) -> str:
    existe = frappe.db.exists("LMS Course", cfg["name"])
    if existe:
        curso = frappe.get_doc("LMS Course", cfg["name"])
    else:
        curso = frappe.new_doc("LMS Course")
        curso.name = cfg["name"]

    # Los cursos que ya estaban publicados traen su descripción, precio y
    # ajustes de membresía revisados: solo se les rehace la estructura.
    if not (existe and cfg.get("conservar_datos")):
        curso.update(
            {
                "title": cfg["title"],
                "short_introduction": cfg["intro"],
                "description": cfg["descripcion"],
                "published": 1,
                "taar_incluido_en_membresia": 1,
            }
        )
    # instructors es obligatorio, así que hay que ponerlo antes de insertar.
    if not curso.get("instructors") and frappe.db.exists("User", INSTRUCTOR):
        curso.append("instructors", {"instructor": INSTRUCTOR})

    if curso.is_new():
        curso.insert(ignore_permissions=True, set_name=cfg["name"])
    else:
        curso.save(ignore_permissions=True)
    return curso.name


def limpiar_estructura(curso: str, conservar: set):
    """Quita capítulos y lecciones que ya no están en la estructura nueva."""
    for l in frappe.get_all("Course Lesson", filters={"course": curso}, pluck="name"):
        if l in conservar:
            continue
        if frappe.db.count("LMS Course Progress", {"lesson": l}):
            print(f"  AVISO: {l} tiene progreso de alumnos, no se toca")
            continue
        for fila in frappe.get_all("Lesson Reference", filters={"lesson": l}, fields=["parent"]):
            cap = frappe.get_doc("Course Chapter", fila.parent)
            cap.set("lessons", [x for x in cap.lessons if x.lesson != l])
            cap.save(ignore_permissions=True)
        frappe.delete_doc("Course Lesson", l, ignore_permissions=True, force=True)
        print(f"  lección obsoleta {l} eliminada")

    for c in frappe.get_all("Course Chapter", filters={"course": curso}, pluck="name"):
        if c in conservar:
            continue
        if not frappe.get_all("Lesson Reference", filters={"parent": c}):
            doc = frappe.get_doc("LMS Course", curso)
            doc.set("chapters", [x for x in doc.chapters if x.chapter != c])
            doc.save(ignore_permissions=True)
            frappe.delete_doc("Course Chapter", c, ignore_permissions=True, force=True)
            print(f"  capítulo obsoleto {c} eliminado")


def construir(cfg: dict):
    print(f"\n=== {cfg['title']}")
    curso = asegurar_curso(cfg)

    origen = {}
    if cfg.get("datos"):
        with open(os.path.join(BASE, cfg["datos"]), encoding="utf-8") as fh:
            crudo = json.load(fh)
        lista = crudo["lecciones"] if isinstance(crudo, dict) else crudo
        origen = {x["i"]: x for x in lista}

    archivos = {}
    imagenes = {}
    if cfg.get("materiales"):
        ruta = os.path.join(MATERIALES, cfg["materiales"], "mapa.json")
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as fh:
                archivos = json.load(fh)
        # Las imágenes incrustadas en el texto van aparte de los adjuntos.
        ruta_img = os.path.join(MATERIALES, cfg["materiales"], "img", "mapa.json")
        if os.path.exists(ruta_img):
            with open(ruta_img, encoding="utf-8") as fh:
                imagenes = json.load(fh)

    # Los capítulos se acumulan y se escriben al final: guardar el curso dentro
    # del bucle choca con las escrituras de capítulos y lecciones, que también
    # tocan el documento (TimestampMismatchError).
    capitulos = []
    vigentes = set()

    for m_idx, (titulo_modulo, lecciones) in enumerate(cfg["modulos"], start=1):
        cap_name = f"{cfg['name']}-m{m_idx}"
        if frappe.db.exists("Course Chapter", cap_name):
            capitulo = frappe.get_doc("Course Chapter", cap_name)
            capitulo.title = titulo_modulo
        else:
            capitulo = frappe.new_doc("Course Chapter")
            capitulo.update({"title": titulo_modulo, "course": curso})
        capitulo.set("lessons", [])
        if capitulo.is_new():
            capitulo.insert(ignore_permissions=True, set_name=cap_name)
        else:
            capitulo.save(ignore_permissions=True)
        vigentes.add(cap_name)

        for l_idx, definicion in enumerate(lecciones, start=1):
            datos = origen.get(definicion.get("i"), {})
            titulo = definicion.get("titulo") or datos.get("titulo") or "Sin título"
            tipo = definicion.get("tipo") or datos.get("tipo") or "CLASE"

            bloques = []
            if definicion.get("vimeo"):
                bloques.append(bloque_vimeo(definicion["vimeo"]))

            if datos.get("bloques"):
                bloques += normalizar(datos["bloques"])
            elif datos.get("html"):
                bloques += html_a_bloques(datos["html"])

            lec_name = f"{cfg['name']}-{m_idx}-{l_idx}"
            # Cada "imagen_pendiente" del texto se cambia por su archivo, en el
            # mismo orden en que aparecían en Disco.
            pendientes = list(imagenes.get(str(definicion.get("i")), []))
            resueltos = []
            for bloque in bloques:
                if bloque.get("type") != "imagen_pendiente":
                    resueltos.append(bloque)
                    continue
                if not pendientes:
                    print(f"  AVISO: {lec_name} tiene una imagen sin archivo, se omite")
                    continue
                ruta_img = os.path.join(MATERIALES, cfg["materiales"], "img", pendientes.pop(0))
                if os.path.exists(ruta_img):
                    resueltos.append({"type": "upload", "data": subir(ruta_img, lec_name)})
            bloques = resueltos
            if frappe.db.exists("Course Lesson", lec_name):
                leccion = frappe.get_doc("Course Lesson", lec_name)
            else:
                leccion = frappe.new_doc("Course Lesson")

            # Una lección puede llevar varios adjuntos (p. ej. dos imágenes de
            # referencia), así que el mapa admite tanto un nombre como una lista.
            archivo = archivos.get(str(definicion.get("i")))
            lista_archivos = archivo if isinstance(archivo, list) else ([archivo] if archivo else [])
            # El content arranca con "blocks" vacío, no con "{}": el hook
            # save_lesson_details_in_quiz itera content["blocks"] al guardar y
            # revienta con None si la clave no está.
            leccion.update(
                {"title": titulo, "chapter": cap_name, "course": curso, "content": '{"blocks": []}'}
            )
            if leccion.is_new():
                leccion.insert(ignore_permissions=True, set_name=lec_name)
            else:
                leccion.save(ignore_permissions=True)
            vigentes.add(lec_name)

            # Los adjuntos van arriba, como en Disco, y en su orden original.
            for pos, nombre_archivo in enumerate(lista_archivos):
                ruta = os.path.join(MATERIALES, cfg["materiales"], nombre_archivo)
                if os.path.exists(ruta):
                    bloques.insert(pos, {"type": "upload", "data": subir(ruta, lec_name)})
                else:
                    print(f"  AVISO: falta {nombre_archivo}")

            if tipo in CONSIGNAS:
                existente = frappe.db.get_value("LMS Assignment", {"course": curso, "title": titulo}, "name")
                campos = {"title": titulo, "type": "Image or PDF", "question": CONSIGNAS[tipo], "course": curso}
                if existente:
                    asg = frappe.get_doc("LMS Assignment", existente)
                    asg.update(campos)
                    asg.save(ignore_permissions=True)
                else:
                    asg = frappe.get_doc({"doctype": "LMS Assignment", **campos}).insert(ignore_permissions=True)
                bloques.append({"type": "assignment", "data": {"assignment": asg.name}})

            for pos, b in enumerate(bloques):
                b.setdefault("id", f"{lec_name.replace('-', '')}b{pos}")
            leccion.content = json.dumps({"blocks": bloques}, ensure_ascii=False)
            leccion.save(ignore_permissions=True)

            capitulo.append("lessons", {"lesson": lec_name})
            resumen = ", ".join(sorted({b["type"] for b in bloques})) or "vacía"
            print(f"  {lec_name:<22} [{tipo:<9}] {titulo[:38]:<38} -> {resumen}")

        capitulo.save(ignore_permissions=True)
        capitulos.append(cap_name)

    doc_curso = frappe.get_doc("LMS Course", curso)
    doc_curso.set("chapters", [{"chapter": c} for c in capitulos])
    doc_curso.save(ignore_permissions=True)
    limpiar_estructura(curso, vigentes)

    if cfg.get("portada"):
        ruta = os.path.join(MATERIALES, "portadas", cfg["portada"])
        if os.path.exists(ruta) and not frappe.db.get_value("LMS Course", curso, "image"):
            print(f"  (portada pendiente: usa aplicar_portadas.py para {cfg['portada']})")


for cfg in CURSOS:
    construir(cfg)

frappe.db.commit()
print("\nListo.")
