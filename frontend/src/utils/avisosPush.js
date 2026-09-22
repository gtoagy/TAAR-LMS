import { ref } from 'vue'
import { call, createResource, getCachedResource } from 'frappe-ui'
import { notifications, panelVisible } from '@/stores/notifications'
import { sessionStore } from '@/stores/session'
import { esInstalada, esIOS } from '@/utils/appInstalable'
import { getLmsBasePath } from '@/utils/basePath'

/**
 * Los avisos con la app cerrada, en este aparato.
 *
 * El servidor es taar_lms/avisos_push.py (en taar-lms-app) y el service worker,
 * el de /sw.js. Aquí vive lo que le toca al navegador: pedir el permiso,
 * suscribirse, guardar la suscripción y escuchar lo que avisa el service worker.
 * Las reglas y las trampas, en docs/avisos-push.md.
 *
 * Los estados, dichos como los ve ella:
 * - 'activos': este aparato está registrado y le llegan.
 * - 'con-permiso': dio permiso pero el aparato no quedó registrado. NO se pinta
 *   como activo: no le llega nada.
 * - 'negado': bloqueó los avisos en el navegador.
 * - 'falta-instalar': iPhone o iPad sin la app instalada. En Safari no existe
 *   `PushManager`: no es que su teléfono no pueda, es que le falta un paso.
 * - 'no-soportado': el navegador no tiene avisos.
 * - 'sin-configurar': el servidor no tiene los avisos encendidos para su cuenta.
 * - 'sin-preguntar': todavía no se le ha pedido el permiso.
 */

const METODOS = 'taar_lms.avisos_push'
export const MENSAJE_AVISO = 'taar:aviso'
export const MENSAJE_NAVEGAR = 'taar:navegar'

export const configuracionPush = createResource({
	url: `${METODOS}.configuracion`,
	cache: 'TAAR Avisos Push',
})

// Hasta saber qué dice el servidor no se ofrece nada.
export const estadoPush = ref('sin-configurar')

export function soportaPush() {
	return (
		'serviceWorker' in navigator &&
		'PushManager' in window &&
		'Notification' in window
	)
}

export function plataforma() {
	if (esIOS()) return 'ios'
	if (/Android/.test(navigator.userAgent)) return 'android'
	return 'computadora'
}

/** El estado sin mirar la suscripción: lo que se sabe en el acto. */
function estadoSinSuscripcion() {
	// Primero el servidor: sin avisos para esta cuenta, ni siquiera se le dice
	// que instale la app para recibirlos.
	if (!configuracionPush.data?.habilitado) return 'sin-configurar'
	if (!soportaPush()) {
		return esIOS() && !esInstalada() ? 'falta-instalar' : 'no-soportado'
	}
	if (Notification.permission === 'denied') return 'negado'
	if (Notification.permission === 'default') return 'sin-preguntar'
	return 'con-permiso'
}

/** La llave VAPID viaja en base64url; la Push API la quiere en bytes. */
function aBytes(base64) {
	const relleno = '='.repeat((4 - (base64.length % 4)) % 4)
	const crudo = atob((base64 + relleno).replace(/-/g, '+').replace(/_/g, '/'))
	return Uint8Array.from(crudo, (c) => c.charCodeAt(0))
}

function mismaLlave(suscripcion, esperada) {
	const actual = suscripcion.options?.applicationServerKey
	if (!actual) return false
	const bytes = new Uint8Array(actual)
	return bytes.length === esperada.length && bytes.every((b, i) => b === esperada[i])
}

/** `serviceWorker.ready` no termina nunca si no hay service worker: con tope. */
function registroListo() {
	return Promise.race([
		navigator.serviceWorker.ready,
		new Promise((_, rechazar) =>
			setTimeout(() => rechazar(new Error('sin service worker')), 10000)
		),
	])
}

async function suscribir() {
	try {
		await configuracionPush.fetch()
	} catch {
		return estadoPush.value
	}
	const estado = estadoSinSuscripcion()
	if (estado !== 'con-permiso') return estado

	const llave = aBytes(configuracionPush.data.clave_publica)
	let registro
	try {
		registro = await registroListo()
	} catch {
		return 'con-permiso'
	}

	let suscripcion = await registro.pushManager.getSubscription()
	// Si cambió la llave del servidor, la suscripción vieja está muerta: Apple o
	// Google responden 403 y nadie se entera. Se detecta aquí y se rehace.
	if (suscripcion && !mismaLlave(suscripcion, llave)) {
		await suscripcion.unsubscribe().catch(() => {})
		suscripcion = null
	}
	if (!suscripcion) {
		try {
			suscripcion = await registro.pushManager.subscribe({
				userVisibleOnly: true,
				applicationServerKey: llave,
			})
		} catch {
			return 'con-permiso'
		}
	}

	const { endpoint, keys } = suscripcion.toJSON()
	if (!endpoint || !keys?.p256dh || !keys?.auth) return 'con-permiso'
	try {
		const { guardada } = await call(`${METODOS}.guardar_suscripcion`, {
			endpoint,
			p256dh: keys.p256dh,
			auth: keys.auth,
			plataforma: plataforma(),
		})
		return guardada ? 'activos' : 'sin-configurar'
	} catch {
		return 'con-permiso'
	}
}

/**
 * Una sola suscripción a la vez, aunque la pidan tres pantallas juntas.
 *
 * 🚨 No es una optimización, es un arreglo que viene de Wapido (PR #52): tres
 *    componentes suscribían a la vez, los tres veían `getSubscription()` vacío,
 *    y en Chrome quedaron tres dispositivos registrados en 470 ms, dos de ellos
 *    muertos al nacer. El guardia va aquí y no en los componentes, para que
 *    quien llame mañana lo herede sin saber que existe.
 */
let enVuelo = null

export function asegurarSuscripcion() {
	if (!enVuelo) {
		enVuelo = suscribir()
			.then((estado) => {
				estadoPush.value = estado
				return estado
			})
			.finally(() => {
				enVuelo = null
			})
	}
	return enVuelo
}

/**
 * Pedir permiso y dejar el aparato registrado. SOLO desde un toque.
 *
 * El permiso se pide lo primero, sin esperar nada antes: Safari solo lo muestra
 * dentro del gesto de la alumna, y un viaje al servidor de por medio lo gasta.
 * Por eso la configuración tiene que haber llegado antes de pintar el botón.
 */
export async function activarAvisos() {
	if (!soportaPush()) return estadoSinSuscripcion()
	let permiso = Notification.permission
	if (permiso === 'default') {
		try {
			permiso = await Notification.requestPermission()
		} catch {
			permiso = 'denied'
		}
	}
	if (permiso !== 'granted') {
		estadoPush.value = estadoSinSuscripcion()
		return estadoPush.value
	}
	return asegurarSuscripcion()
}

/** El endpoint de este aparato: así se reconoce en la lista, no por el user agent. */
export async function endpointLocal() {
	if (!soportaPush()) return null
	try {
		const registro = await registroListo()
		const suscripcion = await registro.pushManager.getSubscription()
		return suscripcion?.endpoint ?? null
	} catch {
		return null
	}
}

/**
 * Lleva un enlace del servidor (`/lms/...`) a su pantalla, sin recargar.
 *
 * Devuelve false si no es una pantalla de la escuela, y quien llama decide qué
 * hacer. Lo usan el service worker al tocar un aviso con la app abierta y el
 * panel de la campana.
 */
export function navegarDentro(router, enlace) {
	if (!enlace) return false
	let url
	try {
		url = new URL(enlace, window.location.origin)
	} catch {
		return false
	}
	const base = `/${getLmsBasePath()}`
	if (url.origin !== window.location.origin) return false
	if (url.pathname !== base && !url.pathname.startsWith(`${base}/`)) return false
	const destino = router.resolve(
		(url.pathname.slice(base.length) || '/') + url.search + url.hash
	)
	if (!destino.matched.length) return false
	router.push(destino)
	return true
}

function escucharServiceWorker(router) {
	navigator.serviceWorker.addEventListener('message', (evento) => {
		const { type, ruta } = evento.data || {}
		if (type === MENSAJE_AVISO) {
			// El mismo contador de siempre, no uno nuevo.
			getCachedResource('Unread Notifications Count')?.reload()
			if (panelVisible.value) notifications.reload()
		} else if (type === MENSAJE_NAVEGAR) {
			if (!navegarDentro(router, ruta)) window.location.assign(ruta)
		}
	})
}

/**
 * Desde main.js. Con sesión, y si ya dio permiso, vuelve a suscribir en cada
 * arranque: el guardado es un upsert, así que es inofensivo, y así una fila
 * borrada o una suscripción que el navegador renovó se corrigen solas.
 */
export function arrancarAvisosPush(router) {
	if ('serviceWorker' in navigator) escucharServiceWorker(router)
	if (sessionStore().isLoggedIn) refrescarEstadoPush()
}

/** El estado al día. Con permiso ya dado, además vuelve a registrar el aparato. */
export async function refrescarEstadoPush() {
	if (soportaPush() && Notification.permission === 'granted') {
		return asegurarSuscripcion()
	}
	// También sin PushManager: en un iPhone sin instalar hace falta saber si hay
	// avisos para invitarla a instalar la app.
	await configuracionPush.fetch().catch(() => {})
	estadoPush.value = estadoSinSuscripcion()
	return estadoPush.value
}
