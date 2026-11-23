import { createResource } from 'frappe-ui'
import { computed, ref } from 'vue'

/**
 * Los materiales de la escuela: kits por curso y artículos sueltos.
 *
 * Un solo recurso para toda la aplicación, como el de las sesiones en vivo: lo
 * miran el menú (¿está abierta la tienda?), la tienda y la tarjeta de cada
 * curso. Las cifras y lo que se puede pedir los decide siempre el servidor
 * (`taar_lms.kits`); aquí no se suma nada que luego se cobre.
 */
export const catalogoKits = createResource({
	url: 'taar_lms.kits.catalogo',
	cache: 'Catalogo de materiales TAAR',
})

let pedido = false

export function pedirCatalogo() {
	if (pedido) return
	pedido = true
	catalogoKits.fetch()
}

export const tiendaAbierta = computed(
	() => !!(catalogoKits.data?.tienda && catalogoKits.data?.vendible)
)

/**
 * El carrito de la tienda. Vive en el navegador solo como comodidad (que no se
 * pierda al recargar); el pedido de verdad nace en el servidor al confirmar la
 * dirección.
 */
const CLAVE_CARRITO = 'taar-carrito-materiales'

function leerCarrito() {
	try {
		const guardado = JSON.parse(localStorage.getItem(CLAVE_CARRITO) || '[]')
		return Array.isArray(guardado) ? guardado : []
	} catch {
		return []
	}
}

export const carrito = ref(leerCarrito())

function guardarCarrito() {
	try {
		localStorage.setItem(CLAVE_CARRITO, JSON.stringify(carrito.value))
	} catch {
		// Modo privado o almacenamiento bloqueado: el carrito vive solo en la pestaña.
	}
}

export function agregarAlCarrito(articulo, cantidad = 1) {
	const existente = carrito.value.find((x) => x.articulo === articulo.articulo)
	if (existente) {
		existente.cantidad = Math.min(existente.cantidad + cantidad, 20)
	} else {
		carrito.value.push({
			articulo: articulo.articulo,
			nombre: articulo.nombre,
			precio: articulo.precio,
			cantidad,
		})
	}
	guardarCarrito()
}

export function cambiarCantidad(articulo, cantidad) {
	carrito.value = carrito.value
		.map((x) => (x.articulo === articulo ? { ...x, cantidad } : x))
		.filter((x) => x.cantidad > 0)
	guardarCarrito()
}

export function vaciarCarrito() {
	carrito.value = []
	guardarCarrito()
}

/** Pesos con el formato de la escuela, desde centavos. Solo para enseñar. */
export function pesos(centavos) {
	const cifra = (centavos || 0) / 100
	const texto = cifra.toLocaleString('es-MX', {
		minimumFractionDigits: centavos % 100 ? 2 : 0,
		maximumFractionDigits: 2,
	})
	return `$${texto} MXN`
}

/**
 * Abre el pago del pedido. Es un enlace /comprar/kit/<pedido>: si el modal de
 * pago de la escuela está cargado, lo intercepta (tarjeta, PayPal y Mercado
 * Pago); si no, el enlace salta a la página de Stripe de siempre. Así nunca
 * se queda sin salida.
 */
export function pagarPedido(destino, volver) {
	const enlace = document.createElement('a')
	const params = volver ? `?volver=${encodeURIComponent(volver)}` : ''
	enlace.href = `/comprar/${destino}${params}`
	enlace.style.display = 'none'
	document.body.appendChild(enlace)
	enlace.click()
	enlace.remove()
}
