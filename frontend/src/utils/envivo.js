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

/**
 * La zona horaria de quien está mirando.
 *
 * No se usa `getUserTimezone()` de `utils`: esa comprueba la zona contra una
 * lista de fábrica y devuelve `null` en cuanto no la encuentra — y
 * `America/Cancun`, que es la de la escuela, no está en esa lista. Aquí lo que
 * hace falta es lo que diga el navegador, sea lo que sea.
 */
export function zonaDelNavegador() {
	try {
		return Intl.DateTimeFormat().resolvedOptions().timeZone || ''
	} catch (e) {
		return ''
	}
}

/** La fecha como la escriben los calendarios: 20260930T220000Z, siempre en UTC. */
function selloUtc(fecha) {
	return fecha.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
}

/** Cuándo termina, contando la duración. */
function finDe(sesion) {
	const inicio = inicioDe(sesion)
	if (!inicio) return null
	return new Date(inicio.getTime() + (sesion.minutos || 60) * 60000)
}

/**
 * El enlace para añadirla a Google Calendar.
 *
 * Se arma aquí y no en el servidor porque no hace falta nada que el navegador
 * no tenga ya: es un enlace, no un archivo. Con las horas en UTC, Google las
 * convierte sola a la zona de la cuenta de quien lo abre.
 *
 * No lleva el enlace de Zoom, por lo mismo que no lo lleva el correo: acabaría
 * en el historial del navegador y en el calendario compartido de media familia.
 */
function enlaceGoogleCalendar(sesion) {
	const inicio = inicioDe(sesion)
	const fin = finDe(sesion)
	if (!inicio || !fin) return ''

	const escuela = `${window.location.origin}/lms/en-vivo`
	const parametros = new URLSearchParams({
		action: 'TEMPLATE',
		text: sesion.titulo || '',
		dates: `${selloUtc(inicio)}/${selloUtc(fin)}`,
		details: [sesion.descripcion, `Entra desde la escuela: ${escuela}`]
			.filter(Boolean)
			.join('\n\n'),
		location: escuela,
	})
	return `https://calendar.google.com/calendar/render?${parametros}`
}

/**
 * El archivo `.ics`, para Apple, Outlook y todo lo demás.
 *
 * Lo escribe el servidor y esto solo apunta a él: tiene que abrirse con un
 * enlace de verdad —nada de `fetch` ni de `download`—, porque en el iPhone una
 * dirección que responde `text/calendar` levanta la hoja de «Agregar a
 * Calendario», mientras que un archivo armado aquí acaba en Archivos y hay que
 * ir a buscarlo.
 */
function enlaceIcs(sesion) {
	if (!sesion?.nombre) return ''
	return `/api/method/taar_lms.envivo.calendario?nombre=${encodeURIComponent(sesion.nombre)}`
}

/**
 * Si este aparato abre el `.ics` en su propio calendario.
 *
 * En el iPhone, el iPad y el Mac, una dirección que responde `text/calendar`
 * levanta el calendario del sistema. En Android y en Windows no: baja un archivo
 * que hay que ir a buscar, y eso ya no es «añadir al calendario», es un trámite.
 */
function abreElIcsSolo() {
	return /iPhone|iPad|iPod|Macintosh/.test(window.navigator?.userAgent || '')
}

/**
 * El enlace de calendario que le toca a quien está mirando.
 *
 * Uno solo, no dos: «Google Calendar / Apple u Outlook» obliga a elegir a quien
 * no sabe qué lleva su teléfono, y a la mitad le bajaba un archivo. Aquí se
 * decide por ella y siempre acaba en un calendario de verdad: el del sistema
 * donde se abre solo, y Google Calendar en el resto, que en Android es la app.
 *
 * `nueva` va aparte porque el `.ics` tiene que abrirse en la misma pestaña: en
 * iOS, una pestaña nueva que no pinta nada se queda en blanco detrás de la hoja
 * del calendario, y parece que algo se rompió.
 */
export function calendarioDeEsteAparato(sesion) {
	return abreElIcsSolo()
		? { href: enlaceIcs(sesion), nueva: false }
		: { href: enlaceGoogleCalendar(sesion), nueva: true }
}
