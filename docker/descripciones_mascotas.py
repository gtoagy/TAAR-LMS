# -*- coding: utf-8 -*-
"""Copia las descripciones reales de Disco a las lecciones del Curso de Mascotas.

Reconstruye el contenido de cada lección: video de Vimeo (si tiene) +
descripción con formato (encabezados, párrafos, listas).
Ejecutar: env/bin/python /workspace/descripciones_mascotas.py
"""

import json

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

VIDEOS = {
    "mascotas-1-1": "1210950170",
    "mascotas-2-1": "1210950171",
    "mascotas-3-1": "1210950173",
    "mascotas-3-2": "1210950674",
    "mascotas-4-1": "1210955092",
    "mascotas-4-3": "1210955455",
    "mascotas-5-1": "1210966469",
    "mascotas-6-1": "1210955541",
    "mascotas-6-2": "1210955664",
    "mascotas-6-3": "1210955711",
    "mascotas-6-4": "1210955751",
    "mascotas-6-5": "1210966571",
    "mascotas-7-1": "1210956552",
    "mascotas-8-1": "1210956625",
    "mascotas-8-4": "1210956641",
    "mascotas-8-5": "1210956727",
    "mascotas-8-6": "1210956731",
    "mascotas-8-7": "1210957190",
    "mascotas-8-8": "1210957360",
    "mascotas-8-9": "1210957778",
    "mascotas-8-10": "1210957869",
}

# (tag, texto) por lección, copiado de tanartistic.disco.co
DESC = {
    "mascotas-1-1": [
        ("h3", "¡Artista! Bienvenido a este curso renovado de mascotas.🐾"),
        ("p", "Estoy súper emocionada de tenerte por aquí y poderte enseñar todos mis métodos y secretos para crear a los peluditos que tanto amamos. Recuerda que no estás solo en este camino, puedes ir haciendo preguntas en el proceso a través de los canales de retroalimentación o por el grupo de WhatsApp, la comunidad estará feliz de ayudarte."),
        ("p", "¡A pintar peluditos se ha dicho! 🐶🐱"),
    ],
    "mascotas-1-2": [
        ("h2", "✨ ¡Prepara tus materiales porque ya vamos a empezar!"),
        ("p", "Dependiendo de la sección en la que te encuentres serán los materiales que utilizaremos. No te preocupes, todo es muy fácil de conseguir en una tienda de arte."),
        ("h3", "✏ Ejercicios de bocetaje:"),
        ("li", "Lápiz"),
        ("li", "Papel"),
        ("li", "Ipad/Tableta (Opcional)"),
        ("h3", "🎨 Ejercicios de pintura:"),
        ("li", "Pincel de punta redonda, recomiendo del #4 o #6 para crear los detalles del pelaje"),
        ("li", "Pincel de abanico"),
        ("li", "Pincel delineador #0"),
        ("li", "Pincel viejo/usado"),
        ("li", "Pinturas acrílicas de cualquier marca: Rojo, amarillo, azul, blanco y negro"),
        ("h3", "🐩 Proyecto #1:"),
        ("li", "Funda de celular o papel de algodón de 300gr para pintura."),
        ("li", "Pincel de punta redonda, recomiendo del #4 o alguno de tu preferencia para pintar en superficies pequeñas."),
        ("li", "Pinturas acrílicas: Rojo, amarillo, azul, sombra café, azul cobalto, blanco y negro."),
        ("h3", "🐈 Proyecto #2:"),
        ("li", "Pinturas acrílicas: Blanco, negro, sombra café, amarillo, naranja, rojo, azul cobalto"),
        ("li", "Pinceles redondos: núm. 4, 8 y 12"),
        ("li", "Pincel plano mediano"),
        ("li", "Brocha"),
        ("li", "Pincel viejo con cerdas abiertas (opcional, pero útil)"),
        ("li", "Gesso (opcional para darle un mejor acabado a tu obra)"),
        ("li", "Barniz mate para acrílico (pero el acabado final)"),
        ("li", "Lápiz y goma"),
        ("li", "Lienzo de la medida de tu prefrencia"),
        ("li", "Godete"),
        ("li", "Trapito o servilleta"),
        ("li", "Agua"),
    ],
    "mascotas-1-3": [
        ("p", "¡Haz click en el archivo para descargarlo! 👆🏼"),
        ("p", "Con cada módulo nuevo que subamos al curso, iremos actualizando el Workbook con sus ejercicios correspondientes. ¡Mantente atent@ a las actualizaciones! 🐾"),
        ("p", "Te recomiendo imprimir este Workbook en un papel grueso tipo Fabriano de 300gr o cualquier papel similar para pintura acrílica. Te dejo aquí abajito una lección de como puedes imprimir tu Workbook."),
        ("p", "Cualquier duda, puedes hacer una pregunta en el canal del curso o través del grupo de WhatsApp."),
        ("p", "📎 CLASE: ¿Cómo imprimir la guía?"),
    ],
    "mascotas-1-4": [
        ("p", "¿Cuál es tu número de WhatsApp? (En caso que necesitemos comunicarnos contigo) Incluye tu código de país ej. +52 998 222 111"),
    ],
    "mascotas-2-1": [
        ("p", "En este video, se explica cómo pintar la textura peluda en mascotas, centrándose en la creación de volumen y realismo. Se muestra cómo lograr que los pelitos parezcan crecer desde la raíz, con cambios de tono que van desde la base oscura hasta las puntas iluminadas. Se simplifica el proceso dividiéndolo en capas: tono base, tonos sombra, tonos luz y detalles, permitiendo construir profundidad y volumen gradualmente. Al enfocarse en una capa a la vez, se compara el proceso con armar un rompecabezas para lograr una obra de arte realista y detallada."),
    ],
    "mascotas-3-1": [
        ("p", "En este video, se aborda la importancia de perfeccionar los trazos al pintar pelitos en mascotas para lograr un acabado realista y natural. Se identifican errores comunes como la longitud, grosor, dirección y orden de los pelitos, y se proporcionan técnicas para corregirlos, como trabajar con trazos fluidos y variar la dirección de los pelitos. Se muestra cómo pintar pelitos cortos y rizados, unificando secciones y aplicando capas para crear textura y volumen. Se incluyen ejercicios prácticos para mejorar la técnica de pintura de pelitos en mascotas."),
    ],
    "mascotas-3-2": [
        ("h3", "¡Vayamos con el primer ejercicio! 👩🏻‍🎨"),
        ("p", "Dominar el movimiento de la muñeca, la sensibilidad del pincel y la fluidez del trazo serán habilidades esenciales para crear pelitos realistas. ¡Asi que no te detengas con este ejercicio y haz muchos muchos pelitos más!"),
    ],
    "mascotas-4-1": [
        ("p", "En este video se destaca la importancia del color en la pintura de mascotas para lograr realismo y matices. Se enfatiza en la observación detallada de los tonos cálidos y fríos, la saturación de los colores, y las diferencias entre sombras y luces. Se introduce el uso del gotero digital para identificar y mezclar colores de manera precisa, resaltando cómo la iluminación y el entorno influyen en la percepción de los colores. A través de ejercicios prácticos, se demuestra cómo analizar y aplicar correctamente los colores para obtener resultados realistas en las pinturas de mascotas."),
    ],
    "mascotas-4-2": [
        ("h2", "¡Es momento de poner a prueba ese ojo de artista! 👁🎨"),
        ("p", "En este pequeño Quizz te encontrarás preguntas relacionadas al color y diferentes tonalidades en las mascotas. Entender lo que estamos viendo es crucial para pintar mascotas realistas."),
        ("p", "¡Haz click aquí para hacerlo!"),
    ],
    "mascotas-4-3": [
        ("h2", "¡Hora de mezclar! 🎨"),
        ("p", "Aquí te enseñaré a súper detalle mi proceso paso a paso para llegar a los tonos correctos de los peluditos."),
        ("p", "Recuerda... Al momento de ver nuestra imagen de referencia algo que te ayudará muchísimo en el proceso es identificar el tono base, tono sombra y tono luz de cada área del pelaje. De esta manera nos estamos concentrando en desglosar las capas y llegar a los tonos reales y no a los que creemos que vemos. ¡El ojo nos puede engañar! Por eso siempre nos apoyamos de la herramienta del cuentagotas para saber exactamente que color replicar."),
        ("p", "¡Descarga e imprime las nuevas hojas del Workbook para hacer tu ejercicio!"),
        ("p", "📎 GUIA: Descarga e imprime el Workbook"),
        ("h3", "¡Sube tu ejercicio aquí abajo! 👇🏼"),
    ],
    "mascotas-4-4": [
        ("h2", "¡Te toca a ti encontrar los colores a utilizar! 👩🏻‍🔬"),
        ("p", "En la hoja número 6 del Workbook encontrarás la imagen de este gatito."),
        ("p", "Debes realizar lo siguiente"),
        ("li", "Identifica el tono base, tono sombra y tono luz a utilizar y márcalos en la imagen."),
        ("li", "Crea los respectivos tonos."),
        ("li", "¡Sube tu ejercicio!"),
        ("p", "BONUS"),
        ("p", "¡Comparte tu resultado en el post de la comunidad \"Reto: Creando colores con vida\". Ahí les compartiré retroalimentación de su ejercicio!"),
    ],
    "mascotas-5-1": [
        ("p", "En este video, se presentan consejos clave para mejorar la calidad y realismo de las pinturas de mascotas. Se destaca la importancia del bajo contraste y el desenfoque para crear texturas realistas sin exagerar en los detalles. Se aborda la técnica de difuminar los bordes para integrar de manera suave elementos como los ojos y la nariz, evitando que parezcan sobrepuestos. Además, se resalta la importancia de añadir detalles precisos en áreas focales para dar vida a las pinturas. Estos consejos, al ser aplicados con equilibrio, pueden elevar la calidad y realismo de las obras artísticas."),
    ],
    "mascotas-6-1": [
        ("p", "En este video, se prepara a los espectadores para pintar pelaje de perritos, repasando conceptos como capas, trazos, colores realistas y tips de realismo. Se enfatiza la importancia de practicar distintos colores, texturas y largos de pelitos para familiarizarse con el proceso. Se presentan preguntas clave a considerar antes de comenzar a pintar, como identificar las capas, elegir los colores adecuados y determinar el tipo de pelitos a representar. Se detallan los materiales necesarios, incluyendo pinturas primarias, pinceles específicos y el uso de un workbook para el ejercicio."),
    ],
    "mascotas-6-2": [
        ("p", "En este video tutorial se explica detalladamente cómo pintar el pelaje de un perro paso a paso, haciendo hincapié en la textura y los colores necesarios para lograr un aspecto realista. Se aborda la selección de áreas clave, la aplicación de capas con diferentes tonos y la mezcla de colores para crear variaciones tonales. Se enseña a utilizar pinceles específicos para lograr la textura peluda gradualmente, destacando la importancia de la observación detallada y la práctica para alcanzar realismo en la pintura del pelaje."),
    ],
    "mascotas-6-3": [
        ("p", "En este video se enseña cómo crear texturas realistas en animales utilizando diferentes pinceles y técnicas de pintura. Se aborda la importancia de ajustar tonos y contrastes, experimentar con la dilución de la pintura y probar distintos tipos de pinceles. Se detalla la aplicación de trazos para simular pelaje, prestando atención a la dirección y variación de los mismos, así como la progresión en capas para lograr un efecto realista. Además, se destaca la relevancia de los detalles para lograr una representación fiel del pelaje de una mascota."),
    ],
    "mascotas-6-4": [
        ("p", "En este video tutorial, se presentan técnicas detalladas para pintar el pelaje de un perro blanco con realismo, abordando la variación de colores, texturas, tonos, sombras y luces. Se explican métodos para crear la textura del pelaje mediante la formación de mechones y secciones de pelo, así como la aplicación de colores base, sombras y luces. Además, se enseña a pintar sombras de manera cohesiva, añadir tonos de luz y capas de detalle para dar volumen y realismo al pelaje, manteniendo su personalidad y movimiento. Se destaca la importancia de la saturación de colores para un resultado final realista y se guía en la creación de un pelaje ondulado."),
    ],
    "mascotas-6-5": [
        ("p", "En este video, se enseña cómo pintar pelaje detallado y rizado, destacando la importancia de los tonos base y la mezcla de colores para lograr realismo. Se explica cómo añadir capas de tonos claros para dar profundidad y contraste, así como la técnica para pintar mechones de pelo con volumen y textura. Se brindan consejos para evitar la definición excesiva de los mechones y lograr un aspecto natural. Además, se muestra cómo agregar detalles finales para completar el efecto de profundidad en el pelaje."),
    ],
    "mascotas-7-1": [
        ("p", "En este video, aprenderás a bocetar y dibujar a tus mascotas utilizando figuras básicas y simplificando formas. Comenzaremos con el boceto de un perrito, enfocándonos en el hocico y conectando los detalles del rostro para lograr proporciones correctas. La habilidad de bocetar sin calcar es esencial para mejorar tu observación y corregir errores en el dibujo. También discutiremos los materiales necesarios y ejercicios adicionales para mejorar tus habilidades de bocetaje. ¡Prepárate para dar vida a tu peludito en el papel paso a paso!"),
    ],
    "mascotas-8-1": [],
    "mascotas-8-2": [
        ("p", "Muy bien Artista, hora de reunir o salir a comprar tus materiales!!"),
        ("p", "Como en todos los proyectos, intento que los materiales que usemos sean sencillos de conseguir. Yo te compartiré las marcas que utilizo pero si estás en otro país o te gustaría utilizar otras, está más que perfectoooo. ✨"),
        ("p", "Lo que sí te recomiendo es que las pinturas que elijas, pigmenten super bien y que los pinceles tengan excelente puntita."),
        ("p", "Aquí te va:"),
        ("li", "Pinturas aćrilicas: Rojo, Amarillo, Azul cobalto, Blanco, Negro. (yo utilicé pinturas Politec)"),
        ("li", "Pinceles: Redondo no. 4, 5 o 6, Pincel despeinado (opcional, y es literal uno viejo jeje no vayas a llegar a la tienda preguntando por el😅), Pincel plano (para el fondo así que te recomiendo que esté mas grande). Yo utilicé marca White Elite Taklon de Pinto."),
        ("li", "Gesso y lija: para preparar tu lienzo (gesso marca Atl)"),
        ("li", "Godete"),
        ("li", "Papel y agua para limpiar tus pinceles"),
        ("li", "Lienzo: 20 x25 cm"),
        ("p", "¡Y eso es todo! Al finalizar puedes también barnizar tu obra :)"),
        ("p", "Si tienes alguna duda de algún material escríbenos para ayudarte. 👍🏼"),
    ],
    "mascotas-8-3": [
        ("p", "¡Descarga la imagen para imprimirla haciendo click en el archivo! 👇🏼"),
    ],
    "mascotas-8-4": [
        ("p", "Resultado de la capa \"Tono base\""),
    ],
    "mascotas-8-5": [
        ("p", "¡Resultado de los tonos sombra!"),
    ],
    "mascotas-8-6": [
        ("p", "En este video, se aborda la técnica para pintar los ojos de un perro, destacando la importancia de captar su esencia a través de los detalles. Se describe cómo identificar y mezclar los diferentes tonos oscuros de los ojos, utilizando un cuentagotas para observar subtonos como verdosos o morados. El proceso incluye contornear y ajustar la forma de los ojos para que se asemejen más a la mascota, así como la aplicación de colores específicos para realzar la luz y la profundidad. Además, se enfatiza la creación de un punto de luz, crucial para dar vida a la pintura, recordando que la observación cuidadosa es clave para lograr un resultado satisfactorio. Por último, se sugiere que en capas posteriores se añadirán más detalles y luces para un acabado más brillante y atractivo."),
    ],
    "mascotas-8-7": [],
    "mascotas-8-8": [],
    "mascotas-8-9": [],
    "mascotas-8-10": [
        ("p", "¡Artista! Hemos concluído este BOOTCAMP. Tanto para ti como para mi esta fue una experiencia nueva y solo tengo que decir que... Ame poder seguir de más cerca tu progreso y ver como creaste capa por capa este peludito."),
        ("p", "Me hace super feliz saber que llegaste hasta este punto del proyecto y que te hayas llevado un aprendizaje en el proceso, al final es lo que más importa más allá del resultado."),
        ("p", "Para cerrar con broche de oro, sube una foto de tu resultado final y en la sección de comentarios me encantaría que me compartas TODO lo que sentiste durante tu proceso, lo que aprendiste, o lo que tu quieras. :)"),
        ("p", "Muchas gracias artista, y estate muy atent@ del próximo. 🫡"),
    ],
}

PENDIENTE = "Contenido por agregar — sube el video a Vimeo y pega el enlace aquí."


def build_blocks(lesson_name):
    blocks = []
    seq = 0

    def bid():
        nonlocal seq
        seq += 1
        return f"{lesson_name.replace('mascotas-', 'b')}x{seq}"

    if lesson_name in VIDEOS:
        vid = VIDEOS[lesson_name]
        blocks.append(
            {
                "id": bid(),
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
        )

    items = DESC.get(lesson_name, [])
    pending_list = []

    def flush_list():
        nonlocal pending_list
        if pending_list:
            blocks.append(
                {
                    "id": bid(),
                    "type": "list",
                    "data": {
                        "style": "unordered",
                        "items": [{"content": t, "items": []} for t in pending_list],
                    },
                }
            )
            pending_list = []

    for tag, text in items:
        if tag == "li":
            pending_list.append(text)
            continue
        flush_list()
        if tag in ("h1", "h2"):
            blocks.append({"id": bid(), "type": "header", "data": {"text": text, "level": 3}})
        elif tag in ("h3", "h4"):
            blocks.append({"id": bid(), "type": "header", "data": {"text": text, "level": 4}})
        else:
            blocks.append({"id": bid(), "type": "paragraph", "data": {"text": text}})
    flush_list()

    if not blocks:
        blocks.append({"id": bid(), "type": "paragraph", "data": {"text": PENDIENTE}})
    return blocks


count = 0
for m_idx, n_lessons in [(1, 4), (2, 1), (3, 2), (4, 4), (5, 1), (6, 5), (7, 1), (8, 10)]:
    for l_idx in range(1, n_lessons + 1):
        name = f"mascotas-{m_idx}-{l_idx}"
        blocks = build_blocks(name)
        frappe.db.set_value(
            "Course Lesson", name, "content", json.dumps({"blocks": blocks}), update_modified=True
        )
        count += 1
        print("OK", name, "| bloques:", len(blocks))

frappe.db.commit()
print("TOTAL:", count, "lecciones con contenido")
