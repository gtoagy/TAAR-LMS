import frappe

frappe.init(site="lms.localhost")
frappe.connect()

alumno = "alumno@taar.test"

# 1) Crear un instructor dedicado (distinto del alumno)
instr = "instructor@taar.test"
if not frappe.db.exists("User", instr):
    u = frappe.get_doc({
        "doctype": "User",
        "email": instr,
        "first_name": "Instructor",
        "last_name": "TAAR",
        "send_welcome_email": 0,
        "new_password": "Instructor123!",
    })
    u.insert(ignore_permissions=True)
else:
    u = frappe.get_doc("User", instr)
u.add_roles("Course Creator", "LMS Student")
frappe.db.commit()

# 2) En TODOS los cursos, quitar al alumno de la lista de instructores;
#    si un curso queda sin instructores, asignar el instructor dedicado.
courses = frappe.get_all("LMS Course", pluck="name")
for cname in courses:
    course = frappe.get_doc("LMS Course", cname)
    before = [r.instructor for r in course.instructors]
    kept = [r for r in course.instructors if r.instructor != alumno]
    if not kept:
        course.set("instructors", [])
        course.append("instructors", {"instructor": instr})
    else:
        course.set("instructors", kept)
    course.save(ignore_permissions=True)
    after = [r.instructor for r in course.instructors]
    print("CURSO", cname, "| antes:", before, "-> despues:", after)

frappe.db.commit()

# 3) Verificar que el alumno ya no es instructor de ningun curso
rows = frappe.get_all("Course Instructor", filters={"instructor": alumno}, fields=["parent"])
print("ALUMNO_SIGUE_DE_INSTRUCTOR_EN", [r.parent for r in rows])
print("ROLES_ALUMNO", frappe.get_roles(alumno))
