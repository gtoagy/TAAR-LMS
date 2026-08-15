"""Inventario de quién tiene acceso pagado, para migrar sin perder a nadie.

Recorre TODA la cuenta de Stripe y saca tres ficheros:

  auditoria_accesos.csv   una fila por persona y acceso, para revisar a mano
  auditoria_resumen.txt   los totales y los casos raros que hay que decidir
  migracion.json          lo que se le pasa al importador de la plataforma

Todo el cobro de TanArtistic pasó por Stripe —primero desde Thinkific, después
desde Disco—, así que esto es la fuente de verdad de quién debe entrar a la
plataforma nueva.

No escribe nada en Stripe: solo lee.

  python auditar_stripe.py

Pide la clave secreta por teclado (no se ve al teclearla). Si prefieres, puede
venir de la variable de entorno STRIPE_SECRET_KEY. Nunca se guarda en disco.
"""

import collections
import csv
import datetime
import io
import json
import os
import sys
import time

try:
    import stripe
except ImportError:
    sys.exit("Falta la librería: pip install stripe")

# --- lo que hay que editar a mano cuando cambie el catálogo -------------------

# Qué abre en la escuela cada producto de Stripe. Lo que no esté aquí no se
# adivina: se manda a revisar.
PRODUCTOS_A_CURSO = {
    "prod_SlugDyOwTHHNVC": "curso-de-mascotas",   # Mascotas
    "prod_Slv0XlE6vipBXJ": "teoria-del-color",    # Teoría del color
}

# Pagos de un solo importe que dan la escuela entera para siempre.
MEMBRESIA_VITALICIA = {"price_1RlyYvHtYzLxc0E2ua8qO2sT"}  # 2490 MXN de un pago

# Ninguna de estas dos se puede resolver sola: quien paga un regalo casi nunca
# es quien va a estudiar, y de los workshops todavía no sabemos a qué curso del
# LMS corresponden. Se comparan contra el nombre del producto en minúsculas.
PALABRAS_A_MANO = ("gift", "regalo", "workshop", "taller")

# Hay precios denominados en dólares que se cobraron en pesos, euros y pesos
# colombianos. Estos números NO sirven para sumar importes de monedas distintas
# —eso no se hace en ningún sitio de este script—: existen solo para poder
# comparar un cobro suelto contra el umbral de abajo. Son aproximados.
EQUIVALENCIAS_A_MXN = {"mxn": 1.0, "usd": 16.6, "eur": 18.0, "cop": 0.0042}

# Por debajo de esto el cobro era una promoción vieja o un curso barato, y no
# tiene sentido pedirle reseña a quien no está pagando la membresía de verdad.
UMBRAL_RESENA_MXN = 249  # ≈ 15 USD

# Todos los que vienen de la plataforma vieja entran con el mismo plan, que abre
# más cursos que los planes nuevos (ver la migración de Disco).
PLAN_LEGACY = "Legacy"

# Estados en los que la persona conserva el acceso.
VIVAS = ("active", "trialing", "past_due", "unpaid")

# Cómo se llama cada estado de Stripe en el fichero del importador.
ESTADOS_IMPORTADOR = {
    "active": "Activa",
    "trialing": "Activa",
    "past_due": "En mora",
    "unpaid": "En mora",
    "canceled": "Cancelada",
}

TODA_LA_ESCUELA = "TODO"
REVISAR = "Revisar a mano"

# -----------------------------------------------------------------------------

# La consola de Windows viene en cp1252 y se come los acentos.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

clave = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
if not clave:
    # Se pide por teclado en vez de exigir una variable de entorno: cada
    # terminal la declara de una forma (set, $env:, export) y es la fuente
    # habitual de "pero si ya la puse". getpass no la muestra al teclearla ni
    # la deja en el historial de la terminal.
    if not sys.stdin.isatty():
        sys.exit(
            "Falta la clave. Ejecútalo desde una terminal y te la pido, "
            "o déjala en la variable STRIPE_SECRET_KEY."
        )
    import getpass

    clave = getpass.getpass("Pega tu clave secreta de Stripe (no se verá): ").strip()
if not clave:
    sys.exit("Sin clave no hay nada que leer.")
if not clave.startswith("sk_"):
    sys.exit("Eso no parece una clave secreta: debe empezar por sk_live_ o sk_test_.")
if clave.startswith("sk_test"):
    print("AVISO: es una clave de PRUEBAS; los alumnos reales no saldrán.\n")
stripe.api_key = clave


def dinero(centavos, moneda):
    return f"{(centavos or 0) / 100:,.2f} {(moneda or '').upper()}"


def a_pesos(centavos, moneda):
    """El importe llevado a pesos, solo para compararlo con el umbral.

    Devuelve None si la moneda no está en la tabla: antes que inventarse un tipo
    de cambio, la fila se manda a revisar.
    """
    factor = EQUIVALENCIAS_A_MXN.get((moneda or "").lower())
    if factor is None:
        return None
    return (centavos or 0) / 100 * factor


def fecha(ts):
    """La marca de tiempo de Stripe en algo que se pueda leer de un vistazo.

    En UTC, que es en lo que Stripe las guarda: así el fichero sale igual se
    ejecute desde donde se ejecute.
    """
    if not ts:
        return ""
    momento = datetime.datetime.fromtimestamp(int(ts), datetime.timezone.utc)
    return momento.strftime("%Y-%m-%d %H:%M:%S")


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


def id_de(valor):
    """El identificador de un campo que unas veces llega suelto y otras entero.

    Según lo que se haya expandido en la petición, Stripe devuelve "cus_123" o
    el objeto completo; a este script solo le interesa la cadena.
    """
    if not valor:
        return ""
    if isinstance(valor, str):
        return valor
    return g(valor, "id", "") or ""


print("Leyendo el catálogo...")
productos = {p.id: p.name for p in stripe.Product.list(limit=100).auto_paging_iter()}
precios = {}
for pr in stripe.Price.list(limit=100).auto_paging_iter():
    recurrente = g(pr, "recurring")
    precios[pr.id] = {
        "producto_id": id_de(g(pr, "product")),
        "producto": productos.get(id_de(g(pr, "product")), id_de(g(pr, "product"))),
        "importe": dinero(g(pr, "unit_amount", 0), g(pr, "currency", "")),
        "centavos": g(pr, "unit_amount", 0),
        "moneda": g(pr, "currency", ""),
        "recurrente": bool(recurrente),
        "intervalo": g(recurrente, "interval") if recurrente else None,
        "es_disco": g(g(pr, "metadata", {}), "app") == "disco",
    }
print(f"  {len(productos)} productos, {len(precios)} precios\n")

# Los cobros viejos de Thinkific no traen ni precio ni producto: lo único que
# queda es el texto del cobro. Se compara contra el nombre que el propio Stripe
# le puso a los productos ya mapeados, que no es adivinar: es el mismo mapa de
# arriba leído por su nombre en vez de por su identificador.
NOMBRES_A_CURSO = {}
for _pid, _curso in PRODUCTOS_A_CURSO.items():
    _nombre = (productos.get(_pid) or "").strip().lower()
    if _nombre:
        NOMBRES_A_CURSO[_nombre] = _curso

filas = []
avisos = []
correos = collections.defaultdict(list)
clientes = {}


def cliente(cid):
    if not cid:
        return None
    if cid not in clientes:
        try:
            clientes[cid] = stripe.Customer.retrieve(cid)
        except Exception as e:
            clientes[cid] = None
            avisos.append(f"cliente ilegible {cid}: {e}")
    return clientes[cid]


def acceso_de(texto, price_id="", producto_id="", es_membresia=False):
    """Traduce una compra a lo que abre en la escuela.

    Devuelve (identificador del curso o TODO, motivo). El motivo solo se llena
    cuando la compra se manda a revisar, y es lo que se le explica a la dueña
    para que decida. Nunca se clasifica por importe: 1490 MXN pueden ser el
    curso de Mascotas, una gift card o la suscripción anual.
    """
    nombre = (texto or "").lower()
    # Primero lo que se revisa siempre, aunque el producto esté mapeado: un
    # regalo mapeado le daría el curso a quien pagó, no a quien va a estudiar.
    for palabra in PALABRAS_A_MANO:
        if palabra in nombre:
            return REVISAR, f"«{texto}» contiene «{palabra}»: decidir a quién le toca"
    if price_id and price_id in MEMBRESIA_VITALICIA:
        return TODA_LA_ESCUELA, ""
    if producto_id and producto_id in PRODUCTOS_A_CURSO:
        return PRODUCTOS_A_CURSO[producto_id], ""
    if es_membresia:
        # Una suscripción en esta escuela es la membresía, y la legacy abre todo.
        return TODA_LA_ESCUELA, ""
    for nombre_catalogo, curso in NOMBRES_A_CURSO.items():
        if nombre_catalogo in nombre:
            return curso, ""
    return REVISAR, f"no sé qué abre «{texto or price_id or 'un cobro sin descripción'}»"


ahora = int(time.time())

# --- reembolsos: quien pidió su dinero no conserva el acceso -----------------
# Se leen antes que nada porque hacen falta para marcar los cobros de abajo.
print("Comprobando reembolsos...")
reembolsados = set()
for r in stripe.Refund.list(limit=100).auto_paging_iter():
    if g(r, "status") != "succeeded":
        continue
    for campo in ("payment_intent", "charge"):
        referencia = id_de(g(r, campo))
        if referencia:
            reembolsados.add(referencia)
print(f"  {len(reembolsados)} referencias reembolsadas\n")


# --- suscripciones ----------------------------------------------------------
def suscripciones(estado):
    """Las suscripciones de un estado, con la última factura ya incluida.

    Se pide expandida porque el importe realmente facturado —con descuentos y
    cupones aplicados— solo está ahí. Si la versión de la API no admite la
    expansión se sigue sin ella y el importe se saca del precio de catálogo.
    """
    try:
        return stripe.Subscription.list(
            status=estado, limit=100, expand=["data.latest_invoice"]
        ).auto_paging_iter()
    except Exception as e:
        avisos.append(f"suscripciones {estado} sin factura expandida: {e}")
        return stripe.Subscription.list(status=estado, limit=100).auto_paging_iter()


def ultimo_cobro(sub):
    """Lo que se le facturó la última vez, en su moneda de verdad.

    Devuelve (centavos, moneda). Se usa el total de la factura y no lo cobrado,
    porque a una suscripción en mora aún no le han pasado el cargo y no por eso
    deja de estar pagando ese importe.
    """
    factura = g(sub, "latest_invoice")
    if factura is not None and not isinstance(factura, str):
        importe = g(factura, "total")
        if importe is None:
            importe = g(factura, "amount_paid", 0)
        return importe or 0, g(factura, "currency", "")
    lineas = g(g(sub, "items", {}), "data", []) or []
    precio = g(lineas[0], "price", {}) if lineas else {}
    # El catálogo manda sobre lo que venga dentro del abono: según la versión de
    # la API, el precio de la línea llega entero o como un identificador pelado,
    # y sin importe ni moneda no se puede comparar nada contra el umbral.
    info = precios.get(id_de(g(precio, "id", "")), {})
    return (
        info.get("centavos") or g(precio, "unit_amount", 0) or 0,
        info.get("moneda") or g(precio, "currency", ""),
    )


print("Leyendo suscripciones...")
for estado in VIVAS + ("canceled",):
    for sub in suscripciones(estado):
        cid = id_de(g(sub, "customer"))
        c = cliente(cid)
        email = g(c, "email", "")
        centavos, moneda = ultimo_cobro(sub)
        for item in g(g(sub, "items", {}), "data", []):
            pid = id_de(g(g(item, "price", {}), "id", ""))
            info = precios.get(pid, {})
            # Stripe movió current_period_end del abono a cada línea; se mira en
            # los dos sitios para no depender de la versión de la librería.
            fin = g(sub, "current_period_end") or g(item, "current_period_end")
            # Una baja no borra lo que ya está pagado: si el periodo todavía no
            # ha vencido, esa persona conserva el derecho a entrar hasta la
            # fecha de corte, aunque Stripe ya la dé por cancelada.
            vigente = estado in VIVAS or bool(fin and int(fin) > ahora)
            acceso_a, motivo = acceso_de(
                info.get("producto") or pid,
                price_id=pid,
                producto_id=info.get("producto_id", ""),
                es_membresia=True,
            )
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
                    "reembolsado": "",
                    "da_acceso_a": acceso_a,
                    "acceso_hasta": fecha(fin),
                    "baja_pedida": "si" if g(sub, "cancel_at_period_end") else "",
                    "origen_disco": "si" if info.get("es_disco") else "",
                    "referencia": sub.id,
                    "precio": pid,
                    "_tipo": "suscripcion",
                    "_estado_stripe": estado,
                    "_vigente": vigente,
                    "_vitalicio": False,
                    "_cliente": cid,
                    "_suscripcion": sub.id,
                    "_fin": int(fin) if fin else 0,
                    "_centavos": centavos,
                    "_moneda": moneda,
                    "_motivos": [motivo] if motivo else [],
                }
            )
            if email:
                correos[email.lower().strip()].append(email)
            else:
                avisos.append(f"SIN CORREO: suscripción {sub.id} (cliente {cid})")
print(f"  {len(filas)} líneas de suscripción\n")

# --- pagos únicos -----------------------------------------------------------
# Los cursos de por vida y las membresías de un solo pago viven aquí. La espina
# dorsal son los Charge y no las sesiones de Checkout: la mayor parte del
# histórico se cobró desde Thinkific, que no usaba Checkout, y esos pagos solo
# existen como Charge. Las sesiones siguen haciendo falta porque son las únicas
# que dicen qué producto se compró, así que se indexan antes por payment_intent
# y luego se consultan de memoria: una petición por cobro serían miles.
print("Indexando sesiones de Checkout...")
sesiones_por_pi = {}
lineas_por_sesion = {}


def sesiones_completas():
    """Las sesiones pagadas, con sus líneas de detalle en la misma petición."""
    try:
        return stripe.checkout.Session.list(
            limit=100, status="complete", expand=["data.line_items"]
        ).auto_paging_iter()
    except Exception as e:
        avisos.append(f"sesiones sin líneas expandidas: {e}")
        return stripe.checkout.Session.list(limit=100, status="complete").auto_paging_iter()


for sesion in sesiones_completas():
    if g(sesion, "payment_status") != "paid":
        continue
    pi = id_de(g(sesion, "payment_intent"))
    if pi:
        sesiones_por_pi[pi] = sesion
print(f"  {len(sesiones_por_pi)} sesiones pagadas\n")


def lineas_de(sesion):
    """Las líneas de una sesión, pidiéndolas solo si no vinieron ya expandidas."""
    sid = g(sesion, "id", "")
    if sid in lineas_por_sesion:
        return lineas_por_sesion[sid]
    lineas = g(g(sesion, "line_items"), "data")
    if lineas is None:
        try:
            lineas = g(stripe.checkout.Session.list_line_items(sid, limit=10), "data", [])
        except Exception as e:
            avisos.append(f"sesión sin detalle {sid}: {e}")
            lineas = []
    lineas_por_sesion[sid] = lineas
    return lineas


def datos_de_contacto(cargo, sesion):
    """El correo y el nombre de un cobro, mirando donde haga falta.

    Los cobros de Thinkific no tienen sesión de Checkout, así que el correo hay
    que buscarlo en los datos de facturación o en el propio cliente.
    """
    detalles = g(sesion, "customer_details", {}) if sesion is not None else {}
    facturacion = g(cargo, "billing_details", {})
    email = g(detalles, "email") or g(facturacion, "email") or g(cargo, "receipt_email") or ""
    nombre = g(detalles, "name") or g(facturacion, "name") or ""
    if not email:
        c = cliente(id_de(g(cargo, "customer")))
        email = g(c, "email", "")
        nombre = nombre or g(c, "name", "")
    return email, nombre


print("Leyendo cobros únicos (toda la historia de la cuenta)...")
n_cobros = 0
for cargo in stripe.Charge.list(limit=100).auto_paging_iter():
    if g(cargo, "status") != "succeeded":
        continue
    # Un cobro con factura es el recibo de una suscripción, que ya se contó
    # arriba; aquí solo interesan las compras sueltas.
    if g(cargo, "invoice"):
        continue
    n_cobros += 1
    if n_cobros % 500 == 0:
        print(f"  {n_cobros} cobros...")

    pi = id_de(g(cargo, "payment_intent"))
    sesion = sesiones_por_pi.get(pi) if pi else None
    email, nombre_persona = datos_de_contacto(cargo, sesion)
    moneda = g(cargo, "currency", "")
    # El cobro puede venir ya marcado, o saberse solo por la lista de reembolsos.
    hay_reembolso = (
        bool(g(cargo, "refunded"))
        or (g(cargo, "amount_refunded", 0) or 0) > 0
        or bool(pi and pi in reembolsados)
        or g(cargo, "id", "") in reembolsados
    )
    # Devolver una parte no es devolver la compra: suele ser un detalle
    # comercial de unos pesos, y quitarle el curso a quien sí pagó sería peor
    # que preguntarlo. Solo se pierde el acceso cuando se devolvió todo.
    parcial = hay_reembolso and 0 < (g(cargo, "amount_refunded", 0) or 0) < (
        g(cargo, "amount", 0) or 0
    )
    devuelto = hay_reembolso and not parcial

    # Qué se compró: primero la línea de detalle de la sesión, que es el dato
    # bueno; si no hay sesión, la descripción que dejó la pasarela vieja.
    compras = []
    for li in lineas_de(sesion) if sesion is not None else []:
        precio_linea = g(li, "price", {})
        pid = id_de(g(precio_linea, "id", ""))
        info = precios.get(pid, {})
        producto_id = info.get("producto_id") or id_de(g(precio_linea, "product"))
        texto = info.get("producto") or g(li, "description") or pid
        compras.append(
            {
                "texto": texto,
                "price_id": pid,
                "producto_id": producto_id,
                "centavos": g(li, "amount_total", 0),
                "es_disco": info.get("es_disco", False),
            }
        )
    if not compras:
        compras.append(
            {
                "texto": g(cargo, "description") or "",
                "price_id": "",
                "producto_id": "",
                "centavos": g(cargo, "amount", 0),
                "es_disco": False,
            }
        )

    for compra in compras:
        acceso_a, motivo = acceso_de(
            compra["texto"],
            price_id=compra["price_id"],
            producto_id=compra["producto_id"],
        )
        vitalicio = acceso_a == TODA_LA_ESCUELA
        if devuelto:
            etiqueta = "Reembolsado"
        elif vitalicio:
            etiqueta = "Membresía de por vida"
        else:
            etiqueta = "Pago único"
        filas.append(
            {
                "correo": email,
                "nombre": nombre_persona,
                "acceso": etiqueta,
                "producto": compra["texto"] or (pi or g(cargo, "id", "")),
                "importe": dinero(compra["centavos"], moneda),
                "periodo": "" if devuelto else "de por vida",
                "estado": "reembolsado" if devuelto else "pagado",
                "vigente": "no" if devuelto else "si",
                "reembolsado": "si" if devuelto else ("parcial" if parcial else ""),
                "da_acceso_a": acceso_a,
                "acceso_hasta": "" if devuelto else "siempre",
                "baja_pedida": "",
                "origen_disco": "si" if compra["es_disco"] else "",
                "referencia": g(sesion, "id", "") or g(cargo, "id", ""),
                "precio": compra["price_id"],
                "_tipo": "unico",
                "_estado_stripe": "",
                "_vigente": not devuelto,
                "_vitalicio": vitalicio and not devuelto,
                "_cliente": id_de(g(cargo, "customer")),
                "_suscripcion": "",
                "_fin": 0,
                "_centavos": compra["centavos"],
                "_moneda": moneda,
                "_motivos": [
                    m
                    for m in (
                        motivo,
                        f"le devolvimos parte de «{compra['texto']}»: confirmar que conserva el acceso"
                        if parcial
                        else "",
                    )
                    if m
                ],
            }
        )
        if motivo and not devuelto:
            avisos.append(
                f"REVISAR: {compra['texto'] or 'cobro sin descripción'} de "
                f"{email or 'sin correo'} ({g(cargo, 'id', '')}) — {motivo}"
            )
        if email:
            correos[email.lower().strip()].append(email)
        else:
            avisos.append(f"SIN CORREO: cobro único {g(cargo, 'id', '')}")
print(f"  {n_cobros} cobros únicos\n")

# --- el fichero del importador ----------------------------------------------
# Una entrada por persona, agrupando por correo en minúsculas. Solo entra quien
# conserva algún acceso: lo reembolsado y lo cancelado y vencido se queda fuera.
print("Agrupando por persona...")
personas = {}
# El orden de mejor a peor para quedarse con una sola suscripción por persona.
RANGO_ESTADO = {"active": 0, "trialing": 1, "past_due": 2, "unpaid": 3, "canceled": 4}


def anota(persona, motivo):
    if motivo and motivo not in persona["revisar"]:
        persona["revisar"].append(motivo)


for fila in filas:
    correo = fila["correo"].lower().strip()
    if not correo or not fila["_vigente"]:
        continue
    persona = personas.get(correo)
    if persona is None:
        persona = personas[correo] = {
            "correo": correo,
            "nombre": "",
            "acceso": "",
            "plan": PLAN_LEGACY,
            "vitalicio": False,
            "invitar_resena": False,
            "estado": "",
            "acceso_hasta": "",
            "stripe_customer_id": "",
            "stripe_subscription_id": "",
            "cursos": [],
            "revisar": [],
            "_membresia": False,
            "_rango": 99,
        }
    persona["nombre"] = persona["nombre"] or fila["nombre"] or ""
    persona["stripe_customer_id"] = persona["stripe_customer_id"] or fila["_cliente"]
    for motivo_fila in fila["_motivos"]:
        anota(persona, motivo_fila)

    if fila["da_acceso_a"] == TODA_LA_ESCUELA:
        persona["_membresia"] = True
    elif fila["da_acceso_a"] != REVISAR and fila["da_acceso_a"] not in persona["cursos"]:
        persona["cursos"].append(fila["da_acceso_a"])

    if fila["_vitalicio"]:
        persona["vitalicio"] = True

    if fila["_tipo"] != "suscripcion":
        continue

    # Con varias suscripciones se conserva la mejor: la más viva, y a igualdad
    # de estado la que llega más lejos. Las demás quedan anotadas para revisar.
    if persona["stripe_subscription_id"] and persona["stripe_subscription_id"] != fila["_suscripcion"]:
        anota(persona, "tiene más de una suscripción vigente")
    rango = RANGO_ESTADO.get(fila["_estado_stripe"], 9)
    mejor = rango < persona["_rango"] or (
        rango == persona["_rango"] and fecha(fila["_fin"]) > persona["acceso_hasta"]
    )
    if not mejor:
        continue
    persona["_rango"] = rango
    persona["estado"] = ESTADOS_IMPORTADOR.get(fila["_estado_stripe"], fila["_estado_stripe"])
    persona["acceso_hasta"] = fecha(fila["_fin"])
    persona["stripe_subscription_id"] = fila["_suscripcion"]
    persona["stripe_customer_id"] = fila["_cliente"] or persona["stripe_customer_id"]

    # La invitación a reseñar es solo para quien está pagando de verdad hoy: no
    # se le pide a quien entró con una promoción vieja de importe simbólico.
    if fila["_estado_stripe"] in ("active", "past_due"):
        pesos = a_pesos(fila["_centavos"], fila["_moneda"])
        if pesos is None:
            anota(persona, f"no sé convertir {(fila['_moneda'] or '?').upper()} a pesos")
        elif pesos >= UMBRAL_RESENA_MXN:
            persona["invitar_resena"] = True

# Un reembolso que deja a alguien sin nada no lo mete en el fichero, pero si esa
# persona conserva otras compras conviene que la dueña lo sepa al revisar.
for fila in filas:
    correo = fila["correo"].lower().strip()
    if fila["reembolsado"] == "si" and correo in personas:
        anota(personas[correo], f"le devolvimos «{fila['producto']}»: ese acceso no cuenta")

for correo, variantes in correos.items():
    if len(set(variantes)) > 1 and correo in personas:
        anota(personas[correo], f"el correo aparece escrito de varias formas: {sorted(set(variantes))}")

migracion = []
for correo in sorted(personas):
    persona = personas[correo]
    tiene_membresia = persona.pop("_membresia")
    persona.pop("_rango")
    persona["cursos"] = sorted(persona["cursos"])
    if tiene_membresia and persona["cursos"]:
        persona["acceso"] = "ambos"
    elif tiene_membresia:
        persona["acceso"] = "membresia"
    elif persona["cursos"]:
        persona["acceso"] = "cursos"
    else:
        # Todo lo que compró está sin resolver (una gift card, un workshop). Se
        # deja en el fichero con el acceso vacío para que nadie se pierda por
        # silencio, pero NO se le da nada hasta que alguien lo mire.
        persona["acceso"] = ""
        anota(persona, "no se le pudo asignar ningún acceso: decidir a mano")
    migracion.append(persona)

with io.open("migracion.json", "w", encoding="utf-8") as fh:
    json.dump(migracion, fh, ensure_ascii=False, indent=2)
    fh.write("\n")
print(f"  {len(migracion)} personas con acceso\n")

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
    "reembolsado",
    "da_acceso_a",
    "acceso_hasta",
    "baja_pedida",
    "origen_disco",
    "referencia",
    "precio",
]
with io.open("auditoria_accesos.csv", "w", encoding="utf-8-sig", newline="") as fh:
    # extrasaction: las filas llevan campos internos con guion bajo que sirven
    # para armar el JSON y no pintan nada en la hoja de cálculo.
    escritor = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
    escritor.writeheader()
    escritor.writerows(sorted(filas, key=lambda f: (f["correo"].lower(), f["producto"])))

vigentes = [f for f in filas if f["vigente"] == "si"]
con_acceso = {f["correo"].lower().strip() for f in vigentes if f["correo"]}
duplicados = {k: set(v) for k, v in correos.items() if len({x for x in v}) > 1}

resumen = []
resumen.append(f"Filas totales: {len(filas)}")
resumen.append(f"Accesos vigentes: {len(vigentes)}")
resumen.append(f"Personas distintas con acceso: {len(con_acceso)}")
resumen.append("")

resumen.append("--- Por producto (solo vigentes) ---")
for (prod, tipo), n in sorted(
    collections.Counter((f["producto"], f["acceso"]) for f in vigentes).items(),
    key=lambda x: -x[1],
):
    resumen.append(f"  {n:>4}  {tipo:<22} {prod}")
resumen.append("")

resumen.append("--- Cuántos vienen marcados como de Disco ---")
de_disco = sum(1 for f in vigentes if f["origen_disco"] == "si")
resumen.append(f"  con marca app=disco: {de_disco}")
resumen.append(f"  sin marca:           {len(vigentes) - de_disco}")
resumen.append("")

devueltas = [f for f in filas if f["reembolsado"]]
resumen.append("--- Reembolsos ---")
resumen.append(f"  devueltos enteros (pierden el acceso): {sum(1 for f in devueltas if f['reembolsado'] == 'si')}")
resumen.append(f"  devueltos a medias (lo conservan, revisar): {sum(1 for f in devueltas if f['reembolsado'] == 'parcial')}")
for f in devueltas[:30]:
    resumen.append(
        f"  {f['reembolsado']:<8} {f['correo'] or 'sin correo':<38} {f['producto']} ({f['importe']})"
    )
if len(devueltas) > 30:
    resumen.append(f"  ...y {len(devueltas) - 30} más")
resumen.append("")

con_tiempo = [
    f for f in filas if f["_estado_stripe"] == "canceled" and f["_vigente"]
]
resumen.append("--- Canceladas que todavía tienen tiempo pagado ---")
resumen.append(f"  siguen entrando: {len(con_tiempo)}")
for f in con_tiempo[:30]:
    resumen.append(f"  {f['correo'] or 'sin correo':<38} hasta {f['acceso_hasta']}")
if len(con_tiempo) > 30:
    resumen.append(f"  ...y {len(con_tiempo) - 30} más")
resumen.append("")

a_mano = [f for f in vigentes if f["da_acceso_a"] == REVISAR]
resumen.append("--- Compras que no se pueden resolver solas ---")
resumen.append(f"  filas a revisar: {len(a_mano)}")
for prod, n in collections.Counter(f["producto"] for f in a_mano).most_common(30):
    resumen.append(f"  {n:>4}  {prod}")
resumen.append("")

resumen.append("--- migracion.json ---")
resumen.append(f"  personas: {len(migracion)}")
for etiqueta in ("membresia", "cursos", "ambos", ""):
    n = sum(1 for p in migracion if p["acceso"] == etiqueta)
    resumen.append(f"  acceso {etiqueta or '(sin resolver)':<16} {n}")
resumen.append(f"  vitalicios:            {sum(1 for p in migracion if p['vitalicio'])}")
resumen.append(f"  se les pide reseña:    {sum(1 for p in migracion if p['invitar_resena'])}")
resumen.append(f"  con algo que revisar:  {sum(1 for p in migracion if p['revisar'])}")
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
print("\nEscritos: auditoria_accesos.csv · auditoria_resumen.txt · migracion.json")
