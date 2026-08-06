import json
import os
import re
import secrets
import shutil
import tempfile
import zipfile
from datetime import date, datetime, timedelta

import frappe
from frappe import _
from frappe.utils import escape_html, validate_email_address
from frappe.utils.file_manager import is_safe_path

from lms.lms.utils import create_user as create_lms_user


def export_course_zip(course_name):
	course = frappe.get_doc("LMS Course", course_name)
	chapters = get_chapters_for_export(course.chapters)
	lessons = get_lessons_for_export(course_name)
	instructors = get_course_instructors(course)
	evaluator = get_course_evaluator(course)
	assessments, questions, test_cases = get_course_assessments(lessons)
	assets = get_course_assets(course, lessons, instructors, evaluator, assessments, questions)
	safe_time = frappe.utils.now_datetime().strftime("%Y%m%d_%H%M%S")
	zip_filename = f"{course.name}_{safe_time}_{secrets.token_hex(4)}.zip"
	create_course_zip(
		zip_filename,
		course,
		chapters,
		lessons,
		assets,
		assessments,
		questions,
		test_cases,
		instructors,
		evaluator,
	)


def get_chapters_for_export(chapters: list):
	chapters_list = []
	for row in chapters:
		chapter = frappe.get_doc("Course Chapter", row.chapter)
		chapters_list.append(chapter)
	return chapters_list


def get_lessons_for_export(course_name: str):
	lessons = frappe.get_all("Course Lesson", {"course": course_name}, pluck="name")
	lessons_list = []
	for lesson in lessons:
		lesson_doc = frappe.get_doc("Course Lesson", lesson)
		lessons_list.append(lesson_doc)
	return lessons_list


def get_assessment_from_block(block):
	block_type = block.get("type")
	data_field = "exercise" if block_type == "program" else block_type
	name = block.get("data", {}).get(data_field)
	doctype = get_assessment_map().get(block_type)
	if frappe.db.exists(doctype, name):
		return frappe.get_doc(doctype, name)
	return None


def get_quiz_questions(doc):
	questions = []
	for q in doc.questions:
		question_doc = frappe.get_doc("LMS Question", q.question)
		questions.append(question_doc.as_dict())
	return questions


def get_exercise_test_cases(doc):
	test_cases = []
	for tc in doc.test_cases:
		test_case_doc = frappe.get_doc("LMS Test Case", tc.name)
		test_cases.append(test_case_doc.as_dict())
	return test_cases


def get_assessments_from_lesson(lesson):
	assessments, questions, test_cases = [], [], []
	content = json.loads(lesson.content) if lesson.content else {}
	for block in content.get("blocks", []):
		if block.get("type") not in ("quiz", "assignment", "program"):
			continue
		doc = get_assessment_from_block(block)
		if not doc:
			continue
		assessments.append(doc.as_dict())
		if doc.doctype == "LMS Quiz":
			questions.extend(get_quiz_questions(doc))
		elif doc.doctype == "LMS Programming Exercise":
			test_cases.extend(get_exercise_test_cases(doc))
	return assessments, questions, test_cases


def get_course_assessments(lessons):
	assessments, questions, test_cases = [], [], []
	for lesson in lessons:
		lesson_assessments, lesson_questions, lesson_test_cases = get_assessments_from_lesson(lesson)
		assessments.extend(lesson_assessments)
		questions.extend(lesson_questions)
		test_cases.extend(lesson_test_cases)
	return assessments, questions, test_cases


def get_course_instructors(course):
	users = []
	for instructor in course.instructors:
		user_info = frappe.db.get_value(
			"User",
			instructor.instructor,
			["name", "full_name", "first_name", "last_name", "email", "user_image"],
			as_dict=True,
		)
		if user_info:
			users.append(user_info)
	return users


def get_course_evaluator(course):
	evaluators = []
	if course.evaluator and frappe.db.exists("Course Evaluator", course.evaluator):
		evaluator_info = frappe.get_doc("Course Evaluator", course.evaluator)
		evaluators.append(evaluator_info)
	return evaluators


# Un cuestionario ilustrado guarda sus fotos dentro del HTML del enunciado y de
# las explicaciones, no en bloques `upload`. Mirando solo los bloques, el ZIP
# viajaba sin ellas y el quiz llegaba al destino con las imágenes rotas.
ASSET_EN_HTML = re.compile(r'src=[\'"](/(?:private/)?files/[^\'"]+)[\'"]')


def recoger_assets(valor, assets):
	"""Recorre cualquier estructura y anota las rutas de fichero que encuentre."""
	if isinstance(valor, str):
		assets.extend(ASSET_EN_HTML.findall(valor))
	elif isinstance(valor, dict):
		for v in valor.values():
			recoger_assets(v, assets)
	elif isinstance(valor, (list, tuple)):
		for v in valor:
			recoger_assets(v, assets)


def get_course_assets(course, lessons, instructors, evaluator, assessments=None, questions=None):
	assets = []
	if course.image:
		assets.append(course.image)
	for lesson in lessons:
		content = json.loads(lesson.content) if lesson.content else {}
		for block in content.get("blocks", []):
			if block.get("type") == "upload":
				url = block.get("data", {}).get("file_url")
				assets.append(url)
		# Y las imágenes que van sueltas en el HTML de un párrafo o una tabla.
		recoger_assets(content.get("blocks", []), assets)
	for evaluacion in assessments or []:
		recoger_assets(evaluacion, assets)
	for pregunta in questions or []:
		recoger_assets(pregunta, assets)
	for instructor in instructors:
		if instructor.get("user_image"):
			assets.append(instructor["user_image"])
	if len(evaluator):
		assets.append(evaluator[0].user_image)
	return assets


def read_asset_content(url):
	try:
		file_doc = frappe.get_doc("File", {"file_url": url})
		file_path = file_doc.get_full_path()
		if not is_safe_path(file_path):
			return None
		with open(file_path, "rb") as f:
			return f.read()
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Could not read asset: {url}")
		return None


def create_course_zip(
	zip_filename,
	course,
	chapters,
	lessons,
	assets,
	assessments,
	questions,
	test_cases,
	instructors,
	evaluator,
):
	try:
		tmp_path = os.path.join(tempfile.gettempdir(), zip_filename)
		build_course_zip(
			tmp_path,
			course,
			chapters,
			lessons,
			assets,
			assessments,
			questions,
			test_cases,
			instructors,
			evaluator,
		)
		final_path = move_zip_to_private(tmp_path, zip_filename)
		schedule_file_deletion(final_path, delay_seconds=600)  # 10 minutes
		serve_zip(final_path, zip_filename)
	except Exception as e:
		frappe.throw(
			_("Could not create the course ZIP file. Please try again later. Error: {0}").format(str(e))
		)
		return None


def build_course_zip(
	tmp_path, course, chapters, lessons, assets, assessments, questions, test_cases, instructors, evaluator
):
	with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
		write_course_json(zip_file, course)
		write_chapters_json(zip_file, chapters)
		write_lessons_json(zip_file, lessons)
		write_assessments_json(zip_file, assessments, questions, test_cases)
		write_assets(zip_file, assets)
		write_instructors_json(zip_file, instructors)
		write_evaluator_json(zip_file, evaluator)


def write_course_json(zip_file, course):
	zip_file.writestr("course.json", frappe_json_dumps(course.as_dict()))


def write_chapters_json(zip_file, chapters):
	for chapter in chapters:
		chapter_data = chapter.as_dict()
		chapter_json = frappe_json_dumps(chapter_data)
		safe_name = sanitize_string(chapter.name)
		zip_file.writestr(f"chapters/{safe_name}.json", chapter_json)


def write_lessons_json(zip_file, lessons):
	for lesson in lessons:
		lesson_data = lesson.as_dict()
		lesson_json = frappe_json_dumps(lesson_data)
		safe_name = sanitize_string(lesson.name)
		zip_file.writestr(f"lessons/{safe_name}.json", lesson_json)


def write_assessments_json(zip_file, assessments, questions, test_cases):
	for question in questions:
		question_json = frappe_json_dumps(question)
		safe_name = sanitize_string(question["name"])
		zip_file.writestr(f"assessments/questions/{safe_name}.json", question_json)

	for test_case in test_cases:
		test_case_json = frappe_json_dumps(test_case)
		safe_name = sanitize_string(test_case["name"])
		zip_file.writestr(f"assessments/test_cases/{safe_name}.json", test_case_json)

	for assessment in assessments:
		assessment_json = frappe_json_dumps(assessment)
		doctype = "_".join(assessment["doctype"].lower().split(" "))
		safe_name = "_".join(sanitize_string(assessment["name"]).split(" "))
		zip_file.writestr(f"assessments/{doctype}_{safe_name}.json", assessment_json)


def safe_asset_filename(name):
	"""Nombre de fichero seguro conservando el original.

	sanitize_string() está pensado para títulos y borra los guiones bajos, así
	que "03_Workbook.pdf" se guardaba como "03Workbook.pdf": al importar, el
	fichero acababa en una URL distinta de la que apunta el contenido de la
	lección y el material no se veía. Aquí solo se quita lo que permitiría
	salirse del directorio o romper la ruta.
	"""
	name = os.path.basename((name or "").replace("\\", "/")).replace("..", "")
	name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name).strip()
	return name or "asset"


def write_assets(zip_file, assets):
	assets = list(set(assets))
	for asset in assets:
		real_path = frappe.get_site_path(asset.lstrip("/"))
		if not asset or not isinstance(asset, str) or not is_safe_path(real_path):
			continue

		file_doc = frappe.get_doc("File", {"file_url": asset})
		file_path = os.path.abspath(file_doc.get_full_path())

		# El material de las lecciones es privado y las portadas públicas. La
		# carpeta lo indica para poder recrearlo igual al importar: si cambia
		# la privacidad, cambia la URL y el enlace de la lección se rompe.
		folder = "private" if file_doc.is_private else "public"
		zip_file.write(file_path, f"assets/{folder}/{safe_asset_filename(asset)}")


def move_zip_to_private(tmp_path, zip_filename):
	final_path = os.path.join(frappe.get_site_path("private", "files"), zip_filename)
	shutil.move(tmp_path, final_path)
	return final_path


def write_instructors_json(zip_file, instructors):
	instructors_json = frappe_json_dumps(instructors)
	zip_file.writestr("instructors.json", instructors_json)


def write_evaluator_json(zip_file, evaluator):
	if not len(evaluator):
		return
	evaluator_json = frappe_json_dumps(evaluator[0].as_dict())
	zip_file.writestr("evaluator.json", evaluator_json)


def serve_zip(final_path, zip_filename):
	if not os.path.exists(final_path) or not os.path.isfile(final_path):
		frappe.throw(_("File not found"))

	safe_filename = sanitize_string(zip_filename)

	try:
		with open(final_path, "rb") as f:
			frappe.local.response.filename = safe_filename
			frappe.local.response.filecontent = f.read()
			frappe.local.response.type = "download"
			frappe.local.response.content_type = "application/zip"
	except Exception as e:
		frappe.log_error(f"Error serving ZIP file: {str(e)}")
		frappe.throw(_("Error downloading file"))


def schedule_file_deletion(file_path, delay_seconds=600):
	frappe.enqueue(
		delete_file,
		file_path=file_path,
		queue="long",
		timeout=delay_seconds,
		at_front=False,
		enqueue_after_commit=True,
	)


def delete_file(file_path):
	try:
		if os.path.exists(file_path):
			os.remove(file_path)
	except Exception as e:
		frappe.log_error(f"Error deleting exported file {file_path}: {e}")


def frappe_json_dumps(data):
	def default(obj):
		try:
			if isinstance(obj, (datetime | date | timedelta)):
				return str(obj)
		except Exception as e:
			frappe.log_error(f"Error serializing object {obj}: {e}")

	return json.dumps(data, indent=4, default=default)


def import_course_zip(zip_file_path):
	zip_file_path = zip_file_path.lstrip("/")
	actual_path = frappe.get_site_path(zip_file_path)
	validate_zip_file(actual_path)

	with zipfile.ZipFile(actual_path, "r") as zip_file:
		course_data = read_json_from_zip(zip_file, "course.json")
		if not course_data:
			frappe.throw(_("Invalid course ZIP: Missing course.json"))

		create_assets(zip_file)
		create_user_for_instructors(zip_file)
		create_evaluator(zip_file)
		course_doc = create_course_doc(course_data)
		# Al importar, todo se renombra: los nombres del ZIP son los del sitio de
		# origen y en el destino ya pueden pertenecer a otra cosa. Se lleva un
		# mapa origen -> destino de cada tipo y se resuelven las referencias con
		# él; buscar por título, como se hacía antes, cruza los documentos en
		# cuanto dos lecciones o dos tareas comparten nombre.
		chapter_docs, mapa_capitulos = create_chapter_docs(zip_file, course_doc.name)
		mapa_evaluaciones = create_assessment_docs(zip_file)
		mapa_lecciones = create_lesson_docs(
			zip_file, course_doc.name, mapa_capitulos, mapa_evaluaciones
		)
		save_course_structure(zip_file, course_doc, chapter_docs, mapa_lecciones)
		return course_doc.name


def read_json_from_zip(zip_file, filename):
	try:
		with zip_file.open(filename) as f:
			return json.load(f)
	except Exception as e:
		frappe.log_error(f"Error reading {filename} from ZIP: {e}")
		return None


def create_user_for_instructors(zip_file):
	instructors = read_json_from_zip(zip_file, "instructors.json")
	if not instructors:
		return
	for instructor in instructors:
		if not frappe.db.exists("User", instructor["email"]):
			create_user(instructor)


def sanitize_string(
	value,
	allow_spaces=True,
	max_length=None,
	replacement_char=None,
	escape_html_content=True,
	strip_whitespace=True,
):
	"""
	Unified function to sanitize strings for various use cases.

	Args:
		value: String to sanitize
		allow_spaces: Whether to allow spaces in the output (True for names, False for filenames)
		max_length: Maximum length to truncate to (None for no limit)
		replacement_char: Character to replace invalid chars with (None to remove them)
		escape_html_content: Whether to escape HTML entities
		strip_whitespace: Whether to strip leading/trailing whitespace

	Returns:
		Sanitized string
	"""
	if not value:
		return value

	if strip_whitespace:
		value = value.strip()
	if max_length:
		value = value[:max_length]

	if escape_html_content:
		value = escape_html(value)

	if allow_spaces:
		invalid_pattern = r"[^a-zA-Z0-9\s\-\.]"
		valid_pattern = r"^[a-zA-Z0-9\s\-\.]+$"
	else:
		invalid_pattern = r"[^a-zA-Z0-9_\-\.]"
		valid_pattern = r"^[a-zA-Z0-9_\-\.]+$"

	if replacement_char is None:
		if not re.match(valid_pattern, value):
			value = re.sub(invalid_pattern, "", value)
	else:
		value = re.sub(invalid_pattern, replacement_char, value)

	return value


def validate_user_email(user):
	if not user.get("email") or not validate_email_address(user["email"]):
		frappe.throw(f"Invalid email for user creation: {user.get('email')}")


def get_user_names(user):
	first_name = sanitize_string(user.get("first_name", ""), max_length=50)
	last_name = sanitize_string(user.get("last_name", ""), max_length=50)
	full_name = sanitize_string(user.get("full_name", ""), max_length=100)
	parts = full_name.split() if full_name else []
	return (
		first_name or (parts[0] if parts else "Imported"),
		last_name or (" ".join(parts[1:]) if len(parts) > 1 else None),
		full_name,
	)


def create_user(user):
	first_name, last_name, full_name = get_user_names(user)
	user_doc = create_lms_user(
		email=user["email"],
		first_name=first_name,
		last_name=last_name,
		full_name=full_name,
		user_image=user.get("user_image"),
		roles=["Course Creator"],
	)
	return user_doc


def create_evaluator(zip_file):
	evaluator_data = read_json_from_zip(zip_file, "evaluator.json")
	if not evaluator_data:
		return

	if not evaluator_data.get("evaluator") or not validate_email_address(evaluator_data.get("evaluator", "")):
		frappe.log_error(f"Invalid evaluator data: {evaluator_data}")
		return

	if not frappe.db.exists("User", evaluator_data["evaluator"]):
		evaluator_data["email"] = evaluator_data["evaluator"]
		create_user(evaluator_data)

	if not frappe.db.exists("Course Evaluator", evaluator_data["name"]):
		evaluator_doc = frappe.new_doc("Course Evaluator")
		evaluator_doc.update(evaluator_data)
		evaluator_doc.insert(ignore_permissions=True)


def get_course_fields():
	return [
		"title",
		"tags",
		"image",
		"video_link",
		"card_gradient",
		"short_introduction",
		"description",
		"published",
		"upcoming",
		"featured",
		"disable_self_learning",
		"published_on",
		"category",
		"evaluator",
		"timezone",
		"paid_course",
		"paid_certificate",
		"course_price",
		"currency",
		"amount_usd",
		"enable_certification",
	]


def add_data_to_course(course_doc, course_data):
	for field in get_course_fields():
		if field in course_data:
			course_doc.set(field, course_data[field])


def add_instructors_to_course(course_doc, course_data):
	instructors = course_data.get("instructors", [])
	for instructor in instructors:
		course_doc.append("instructors", {"instructor": instructor["instructor"]})


def verify_category(category_name):
	if category_name and not frappe.db.exists("LMS Category", category_name):
		category = frappe.new_doc("LMS Category")
		category.category = category_name
		category.insert(ignore_permissions=True)


def create_course_doc(course_data):
	course_doc = frappe.new_doc("LMS Course")
	add_instructors_to_course(course_doc, course_data)
	verify_category(course_data.get("category"))
	course_data.pop("instructors", None)
	course_data.pop("chapters", None)
	add_data_to_course(course_doc, course_data)
	course_doc.insert(ignore_permissions=True)
	return course_doc


def insert_with_safe_name(doc):
	"""Inserta capítulos y lecciones sin que el título rompa el nombre.

	El autoname de ambos es "format:{####} {title}". Si el título trae una
	almohadilla —"Ejercicio #2", "Proyecto #1 (Perrito en funda)"— Frappe la
	interpreta como serie de nombres y la importación entera revienta con
	InvalidNamingSeriesError. Se genera el nombre con el título sin
	almohadillas, pero el título visible se conserva intacto.
	"""
	titulo = doc.get("title") or ""
	if "#" not in titulo:
		doc.insert(ignore_permissions=True)
		return

	# Se inserta con el título sin almohadillas para que el autoname funcione,
	# y acto seguido se devuelve el título real. El nombre ya generado no se
	# toca: solo cambia lo que se muestra.
	doc.title = titulo.replace("#", "")
	doc.insert(ignore_permissions=True)
	frappe.db.set_value(doc.doctype, doc.name, "title", titulo, update_modified=False)
	doc.title = titulo


def exclude_meta_fields(data):
	meta_fields = ["name", "owner", "creation", "created_by", "modified", "modified_by", "docstatus"]
	return {k: v for k, v in data.items() if k not in meta_fields}


def create_chapter_docs(zip_file, course_name):
	chapter_docs = []
	mapa = {}
	for file in zip_file.namelist():
		if file.startswith("chapters/") and file.endswith(".json"):
			chapter_data = read_json_from_zip(zip_file, file)
			nombre_origen = (chapter_data or {}).get("name")
			chapter_data = exclude_meta_fields(chapter_data)
			if chapter_data:
				chapter_doc = frappe.new_doc("Course Chapter")
				chapter_data.pop("lessons", None)
				chapter_doc.update(chapter_data)
				chapter_doc.course = course_name
				insert_with_safe_name(chapter_doc)
				chapter_docs.append(chapter_doc)
				if nombre_origen:
					mapa[nombre_origen] = chapter_doc.name
	return chapter_docs, mapa


def get_assessment_map():
	return {"quiz": "LMS Quiz", "assignment": "LMS Assignment", "program": "LMS Programming Exercise"}


def replace_assessment_names(content, mapa_evaluaciones, sin_resolver):
	assessment_types = ["quiz", "assignment", "program"]
	content = json.loads(content)
	for block in content.get("blocks", []):
		if block.get("type") not in assessment_types:
			continue
		data_field = "exercise" if block.get("type") == "program" else block.get("type")
		nombre_origen = block.get("data", {}).get(data_field)
		destino = mapa_evaluaciones.get(nombre_origen)
		if destino:
			block["data"][data_field] = destino
		elif nombre_origen:
			# Se deja el bloque vacío a propósito. Conservar el nombre de origen
			# es peor que perderlo: en este sitio suele existir con ese nombre
			# otra tarea distinta, y la lección la mostraría sin avisar.
			block["data"].pop(data_field, None)
			sin_resolver.append(nombre_origen)
	return json.dumps(content)


def replace_assets(content):
	content = json.loads(content)
	for block in content.get("blocks", []):
		if block.get("type") == "upload":
			asset_url = block.get("data", {}).get("file_url")
			if asset_url:
				asset_name = asset_url.split("/")[-1]
				current_asset_url = frappe.db.get_value("LMS Asset", {"file_name": asset_name}, "file_url")
				if current_asset_url:
					block["data"]["url"] = current_asset_url


def reapuntar_evaluaciones(lesson_doc, course_name):
	"""Devuelve a cada evaluación su lección y su curso en este sitio.

	Al importar se les quita, porque apuntan al sitio de origen, pero no se
	volvían a poner: los cuestionarios quedaban sin dueño y solo aparecían en la
	lista general, sin forma de saber de qué curso eran.
	"""
	if not lesson_doc.content:
		return
	for block in json.loads(lesson_doc.content).get("blocks", []):
		doctype = get_assessment_map().get(block.get("type"))
		if not doctype:
			continue
		campo = "exercise" if block.get("type") == "program" else block.get("type")
		nombre = block.get("data", {}).get(campo)
		if not nombre or not frappe.db.exists(doctype, nombre):
			continue
		# No todas las evaluaciones tienen los dos campos: LMS Assignment, por
		# ejemplo, no guarda a qué lección pertenece.
		meta = frappe.get_meta(doctype)
		valores = {}
		if meta.has_field("lesson"):
			valores["lesson"] = lesson_doc.name
		if meta.has_field("course"):
			valores["course"] = course_name
		if valores:
			frappe.db.set_value(doctype, nombre, valores, update_modified=False)


def create_lesson_docs(zip_file, course_name, mapa_capitulos, mapa_evaluaciones):
	mapa = {}
	sin_resolver = []
	for file in zip_file.namelist():
		if file.startswith("lessons/") and file.endswith(".json"):
			lesson_data = read_json_from_zip(zip_file, file)
			nombre_origen = (lesson_data or {}).get("name")
			capitulo_origen = (lesson_data or {}).get("chapter")
			lesson_data = exclude_meta_fields(lesson_data)
			if lesson_data:
				lesson_doc = frappe.new_doc("Course Lesson")
				lesson_doc.update(lesson_data)
				lesson_doc.course = course_name
				lesson_doc.chapter = mapa_capitulos.get(capitulo_origen)
				lesson_doc.content = (
					replace_assessment_names(lesson_doc.content, mapa_evaluaciones, sin_resolver)
					if lesson_doc.content
					else None
				)
				insert_with_safe_name(lesson_doc)
				reapuntar_evaluaciones(lesson_doc, course_name)
				if nombre_origen:
					mapa[nombre_origen] = lesson_doc.name
	if sin_resolver:
		frappe.msgprint(
			_("Estas evaluaciones no venían en el ZIP y sus bloques quedaron vacíos: {0}").format(
				", ".join(sorted(set(sin_resolver)))
			),
			indicator="orange",
		)
	return mapa


def create_question_doc(zip_file, file):
	question_data = read_json_from_zip(zip_file, file)
	if not question_data:
		return None, None
	nombre_origen = question_data.pop("name", None)
	doc = frappe.new_doc("LMS Question")
	doc.update(question_data)
	doc.insert(ignore_permissions=True)
	return nombre_origen, doc.name


def create_test_case_doc(zip_file, file):
	test_case_data = read_json_from_zip(zip_file, file)
	if test_case_data:
		doc = frappe.new_doc("LMS Test Case")
		doc.update(test_case_data)
		doc.insert(ignore_permissions=True)


def add_questions_to_quiz(quiz_doc, questions, mapa_preguntas):
	for question in questions:
		# La pregunta se buscaba por su texto plano (`question_detail`) contra el
		# campo `question`, que guarda el HTML. En cuanto el enunciado llevaba
		# formato —negrita, una imagen— no casaba y el cuestionario se creaba
		# vacío, sin una sola pregunta y sin avisar.
		nombre = mapa_preguntas.get(question.get("question"))
		if not nombre:
			continue
		fila = {"question": nombre}
		# Los puntos y el tipo venían en la fila; al no copiarlos, un
		# cuestionario de 18 puntos aterrizaba valiendo 0.
		for campo in ("marks", "type"):
			if question.get(campo):
				fila[campo] = question[campo]
		quiz_doc.append("questions", fila)


def create_supporting_docs(zip_file):
	mapa_preguntas = {}
	for file in zip_file.namelist():
		if file.startswith("assessments/questions/") and file.endswith(".json"):
			origen, destino = create_question_doc(zip_file, file)
			if origen and destino:
				mapa_preguntas[origen] = destino
		elif file.startswith("assessments/test_cases/") and file.endswith(".json"):
			create_test_case_doc(zip_file, file)
	return mapa_preguntas


def is_assessment_file(file):
	return (
		file.startswith("assessments/")
		and file.endswith(".json")
		and not file.startswith("assessments/questions/")
		and not file.startswith("assessments/test_cases/")
	)


def build_assessment_doc(assessment_data, mapa_preguntas):
	"""Crea la evaluación y devuelve (nombre en el ZIP, nombre en este sitio)."""
	doctype = assessment_data.get("doctype")
	if doctype not in ("LMS Quiz", "LMS Assignment", "LMS Programming Exercise"):
		return None, None

	# El nombre del ZIP es el del sitio de origen. Antes, si aquí ya existía uno
	# igual, se daba por importada y se dejaba la referencia apuntando a ese
	# documento: la lección acababa mostrando la tarea de otro curso. Se crea
	# siempre uno nuevo y el autoname le asigna un nombre libre.
	nombre_origen = assessment_data.pop("name", None)
	questions = assessment_data.pop("questions", [])
	test_cases = assessment_data.pop("test_cases", [])
	doc = frappe.new_doc(doctype)
	doc.update(assessment_data)

	if doctype == "LMS Quiz":
		add_questions_to_quiz(doc, questions, mapa_preguntas)
	elif doctype == "LMS Programming Exercise":
		for row in test_cases:
			doc.append("test_cases", {"input": row["input"], "expected_output": row["expected_output"]})

	doc.insert(ignore_permissions=True)
	return nombre_origen, doc.name


def create_main_assessment_docs(zip_file, mapa_preguntas):
	mapa = {}
	for file in zip_file.namelist():
		if not is_assessment_file(file):
			continue
		assessment_data = read_json_from_zip(zip_file, file)
		if not assessment_data:
			continue
		# Apuntan al sitio de origen; se reponen al crear las lecciones, en
		# reapuntar_evaluaciones().
		assessment_data.pop("lesson", None)
		assessment_data.pop("course", None)
		origen, destino = build_assessment_doc(assessment_data, mapa_preguntas)
		if origen and destino:
			mapa[origen] = destino
	return mapa


def create_assessment_docs(zip_file):
	mapa_preguntas = create_supporting_docs(zip_file)
	return create_main_assessment_docs(zip_file, mapa_preguntas)


def create_asset_doc(asset_name, content, is_private=0):
	if frappe.db.exists("File", {"file_name": asset_name}):
		return
	asset_doc = frappe.new_doc("File")
	asset_doc.file_name = asset_name
	asset_doc.is_private = 1 if is_private else 0
	asset_doc.content = content
	asset_doc.insert()


def process_asset_file(zip_file, file):
	# La ruta es interna del ZIP, no del disco: is_safe_path() la resolvía
	# contra el directorio del sitio y siempre daba falso, así que NINGÚN
	# fichero llegaba a importarse (y el fallo quedaba oculto en el log).
	parts = file.split("/")
	if file.startswith("/") or ".." in parts:
		return

	# assets/private/... y assets/public/...; los ZIP antiguos traen los
	# ficheros sueltos en assets/ y se tratan como públicos.
	is_private = len(parts) > 2 and parts[1] == "private"

	with zip_file.open(file) as f:
		create_asset_doc(safe_asset_filename(parts[-1]), f.read(), is_private)


def create_assets(zip_file):
	fallos = []
	for file in zip_file.namelist():
		if not file.startswith("assets/") or file.endswith("/"):
			continue
		try:
			process_asset_file(zip_file, file)
		except Exception as e:
			frappe.log_error(f"Error processing asset {file}: {e}")
			fallos.append(os.path.basename(file))
	if fallos:
		# Antes esto se tragaba en silencio y el curso quedaba sin materiales
		# sin que nadie se enterara hasta abrir la lección.
		frappe.msgprint(
			_("No se pudieron importar estos archivos: {0}").format(", ".join(fallos)),
			indicator="orange",
		)


def add_lessons_to_chapters(zip_file, chapter_docs, mapa_lecciones):
	perdidas = []
	for file in zip_file.namelist():
		if file.startswith("chapters/") and file.endswith(".json"):
			chapter_data = read_json_from_zip(zip_file, file)
			chapter_doc = next((c for c in chapter_docs if c.title == chapter_data.get("title")), None)
			if not chapter_doc:
				continue
			for lesson in chapter_data.get("lessons", []):
				# Se buscaba la lección por título dentro del curso. Cuando un
				# curso repite títulos entre módulos —"Ojos", "Tonos luz", una
				# por proyecto— todos los módulos acababan apuntando a la misma
				# y el resto quedaba creado pero fuera del temario.
				lesson_name = mapa_lecciones.get(lesson["lesson"])
				if lesson_name:
					chapter_doc.append("lessons", {"lesson": lesson_name})
				else:
					perdidas.append(lesson["lesson"])
			chapter_doc.save(ignore_permissions=True)
	if perdidas:
		frappe.msgprint(
			_("Estas lecciones no venían en el ZIP y faltan en el temario: {0}").format(
				", ".join(sorted(set(perdidas)))
			),
			indicator="orange",
		)


def add_chapter_to_course(course_doc, chapter_docs):
	course_doc.reload()
	for chapter_doc in chapter_docs:
		course_doc.append("chapters", {"chapter": chapter_doc.name})
	course_doc.save(ignore_permissions=True)


def save_course_structure(zip_file, course_doc, chapter_docs, mapa_lecciones):
	add_chapter_to_course(course_doc, chapter_docs)
	add_lessons_to_chapters(zip_file, chapter_docs, mapa_lecciones)


def validate_zip_file(zip_file_path):
	if not os.path.exists(zip_file_path) or not zipfile.is_zipfile(zip_file_path):
		frappe.throw(_("Invalid ZIP file"))

	if not is_safe_path(zip_file_path):
		frappe.throw(_("Unsafe file path detected"))
