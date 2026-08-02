import frappe

frappe.init(site="lms.localhost")
frappe.connect()

email = "alumno@taar.test"
if not frappe.db.exists("User", email):
    u = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": "Alumno",
        "last_name": "TAAR",
        "send_welcome_email": 0,
        "new_password": "Alumno123!",
    })
    u.insert(ignore_permissions=True)
    frappe.db.commit()
    print("USER_CREATED", email)
else:
    print("USER_EXISTS", email)

published = frappe.get_all("LMS Course", filters={"published": 1}, fields=["name", "title"])
allc = frappe.get_all("LMS Course", fields=["name", "title", "published"])
print("PUBLISHED_COURSES", len(published))
print("TOTAL_COURSES", len(allc))
for c in allc:
    print("  -", c.get("name"), "| pub=", c.get("published"), "|", c.get("title"))
