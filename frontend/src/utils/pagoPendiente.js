/**
 * El pago recién hecho, guardado fuera de la dirección de la página.
 *
 * Stripe devuelve a la alumna con el identificador de su sesión de pago en la
 * URL, y ese identificador es lo único que prueba quién es antes de tener
 * contraseña. El problema es que la URL no aguanta: el catálogo la limpiaba
 * nada más abrir la ventana de bienvenida, y aunque no lo hiciera, cada vez que
 * ella toca un filtro la dirección se reescribe entera. Con eso, cerrar la
 * ventana sin querer o recargar la página dejaba a alguien que acaba de pagar
 * sin forma de volver a la pantalla donde se crea la contraseña.
 *
 * Guardarlo en el navegador lo arregla: puede cerrar la pestaña, volver al día
 * siguiente y el asistente sigue ahí.
 */

const CLAVE = 'taar-pago-pendiente'
const VIGENCIA = 24 * 60 * 60 * 1000

/** Guarda el pago que viene en la dirección. Devuelve el identificador. */
export function recordarPagoPendiente(sessionId, tipo) {
	if (!sessionId) return null
	try {
		localStorage.setItem(
			CLAVE,
			JSON.stringify({ sessionId, tipo: tipo || 'membresia', ts: Date.now() })
		)
	} catch (e) {
		// Navegador en privado o con el almacenamiento bloqueado. No es grave:
		// mientras no recargue, la dirección todavía trae el identificador.
	}
	return sessionId
}

/** El pago guardado, si aún vale. */
export function recogerPagoPendiente() {
	try {
		const crudo = localStorage.getItem(CLAVE)
		if (!crudo) return null
		const dato = JSON.parse(crudo)
		if (!dato?.sessionId) return null
		// Pasado un día, ese pago ya se resolvió por correo o hay que atenderlo a
		// mano. Insistir con una pantalla de bienvenida sería desconcertante.
		if (Date.now() - (dato.ts || 0) > VIGENCIA) {
			olvidarPagoPendiente()
			return null
		}
		return dato.sessionId
	} catch (e) {
		return null
	}
}

export function olvidarPagoPendiente() {
	try {
		localStorage.removeItem(CLAVE)
	} catch (e) {
		/* nada que hacer */
	}
}
