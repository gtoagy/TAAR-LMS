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
 * La fecha escrita en la hora de quien mira, diciendo cuál es esa hora.
 *
 * A propósito no se usa la zona de la sesión: la alumna de Buenos Aires quiere
 * saber a qué hora se conecta ella, no a qué hora es en Ciudad de México. Pero
 * una hora sola no dice si ya está convertida, y quien sabe que la escuela es
 * mexicana resta por si acaso y llega una hora tarde. Por eso termina con el
 * nombre de su zona: «6:00 p.m. hora de Colombia».
 */
export function fechaLarga(sesion) {
	const inicio = inicioDe(sesion)
	if (!inicio) return ''
	const fecha = new Intl.DateTimeFormat(idioma(), {
		weekday: 'long',
		day: 'numeric',
		month: 'long',
		hour: 'numeric',
		minute: '2-digit',
	}).format(inicio)
	return `${fecha} ${zonaEscrita(inicio)}`
}

/**
 * Las ciudades que Chrome escribe en inglés aunque la página esté en español.
 *
 * Chrome lleva los datos de idioma recortados: los países sí los trae
 * traducidos («hora de Colombia», «hora de Perú»), pero las ciudades, que es
 * como se nombra una zona dentro de un país con varias, las deja en inglés. En
 * Chrome salía «hora de Mexico City», justo la zona de casi todas las alumnas.
 * Solo van las que cambian al escribirlas en español.
 */
const CIUDADES = {
	'America/Mexico_City': 'Ciudad de México',
	'America/Cancun': 'Cancún',
	'America/Merida': 'Mérida',
	'America/Mazatlan': 'Mazatlán',
	'America/Bahia_Banderas': 'Bahía de Banderas',
	'America/Argentina/Cordoba': 'Córdoba',
	'America/Sao_Paulo': 'São Paulo',
	'America/New_York': 'Nueva York',
	'America/Los_Angeles': 'Los Ángeles',
}

/**
 * La zona de quien mira, escrita: «hora de Colombia».
 *
 * La pone el navegador (`shortGeneric`), ya en su idioma y con el país o la
 * ciudad que ella reconoce, salvo las ciudades de `CIUDADES`. Los navegadores de
 * antes de 2022 no conocen `shortGeneric` y lanzan un error: a esos se les dice
 * «tu hora local», que también responde a la duda.
 */
function zonaEscrita(momento) {
	const ciudad = CIUDADES[zonaDelNavegador()]
	if (ciudad && idioma().startsWith('es')) return `hora de ${ciudad}`
	try {
		const nombre = new Intl.DateTimeFormat(idioma(), { timeZoneName: 'shortGeneric' })
			.formatToParts(momento)
			.find((parte) => parte.type === 'timeZoneName')?.value
		if (nombre) return nombre
	} catch (e) {
		// Sigue abajo.
	}
	return `(${__('your local time')})`
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
 * lista de fábrica y devuelve `null` en cuanto no la encuentra. Aquí lo que hace
 * falta es lo que diga el navegador, sea lo que sea.
 */
export function zonaDelNavegador() {
	try {
		return Intl.DateTimeFormat().resolvedOptions().timeZone || ''
	} catch (e) {
		return ''
	}
}

/**
 * La zona en la que da clase la escuela.
 *
 * La dice el servidor, y no se adivina por el ordenador de quien programa: si
 * ese día está de viaje, las sesiones no se mueven con él. Solo si el servidor
 * todavía no ha contestado se tira de la del navegador, que es mejor que nada.
 */
export function zonaDeLaEscuela() {
	return sesionesEnVivo.data?.zona_escuela || zonaDelNavegador()
}

/**
 * Qué hora lleva esa zona respecto de Greenwich, escrito corto: «GMT-6».
 *
 * Es lo que deja ver de un golpe si se eligió la que se quería. Cien
 * identificadores como `America/Mexico_City` se leen igual de bien estando mal
 * elegidos, y la primera sesión se programó a las cinco de la mañana por no ver
 * a tiempo una diferencia de estas.
 */
export function desfaseDe(zona) {
	try {
		return (
			new Intl.DateTimeFormat('en-US', {
				timeZone: zona,
				timeZoneName: 'shortOffset',
			})
				.formatToParts(new Date())
				.find((parte) => parte.type === 'timeZoneName')?.value || ''
		)
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
 *
 * El texto de dentro sí lo escribe el servidor y llega hecho: es el mismo que el
 * del `.ics`, y teniéndolo aquí habría que cambiarlo en dos repos que se
 * despliegan por separado, con el riesgo de que durante un tiempo cada calendario
 * dijera una cosa.
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
		details: sesion.calendario || '',
		location: escuela,
	})
	return `https://calendar.google.com/calendar/render?${parametros}`
}

/**
 * El calendario de la escuela, para suscribirse desde un aparato de Apple.
 *
 * Es `webcal://` y no `https://` porque ese enlace no lo abre el navegador: se
 * lo pasa al teléfono, que abre su app de Calendario y pregunta si suscribirse.
 * Así da igual desde dónde se pulse. El `.ics` de una sola sesión por `https`
 * solo lo sabía abrir Safari: en Chrome del iPhone se quedaba en una descarga
 * que acababa en error.
 *
 * Es el calendario entero y no esta sesión porque una suscripción es para
 * siempre: con una por sesión, cada mes aparecería un calendario nuevo en su
 * lista. Con este, las siguientes llegan solas.
 */
function enlaceSuscripcion() {
	return `webcal://${window.location.host}/api/method/taar_lms.envivo.calendario_escuela`
}

/**
 * Qué aparato de Apple es este, o vacío si no es de Apple.
 *
 * El iPad se hace pasar por un Mac desde iPadOS 13 —pide las páginas de
 * escritorio—, y lo único que lo delata es que tiene pantalla táctil.
 */
function aparatoDeApple() {
	const agente = window.navigator?.userAgent || ''
	if (/iPhone|iPod/.test(agente)) return 'iPhone'
	if (/iPad/.test(agente)) return 'iPad'
	if (/Macintosh/.test(agente)) {
		return window.navigator.maxTouchPoints > 1 ? 'iPad' : 'Mac'
	}
	return ''
}

/**
 * Cómo se añade la sesión al calendario en este aparato.
 *
 * Fuera de Apple, directo a Google Calendar: en Android es el calendario del
 * teléfono, y en Windows es lo que usa casi todo el mundo. Un menú para una sola
 * opción es un toque de más.
 *
 * En Apple se pregunta, porque ahí hay dos respuestas buenas y el aparato no
 * dice cuál usa ella: el calendario del iPhone, o Google Calendar, que en
 * Latinoamérica llevan muchas de las que tienen iPhone con su cuenta de Gmail.
 *
 * Devuelve `{ href }` si va directo y `{ opciones }` si hay que elegir.
 */
export function calendarioDeEsteAparato(sesion) {
	const google = enlaceGoogleCalendar(sesion)
	const apple = aparatoDeApple()
	if (!apple) return { href: google }

	const nombres = {
		iPhone: __('iPhone Calendar'),
		iPad: __('iPad Calendar'),
		Mac: __('Mac Calendar'),
	}
	return {
		opciones: [
			{
				label: nombres[apple],
				description: __('Every session, and they update on their own'),
				onClick() {
					window.location.href = enlaceSuscripcion()
				},
			},
			{
				label: 'Google Calendar',
				description: __('Just this session'),
				onClick() {
					window.open(google, '_blank', 'noopener')
				},
			},
		],
	}
}
