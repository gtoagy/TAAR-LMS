"""Inventario de quién tiene acceso pagado, para migrar desde Disco sin perder a nadie.

Recorre TODA la cuenta de Stripe y saca dos ficheros:

  auditoria_accesos.csv   una fila por persona y acceso, para revisar a mano
  auditoria_resumen.txt   los totales y los casos raros que hay que decidir

Todo el cobro de TanArtistic pasó por Stripe, así que esto es la fuente de
verdad de quién debe entrar a la plataforma nueva.

No escribe nada en Stripe: solo lee.

  set STRIPE_SECRET_KEY=sk_live_...        (Windows: set · bash: export)
  python auditar_stripe.py

La clave se lee del entorno a propósito, para no dejarla escrita en ningún
fichero del repositorio.
"""

import collections
import csv
import io
import os
import sys

try:
    import stripe
except ImportError:
    sys.exit("Falta la librería: pip install stripe")

# La consola de Windows viene en cp1252 y se come los acentos.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

clave = os.environ.get("STRIPE_SECRET_KEY")
if not clave:
    sys.exit("Falta STRIPE_SECRET_KEY en el entorno.")
if clave.startswith("sk_test"):
    print("AVISO: es una clave de PRUEBAS; los alumnos reales no saldrán.\n")
stripe.api_key = clave

# Estados en los que la persona conserva el acceso.
VIVAS = ("active", "trialing", "past_due", "unpaid")


def dinero(centavos, moneda):
    return f"{(centavos or 0) / 100:,.2f} {(moneda or '').upper()}"


def g(objeto, clave, por_defecto=None):
    """Lee un campo de un objeto de Stripe.

    A partir de la versión 12 de la librería los objetos ya no admiten .get(),
    así que se accede por clave. Sirve igual para dicts sueltos.
    """
    if objeto is None:
        return por_defecto
    try:
        valor = objeto[clave]
    except (KeyError, TypeError, AttributeError):
        return por_defecto
    return por_defecto if valor is None else valor


print("Leyendo el catálogo...")
productos = {p.id: p.name for p in stripe.Product.list(limit=100).auto_paging_iter()}
precios = {}
for pr in stripe.Price.list(limit=100).auto_paging_iter():
    recurrente = g(pr, "recurring")
    precios[pr.id] = {
        "producto": productos.get(g(pr, "product"), g(pr, "product")),
        "importe": dinero(g(pr, "unit_amount", 0), g(pr, "currency", "")),
        "recurrente": bool(recurrente),
        "intervalo": g(recurrente, "interval") if recurrente else None,
        "es_disco": g(g(pr, "metadata", {}), "app") == "disco",
    }
print(f"  {len(productos)} productos, {len(precios)} precios\n")

filas = []
avisos = []
correos = collections.defaultdict(list)
clientes = {}


def cliente(cid):
    if cid not in clientes:
        try:
            clientes[cid] = stripe.Customer.retrieve(cid)
        except Exception as e:
            clientes[cid] = None
            avisos.append(f"cliente ilegible {cid}: {e}")
    return clientes[cid]


# --- suscripciones ----------------------------------------------------------
print("Leyendo suscripciones...")
for estado in VIVAS + ("canceled",):
    for sub in stripe.Subscription.list(status=estado, limit=100).auto_paging_iter():
        c = cliente(g(sub, "customer"))
        email = g(c, "email", "")
        for item in g(g(sub, "items", {}), "data", []):
            pid = g(g(item, "price", {}), "id", "")
            info = precios.get(pid, {})
            # En Stripe, quien pide la baja sigue en "active" con
            # cancel_at_period_end hasta que le vence el periodo pagado. Si ya
            # figura como "canceled", se acabó: no arrastra acceso.
            vigente = estado in VIVAS
            filas.append(
                {
                    "correo": email,
                    "nombre": g(c, "name", ""),
                    "acceso": "Membresía",
                    "producto": info.get("producto", pid),
                    "importe": info.get("importe", ""),
                    "periodo": info.get("intervalo") or "",
                    "estado": estado,
                    "vigente": "si" if vigente else "no",
                    "baja_pedida": "si" if g(sub, "cancel_at_period_end") else "",
                    "origen_disco": "si" if info.get("es_disco") else "",
                    "referencia": sub.id,
                    "precio": pid,
                }
            )
            if email:
                correos[email.lower().strip()].append(email)
            else:
                avisos.append(f"SIN CORREO: suscripción {sub.id} (cliente {g(sub, 'customer')})")
print(f"  {len(filas)} líneas de suscripción\n")

# --- pagos únicos -----------------------------------------------------------
# Los cursos de por vida y las membresías de un solo pago viven aquí. Se leen
# desde las sesiones de Checkout porque son las que saben qué producto se
# compró; un PaymentIntent suelto no lo dice.
print("Leyendo pagos únicos...")
n_pagos = 0
for sesion in stripe.checkout.Session.list(limit=100, status="complete").auto_paging_iter():
    if g(sesion, "mode") != "payment" or g(sesion, "payment_status") != "paid":
        continue
    n_pagos += 1
    detalles = g(sesion, "customer_details", {})
    email = g(detalles, "email", "")
    try:
        lineas = stripe.checkout.Session.list_line_items(sesion.id, limit=10)
    except Exception as e:
        avisos.append(f"sesión sin detalle {sesion.id}: {e}")
        continue
    for li in g(lineas, "data", []):
        pid = g(g(li, "price", {}), "id", "")
        info = precios.get(pid, {})
        nombre_producto = info.get("producto") or g(li, "description") or pid
        es_regalo = "gift" in (nombre_producto or "").lower()
        filas.append(
            {
                "correo": email,
                "nombre": g(detalles, "name", ""),
                "acceso": "Regalo (revisar)" if es_regalo else "Pago único",
                "producto": nombre_producto,
                "importe": dinero(g(li, "amount_total", 0), g(sesion, "currency", "")),
                "periodo": "de por vida",
                "estado": "pagado",
                "vigente": "si",
                "baja_pedida": "",
                "origen_disco": "si" if info.get("es_disco") else "",
                "referencia": sesion.id,
                "precio": pid or "",
            }
        )
        if es_regalo:
            avisos.append(
                f"REGALO: {nombre_producto} pagado por {email or 'sin correo'} "
                f"({sesion.id}) — el acceso puede ser de OTRA persona"
            )
        if email:
            correos[email.lower().strip()].append(email)
        else:
            avisos.append(f"SIN CORREO: pago único {sesion.id}")
print(f"  {n_pagos} pagos únicos\n")

# --- reembolsos: quien pidió su dinero no debería conservar el acceso -------
print("Comprobando reembolsos...")
reembolsados = set()
for r in stripe.Refund.list(limit=100).auto_paging_iter():
    if g(r, "status") == "succeeded" and g(r, "payment_intent"):
        reembolsados.add(g(r, "payment_intent"))
print(f"  {len(reembolsados)} cobros reembolsados\n")

# --- escritura ---------------------------------------------------------------
campos = [
    "correo",
    "nombre",
    "acceso",
    "producto",
    "importe",
    "periodo",
    "estado",
    "vigente",
    "baja_pedida",
    "origen_disco",
    "referencia",
    "precio",
]
with io.open("auditoria_accesos.csv", "w", encoding="utf-8-sig", newline="") as fh:
    escritor = csv.DictWriter(fh, fieldnames=campos)
    escritor.writeheader()
    escritor.writerows(sorted(filas, key=lambda f: (f["correo"].lower(), f["producto"])))

vigentes = [f for f in filas if f["vigente"] == "si"]
personas = {f["correo"].lower().strip() for f in vigentes if f["correo"]}
duplicados = {k: set(v) for k, v in correos.items() if len({x for x in v}) > 1}

resumen = []
resumen.append(f"Filas totales: {len(filas)}")
resumen.append(f"Accesos vigentes: {len(vigentes)}")
resumen.append(f"Personas distintas con acceso: {len(personas)}")
resumen.append("")

resumen.append("--- Por producto (solo vigentes) ---")
for (prod, tipo), n in sorted(
    collections.Counter((f["producto"], f["acceso"]) for f in vigentes).items(),
    key=lambda x: -x[1],
):
    resumen.append(f"  {n:>4}  {tipo:<18} {prod}")
resumen.append("")

resumen.append("--- Cuántos vienen marcados como de Disco ---")
de_disco = sum(1 for f in vigentes if f["origen_disco"] == "si")
resumen.append(f"  con marca app=disco: {de_disco}")
resumen.append(f"  sin marca:           {len(vigentes) - de_disco}")
resumen.append("")

if duplicados:
    resumen.append("--- Mismo correo escrito de varias formas ---")
    for k, v in list(duplicados.items())[:40]:
        resumen.append(f"  {k}: {sorted(v)}")
    resumen.append("")

if avisos:
    resumen.append(f"--- Avisos ({len(avisos)}) ---")
    resumen.extend("  " + a for a in avisos[:120])
    if len(avisos) > 120:
        resumen.append(f"  ...y {len(avisos) - 120} más")

texto = "\n".join(resumen)
io.open("auditoria_resumen.txt", "w", encoding="utf-8").write(texto)
print(texto)
print("\nEscritos: auditoria_accesos.csv · auditoria_resumen.txt")
