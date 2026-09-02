import { createResource } from 'frappe-ui'
import { computed, ref } from 'vue'

/**
 * Las sesiones en vivo de revisión.
 *
 * Un solo recurso para toda la aplicación: lo miran la tarjeta del inicio, la
 * página de sesiones y el menú lateral, y no tiene sentido que cada uno pregunte
 * por su cuenta. Quien lo necesite llama a `pedirSesiones()`; si ya se pidió, no
 * se vuelve a pedir.
 *
 * El servidor manda `entrar` solo cuando toca —quien paga, y dentro de la
 * ventana—, así que aquí no hay ninguna decisión de acceso que tomar: si el
 * enlace viene, se enseña; si no viene, no hay botón.
 */
export const sesionesEnVivo = createResource({
	url: 'taar_lms.envivo.mis_sesiones',
	cache: 'Sesiones en vivo TAAR',
})

let pedidas = false

export function pedirSesiones() {
	if (pedidas) return
	pedidas = true
	sesionesEnVivo.fetch()
}

export function refrescarSesiones() {
	sesionesEnVivo.reload()
}

export const haySesiones = computed(
	() =>
		!!sesionesEnVivo.data?.proxima || !!sesionesEnVivo.data?.anteriores?.length
)

/**
 * Un reloj compartido que avanza cada 30 segundos.
 *
 * La cuenta atrás y el «ya empezó» no pueden depender de cuándo se cargó la
 * página: la alumna deja la pestaña abierta mientras pinta, y a la hora tiene
 * que ver el botón sin recargar nada.
 */
export const ahora = ref(new Date())
setInterval(() => (ahora.value = new Date()), 30000)

/** Cuándo empieza, en objeto Date. Vacío si la sesión no trae fecha. */
export function inicioDe(sesion) {
	if (!sesion?.inicio) return null
	const fecha = new Date(sesion.inicio)
	return isNaN(fecha.getTime()) ? null : fecha
}

/**
 * Si la sesión está en marcha, contado en el navegador.
 *
 * El servidor ya lo dice al responder, pero esa respuesta envejece: a los diez
 * minutos sigue diciendo «faltan cinco». Se recalcula aquí con los mismos
 * márgenes para que la pantalla no mienta, aunque el enlace lo siga decidiendo
 * el servidor.
 */
const ANTES_MS = 15 * 60 * 1000
const DESPUES_MS = 30 * 60 * 1000

export function estaAbierta(sesion, momento = ahora.value) {
	const inicio = inicioDe(sesion)
	if (!inicio) return false
	const fin = inicio.getTime() + (sesion.minutos || 60) * 60000 + DESPUES_MS
	return momento.getTime() >= inicio.getTime() - ANTES_MS && momento.getTime() <= fin
}

/** Cuánto falta, ya escrito: «en 5 días», «en 2 horas», «en unos minutos». */
export function cuantoFalta(sesion, momento = ahora.value) {
	const inicio = inicioDe(sesion)
	if (!inicio) return ''

	const minutos = Math.round((inicio.getTime() - momento.getTime()) / 60000)
	if (minutos <= 0) return __('Starting now')
	if (minutos < 60) return __('in {0} min').format(minutos)

	const horas = Math.round(minutos / 60)
	if (horas < 24) return __('in {0} h').format(horas)

	const dias = Math.round(horas / 24)
	return dias === 1 ? __('tomorrow') : __('in {0} days').format(dias)
}

/**
 * El idioma con el que se escriben las fechas.
 *
 * `es` a secas es español de España, y ahí las seis de la tarde son las 18:00.
 * La escuela es mexicana y sus alumnas están en América, donde se dice «6:00
 * p.m.»: una hora en formato de 24 se lee dos veces antes de entenderse.
 */
function idioma() {
	const lang = window.lang || 'es'
	return lang.startsWith('es') ? 'es-MX' : lang
}

/**
 * La fecha escrita en la hora de quien mira.
 *
 * A propósito no se usa la zona de la sesión: la alumna de Buenos Aires quiere
 * saber a qué hora se conecta ella, no a qué hora es en Cancún. La zona original
 * se enseña aparte, como referencia, para que nadie dude.
 */
export function fechaLarga(sesion) {
	const inicio = inicioDe(sesion)
	if (!inicio) return ''
	return new Intl.DateTimeFormat(idioma(), {
		weekday: 'long',
		day: 'numeric',
		month: 'long',
		hour: 'numeric',
		minute: '2-digit',
	}).format(inicio)
}

export function fechaCorta(sesion) {
	const inicio = inicioDe(sesion)
	if (!inicio) return ''
	return new Intl.DateTimeFormat(idioma(), {
		day: 'numeric',
		month: 'short',
		hour: 'numeric',
		minute: '2-digit',
	}).format(inicio)
}
