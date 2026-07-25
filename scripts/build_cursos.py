import frappe
import json


def bloque_video(vid):
	return {
		"id": "v" + vid,
		"type": "embed",
		"data": {
			"service": "vimeo",
			"source": "https://vimeo.com/" + vid,
			"embed": "https://player.vimeo.com/video/" + vid,
			"width": 580,
			"height": 320,
			"caption": "",
		},
	}


def bloque_parrafo(uid, texto):
	return {"id": uid, "type": "paragraph", "data": {"text": texto}}


def contenido(vid, parrafos=None, uid="x"):
	blocks = [bloque_video(vid)]
	for i, p in enumerate(parrafos or []):
		blocks.append(bloque_parrafo(uid + str(i), p))
	return json.dumps({"time": 1784950000000, "blocks": blocks, "version": "2.29.0"}, ensure_ascii=False)


CURSOS = [
	{
		"titulo": "El Ángel Caído",
		"intro": "Recrea la mirada más famosa del arte clásico: pintaremos El Ángel Caído paso a paso, desde el fondo hasta cada mechón.",
		"desc": "<p>Recrea la mirada más famosa del arte clásico: pintaremos <b>El Ángel Caído</b> paso a paso, desde el fondo hasta cada mechón.</p><p>Partimos de las guías y el fondo, construimos el rostro y los ojos con calma, y cerramos con el brazo y el pelo. Un proyecto para perderle el miedo a las obras maestras.</p>",
		"publicado": 1, "incluido": 1, "venta": 0,
		"secciones": [
			{"t": "👋 Bienvenida", "lecciones": [
				{"t": "Introducción y materiales", "v": "1212755586", "preview": 1, "p": ["¡Bienvenid@ a este proyecto! Aquí te cuento qué vamos a pintar y todo lo que necesitas para empezar."]},
				{"t": "Guías", "v": "1212755589", "p": ["Ten a la mano tus guías impresas antes de arrancar: nos van a acompañar durante todo el proyecto."]},
			]},
			{"t": "🎨 Proceso", "lecciones": [
				{"t": "Fondo", "v": "1212755587"},
				{"t": "Rostro (parte 1)", "v": "1212755676"},
				{"t": "Rostro (parte 2)", "v": "1212755804"},
				{"t": "Ojos", "v": "1212755983"},
				{"t": "Brazo (parte 1)", "v": "1212757284"},
				{"t": "Pelo", "v": "1212757822"},
			]},
			{"t": "🏁 Cierre", "lecciones": [
				{"t": "Palabras finales", "v": "1212755588", "p": ["¡Lo lograste! Comparte tu Ángel Caído con la comunidad: nos encanta ver tu versión."]},
			]},
		],
	},
	{
		"titulo": "La Noche Estrellada",
		"intro": "Pinta tu propia versión de la obra más famosa de Van Gogh y domina sus trazos llenos de movimiento.",
		"desc": "<p>Pinta tu propia versión de <b>La Noche Estrellada</b> y domina los trazos llenos de movimiento que hicieron único a Van Gogh.</p><p>Empezamos con un poco de historia y composición, preparamos el boceto y los colores guía, y pintamos por partes: cielo, montañas, campo y ciprés.</p>",
		"publicado": 1, "incluido": 1, "venta": 0,
		"secciones": [
			{"t": "👋 Bienvenida", "lecciones": [
				{"t": "Introducción y materiales", "v": "1212750289", "preview": 1, "p": ["¡Bienvenid@! Este proyecto es un clásico de la escuela: aquí te cuento qué necesitas para empezar."]},
				{"t": "Un poco de historia", "v": "1212750286"},
			]},
			{"t": "✏️ Preparación", "lecciones": [
				{"t": "Composición", "v": "1212750288"},
				{"t": "Boceto", "v": "1212750287"},
				{"t": "Colores guía", "v": "1212750378"},
			]},
			{"t": "🎨 Pintando", "lecciones": [
				{"t": "Plastas", "v": "1212750402"},
				{"t": "Ejercicio de trazos", "v": "1212750587"},
				{"t": "Cielo", "v": "1212750769"},
				{"t": "Montañas", "v": "1212750808"},
				{"t": "Campo y ciprés", "v": "1212750966"},
			]},
		],
	},
	{
		"titulo": "Proyecto Rocky",
		"intro": "Un retrato peludo de principio a fin: pinta a Rocky y aprende el proceso completo de un retrato de mascota.",
		"desc": "<p>Un retrato peludo de principio a fin: pinta a <b>Rocky</b> y aprende el proceso completo de un retrato de mascota.</p><p>Repasamos los fundamentos (preparar el lienzo y transferir tu imagen), montamos el fondo y el color base, y construimos sombras, ojos, nariz y pelitos en sombra y en luz.</p>",
		"publicado": 1, "incluido": 1, "venta": 0,
		"secciones": [
			{"t": "👋 Bienvenida", "lecciones": [
				{"t": "Introducción y materiales", "v": "1211791441", "preview": 1, "p": ["¡Bienvenid@ al Proyecto Rocky! Aquí te cuento qué vamos a pintar y con qué materiales."]},
			]},
			{"t": "🧱 Fundamentos", "lecciones": [
				{"t": "Prepara tu lienzo", "v": "1211793151"},
				{"t": "Transfiere tus imágenes", "v": "1211793443"},
			]},
			{"t": "🎨 Proceso", "lecciones": [
				{"t": "Fondo y color base", "v": "1211792566"},
				{"t": "Sombras y detalles", "v": "1211791296"},
				{"t": "Ojos y nariz", "v": "1211791298"},
				{"t": "Pelitos en sombra", "v": "1211791297"},
				{"t": "Pelitos en luz", "v": "1211791756"},
			]},
			{"t": "🏁 Cierre", "lecciones": [
				{"t": "Palabras finales", "v": "1211791299", "p": ["¡Rocky quedó listo! Comparte tu retrato con la comunidad y presume esos pelitos."]},
			]},
		],
	},
	{
		"titulo": "Resina en fundas",
		"intro": "Dale acabado profesional a tus fundas pintadas: aprende a resinar paso a paso.",
		"desc": "<p>Dale acabado profesional a tus fundas pintadas: aprende a <b>resinar</b> paso a paso.</p><p>Un proyecto corto y directo: los materiales que necesitas y el proceso completo para un terminado brillante, protegido y duradero.</p>",
		"publicado": 1, "incluido": 1, "venta": 0,
		"secciones": [
			{"t": "💎 Proyecto", "lecciones": [
				{"t": "Introducción y materiales", "v": "1212758587", "preview": 1, "p": ["Todo lo que necesitas para resinar tu funda con un acabado profesional."]},
				{"t": "Proceso de resinado", "v": "1212758609"},
			]},
		],
	},
	{
		"titulo": "Retrato en fundas",
		"intro": "Convierte una funda de celular en un retrato en miniatura: rostro, cabello y detalles paso a paso.",
		"desc": "<p>Convierte una funda de celular en un <b>retrato en miniatura</b>: rostro, cabello y detalles paso a paso.</p><p>Con tus guías listas, montamos el color base y los tonos de sombra, sumamos luz y rubor, y rematamos con ojos, boca, saco y cabello. Un proyecto pequeño con resultado enorme.</p>",
		"publicado": 1, "incluido": 1, "venta": 0,
		"secciones": [
			{"t": "👋 Bienvenida", "lecciones": [
				{"t": "Introducción y materiales", "v": "1212761791", "preview": 1, "p": ["¡Bienvenid@! Aquí te cuento qué vamos a crear y todos los materiales para lograrlo."]},
				{"t": "Guías", "v": "1212761980", "p": ["Prepara tus guías: son la base para que las proporciones del retrato queden perfectas."]},
			]},
			{"t": "🎨 Proceso", "lecciones": [
				{"t": "Color base y tonos de sombra", "v": "1212760171"},
				{"t": "Tonos de luz y rubor", "v": "1212761130"},
				{"t": "Ojos, cejas y pestañas", "v": "1212760170"},
				{"t": "Boca", "v": "1212762171"},
				{"t": "Saco", "v": "1212760172"},
				{"t": "Cabello y últimos detalles", "v": "1212760173"},
			]},
		],
	},
	{
		"titulo": "Teoría del color",
		"intro": "El curso que cambia tu forma de mezclar: matiz, saturación y valor, y cómo igualar cualquier color que veas.",
		"desc": "<p>El curso que cambia tu forma de mezclar: <b>matiz, saturación y valor</b>, el círculo cromático y cómo igualar cualquier color que veas.</p><p>Primero entendemos la teoría con ejercicios claros y después la llevamos a la pintura: aplicación real en tus obras y práctica de igualar colores hasta que te salga natural.</p>",
		"publicado": 0, "incluido": 0, "venta": 1,
		"secciones": [
			{"t": "👋 Bienvenida", "lecciones": [
				{"t": "Introducción", "v": "1211560985", "preview": 1, "p": ["¡Bienvenid@! Este curso te va a acompañar en todos tus proyectos: la teoría del color bien explicada y aplicada."]},
				{"t": "Imprime la guía", "v": "1211560986", "p": ["Imprime tu guía antes de continuar: vamos a trabajar sobre ella durante todo el curso."]},
			]},
			{"t": "🌈 Fundamentos", "lecciones": [
				{"t": "Matiz, saturación y valor", "v": "1211560983"},
				{"t": "Círculo cromático", "v": "1211560984"},
			]},
			{"t": "🎨 Aplicación", "lecciones": [
				{"t": "Aplicación en pintura (parte 1)", "v": "1211561163"},
				{"t": "Aplicación en pintura (parte 2)", "v": "1211561165"},
				{"t": "Igualar colores (parte 1)", "v": "1211561566"},
				{"t": "Igualar colores (parte 2)", "v": "1211561659"},
			]},
			{"t": "🏁 Cierre", "lecciones": [
				{"t": "Palabras finales", "v": "1211561662", "p": ["¡Felicidades! Ahora el color juega de tu lado. Vuelve a esta guía cada vez que un proyecto te rete."]},
			]},
		],
	},
	{
		"titulo": "Workshop: Perrito pelo corto",
		"intro": "Workshop grabado: un retrato de perrito de pelo corto, en vivo y sin ediciones, en dos sesiones.",
		"desc": "<p>Workshop grabado: un <b>retrato de perrito de pelo corto</b> de principio a fin, tal como se pintó en vivo.</p><p>Dos sesiones completas para acompañar cada decisión del proceso: colores, formas y esos acabados que hacen la diferencia en el pelo corto.</p>",
		"publicado": 1, "incluido": 1, "venta": 0,
		"secciones": [
			{"t": "🎨 Workshop", "lecciones": [
				{"t": "Parte 1", "v": "1212782292", "preview": 1},
				{"t": "Parte 2", "v": "1212782492"},
			]},
		],
	},
	{
		"titulo": "Workshop: El valor de tu obra",
		"intro": "Workshop grabado: aprende a ponerle precio a tu arte sin malbaratarlo.",
		"desc": "<p>Workshop grabado: aprende a ponerle <b>precio a tu arte</b> sin malbaratarlo.</p><p>Cómo calcular tus costos, valorar tu tiempo y comunicar el precio con seguridad: todo lo que necesitas para cobrar lo justo por tu trabajo.</p>",
		"publicado": 1, "incluido": 1, "venta": 0,
		"secciones": [
			{"t": "💰 Workshop", "lecciones": [
				{"t": "Parte 1", "v": "1212781993", "preview": 1},
				{"t": "Parte 2", "v": "1212781992"},
			]},
		],
	},
	{
		"titulo": "Workshop: Videos virales",
		"intro": "Workshop grabado: cómo crear videos de tu proceso que conecten y se compartan.",
		"desc": "<p>Workshop grabado: cómo crear <b>videos de tu proceso</b> que conecten y se compartan.</p><p>Qué grabar, cómo editarlo y qué hace que un video de arte funcione en redes: la fórmula aplicada con ejemplos reales.</p>",
		"publicado": 1, "incluido": 1, "venta": 0,
		"secciones": [
			{"t": "📱 Workshop", "lecciones": [
				{"t": "Sesión completa", "v": "1212781788", "preview": 1},
			]},
		],
	},
]


mascotas = frappe.get_doc("LMS Course", "curso-de-mascotas")
instructores = [i.instructor for i in (mascotas.instructors or [])]

creados = []
for cdef in CURSOS:
	# Re-ejecutable: si el curso ya existe (de una corrida anterior), se
	# reconstruye desde cero. Ninguno tiene inscripciones todavía.
	existente = frappe.db.get_value("LMS Course", {"title": cdef["titulo"]}, "name")
	if existente:
		for nombre in frappe.get_all("Course Lesson", filters={"course": existente}, pluck="name"):
			frappe.delete_doc("Course Lesson", nombre, force=True, ignore_permissions=True)
		for nombre in frappe.get_all("Course Chapter", filters={"course": existente}, pluck="name"):
			frappe.delete_doc("Course Chapter", nombre, force=True, ignore_permissions=True)
		frappe.delete_doc("LMS Course", existente, force=True, ignore_permissions=True)

	curso = frappe.new_doc("LMS Course")
	curso.title = cdef["titulo"]
	curso.short_introduction = cdef["intro"]
	curso.description = cdef["desc"]
	curso.published = cdef["publicado"]
	curso.paid_course = 0
	curso.taar_incluido_en_membresia = cdef["incluido"]
	curso.taar_venta_individual = cdef["venta"]
	for ins in instructores:
		curso.append("instructors", {"instructor": ins})
	curso.insert(ignore_permissions=True)

	nombres_capitulos = []
	for sec in cdef["secciones"]:
		ch = frappe.new_doc("Course Chapter")
		ch.course = curso.name
		ch.title = sec["t"]
		ch.insert(ignore_permissions=True)
		nombres_capitulos.append(ch.name)
		nombres_lecciones = []
		for lec in sec["lecciones"]:
			l = frappe.new_doc("Course Lesson")
			l.course = curso.name
			l.chapter = ch.name
			l.title = lec["t"]
			l.include_in_preview = lec.get("preview", 0)
			l.content = contenido(lec["v"], lec.get("p"), uid=lec["v"] + "p")
			l.insert(ignore_permissions=True)
			nombres_lecciones.append(l.name)
		# Insertar lecciones actualiza el capítulo por hooks: recargar antes
		# de colgar las referencias para no chocar timestamps.
		ch_fresco = frappe.get_doc("Course Chapter", ch.name)
		for nombre in nombres_lecciones:
			ch_fresco.append("lessons", {"lesson": nombre})
		ch_fresco.save(ignore_permissions=True)

	curso_fresco = frappe.get_doc("LMS Course", curso.name)
	for nombre in nombres_capitulos:
		curso_fresco.append("chapters", {"chapter": nombre})
	curso_fresco.save(ignore_permissions=True)
	creados.append(curso.name)

frappe.db.commit()
print("CURSOS_CREADOS:" + json.dumps(creados, ensure_ascii=False))
