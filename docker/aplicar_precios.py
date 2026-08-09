"""Devuelve a cada curso su modalidad de venta y su precio.

Los flags comerciales NO viajan dentro del ZIP de un curso: al reimportar, los
trece volvieron al valor por defecto (incluidos en la membresía, sin venta
individual). Este script deja la configuración acordada, y sirve para volver a
aplicarla si se reimporta algo.

Los price_id son los del entorno de PRUEBAS de Stripe. Al pasar a la cuenta
real hay que crear los precios allí y sustituirlos aquí.

  env/bin/python /workspace/aplicar_precios.py
"""

import frappe

frappe.init(site="lms.localhost")
frappe.connect()
frappe.set_user("Administrator")

# Mascotas se vende aparte y queda FUERA de la membresía.
# Retratos y Teoría del color entran con el plan anual y además se pueden
# comprar sueltos; con el plan mensual no se ven.
CONFIG = {
    "curso-de-mascotas": {
        "taar_incluido_en_membresia": 0,
        "taar_venta_individual": 1,
        "taar_solo_plan_anual": 0,
        "taar_stripe_price_id": "price_1Tv6TdHxzDlE1j2fas1jKy5V",
        "taar_precio_display": "$1,490 MXN",
    },
    "curso-de-retratos": {
        "taar_incluido_en_membresia": 1,
        "taar_venta_individual": 1,
        "taar_solo_plan_anual": 1,
        "taar_stripe_price_id": "price_1U0o8qHxzDlE1j2fsoe6aB5w",
        "taar_precio_display": "$1,249 MXN",
    },
    "teoria-del-color": {
        "taar_incluido_en_membresia": 1,
        "taar_venta_individual": 1,
        "taar_solo_plan_anual": 1,
        "taar_stripe_price_id": "price_1U0o97HxzDlE1j2fQJPLHvQO",
        "taar_precio_display": "$549 MXN",
    },
}

# El resto entra con cualquier membresía y no se vende suelto.
POR_DEFECTO = {
    "taar_incluido_en_membresia": 1,
    "taar_venta_individual": 0,
    "taar_solo_plan_anual": 0,
    "taar_stripe_price_id": None,
    "taar_precio_display": None,
}

for nombre in sorted(frappe.get_all("LMS Course", pluck="name")):
    deseado = dict(CONFIG.get(nombre, POR_DEFECTO))
    # paid_course es el cobro nativo del LMS y estorba al nuestro.
    deseado["paid_course"] = 0
    deseado["course_price"] = 0

    actual = frappe.db.get_value("LMS Course", nombre, list(deseado.keys()), as_dict=True)
    cambios = {k: v for k, v in deseado.items() if (actual.get(k) or None) != (v or None)}
    if not cambios:
        print(f"  {nombre:<32} ya estaba")
        continue

    curso = frappe.get_doc("LMS Course", nombre)
    curso.update(deseado)
    curso.save(ignore_permissions=True)
    print(f"  {nombre:<32} {', '.join(sorted(cambios))}")

frappe.db.commit()

print("\nComo queda:")
for nombre in sorted(frappe.get_all("LMS Course", pluck="name")):
    c = frappe.db.get_value(
        "LMS Course",
        nombre,
        ["taar_incluido_en_membresia", "taar_venta_individual", "taar_solo_plan_anual", "taar_precio_display"],
        as_dict=True,
    )
    print(
        f"  {nombre:<32} membresia={c.taar_incluido_en_membresia} "
        f"suelto={c.taar_venta_individual} solo_anual={c.taar_solo_plan_anual} {c.taar_precio_display or ''}"
    )
