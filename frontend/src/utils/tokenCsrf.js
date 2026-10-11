/**
 * El token CSRF de la sesión, para cuando la página y el servidor dejan de
 * coincidir.
 *
 * La página recibe su token al cargarse (`window.csrf_token`, en el boot) y
 * frappe-ui lo manda en cada POST. Frappe lo compara con el que tenga guardado
 * la sesión, y la sesión solo lo tiene guardado desde la primera vez que el
 * servidor pinta una página con ella abierta. Mientras la sesión sea la misma
 * con la que se cargó la página, los dos coinciden siempre.
 *
 * Dejan de coincidir cuando la sesión cambia sin recargar la página. El
 * asistente de bienvenida abre la sesión con una llamada (`completar_registro`)
 * y sigue en la misma página, con el token de invitada. Desde ese momento basta
 * con que el servidor pinte cualquier página de /lms/ con la sesión nueva —una
 * recarga en otra pestaña, o el navegador pidiendo un icono por una ruta que
 * cae en /lms/, que es lo que hace el de Instagram— para que le fije un token
 * distinto, y a partir de ahí cada POST de esta página responde "Solicitud
 * inválida" hasta que se recargue. La alumna lo veía al guardar sus respuestas,
 * que es el primer POST con aviso de error después de abrir la sesión.
 *
 * Dos remedios, los dos aquí: fijar el token en cuanto el servidor abre la
 * sesión, y si aun así un POST vuelve rechazado por el token, pedir el bueno y
 * repetirlo una sola vez. Sin recargar y sin perder lo que llevaba escrito.
 */
import { call } from 'frappe-ui'

const RUTA_TOKEN = '/api/method/taar_lms.api.token_csrf'

/** Fija el token que frappe-ui mandará de aquí en adelante. */
export function fijarToken(token) {
	if (token) window.csrf_token = token
}

/** Si el servidor rechazó la llamada por el token, y no por otra cosa. */
export function esTokenViejo(err) {
	return err?.exc_type === 'CSRFTokenError'
}

/**
 * Pide al servidor el token de la sesión abierta y lo fija.
 *
 * Por GET a propósito: un POST con el token viejo es justo lo que no pasa.
 */
export async function renovarToken() {
	const r = await fetch(RUTA_TOKEN, {
		headers: { Accept: 'application/json' },
		credentials: 'same-origin',
	})
	if (!r.ok) throw new Error(`no se pudo renovar el token (${r.status})`)
	const { message } = await r.json()
	fijarToken(message)
	return message
}

/**
 * Como `call` de frappe-ui, pero si el servidor rechaza la llamada por el
 * token, pide el bueno y la repite una sola vez. Cualquier otro error sale tal
 * cual, y si tampoco se pudo renovar el token, sale el error original.
 */
export async function llamar(metodo, params) {
	try {
		return await call(metodo, params)
	} catch (err) {
		if (!esTokenViejo(err)) throw err
		try {
			await renovarToken()
		} catch (e) {
			throw err
		}
		return await call(metodo, params)
	}
}
