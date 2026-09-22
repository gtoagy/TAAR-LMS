import { ref } from 'vue'
import { toast } from 'frappe-ui'
import router from '@/router'
import { getLmsBasePath } from '@/utils/basePath'

/**
 * La app instalada: el service worker, el aviso de versión nueva y lo que hace
 * falta para invitar a instalarla. Las reglas, en docs/app-instalable.md.
 *
 * El service worker es el de taar-lms-app, servido en /sw.js, y no cachea nada
 * a propósito. Existe para que la app se pueda instalar y, más adelante, para
 * recibir los avisos con la app cerrada. Como no guarda nada, la escuela
 * siempre carga lo que está publicado.
 *
 * Lo que sí queda viejo es la pantalla abierta: una app instalada no tiene
 * botón de recargar, y corre el código con el que arrancó. De eso se encargan
 * el aviso de versión nueva y el de chunk perdido. Ninguno de los dos recarga
 * por su cuenta: recargar tira lo que la alumna tenga a medias, y aquí eso es
 * un video o un quiz.
 */

/** Cada cuánto se busca versión nueva con la app abierta mucho rato. */
const CADA = 30 * 60 * 1000

const ID_AVISO_VERSION = 'taar-version-nueva'

/** Cómo lo dice cada navegador cuando no encuentra un chunk: Chrome, Safari y Firefox. */
const CHUNK_PERDIDO =
	/Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module|Unable to preload CSS/i

/** True con la app instalada, sin barra del navegador. `standalone` es el de iOS. */
export function esInstalada() {
	return (
		window.navigator.standalone === true ||
		window.matchMedia?.('(display-mode: standalone)').matches === true
	)
}

/** iPhone o iPad. El iPad con iPadOS 13 o más se anuncia como Mac. */
export function esIOS() {
	return (
		/iPad|iPhone|iPod/.test(navigator.userAgent) ||
		(navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
	)
}

/* ── La invitación a instalar ────────────────────────────────────────────────
   Chrome manda `beforeinstallprompt` cuando la app se puede instalar, casi al
   cargar la página y una sola vez. Se escucha aquí, desde main.js, y no en el
   componente: si el componente se monta después, el evento ya pasó. Y hay que
   quedarse con el evento original, porque `prompt()` solo funciona sobre él. */
export const eventoInstalar = ref(null)
export const instalada = ref(false)

function escucharInstalacion() {
	instalada.value = esInstalada()
	window.addEventListener('beforeinstallprompt', (e) => {
		e.preventDefault()
		eventoInstalar.value = e
	})
	window.addEventListener('appinstalled', () => {
		instalada.value = true
		eventoInstalar.value = null
	})
}

/* ── El service worker ──────────────────────────────────────────────────────── */
async function registrarServiceWorker() {
	if (!('serviceWorker' in navigator)) return

	try {
		// El de VitePWA vivía en /assets/lms/frontend/ y con ese scope no
		// controlaba ninguna página: solo guardaba el build. Se da de baja para
		// que no quede nadie cacheando por su cuenta.
		for (const registro of await navigator.serviceWorker.getRegistrations()) {
			if (registro.scope.includes('/assets/lms/frontend/')) registro.unregister()
		}
	} catch {
		// Sin permiso para listarlos (una ventana privada): no pasa nada.
	}

	let registro
	try {
		registro = await navigator.serviceWorker.register('/sw.js', { scope: '/' })
	} catch {
		// Sin service worker la escuela funciona igual; solo no se instala.
		return
	}

	// El propio sw.js también se renueva: al volver al frente y cada rato.
	const revisar = () => registro.update().catch(() => {})
	document.addEventListener('visibilitychange', () => {
		if (document.visibilityState === 'visible') revisar()
	})
	setInterval(revisar, CADA)
}

/* ── El aviso de versión nueva ──────────────────────────────────────────────── */

/**
 * La versión es el nombre del script principal del build: Vite le pone un hash
 * que cambia en cada publicación. La que corre se lee del HTML con el que
 * arrancó la página; la publicada, del HTML que sirve ahora el servidor.
 */
export function versionDelHtml(html) {
	const encontrada =
		/<script[^>]*type="module"[^>]*src="([^"]*\/assets\/index-[^"]+\.js)"/.exec(
			html
		)
	return encontrada?.[1] ?? null
}

function versionEnMarcha() {
	return (
		document
			.querySelector('script[type="module"][src*="/assets/index-"]')
			?.getAttribute('src') ?? null
	)
}

async function versionPublicada() {
	try {
		// `no-store`, para que ninguna caché conteste con lo que ya tenía, que es
		// justo lo que se trata de detectar.
		const r = await fetch(`/${getLmsBasePath()}`, {
			cache: 'no-store',
			credentials: 'same-origin',
		})
		if (!r.ok) return null
		return versionDelHtml(await r.text())
	} catch {
		// Sin red, el aviso simplemente no sale.
		return null
	}
}

/** Un video en pantalla completa, con la del navegador o con la de respaldo de Plyr. */
function hayVideoEnPantallaCompleta() {
	return Boolean(
		document.fullscreenElement ||
			document.webkitFullscreenElement ||
			document.querySelector('.plyr--fullscreen-fallback, .plyr--fullscreen-active')
	)
}

// La versión que la alumna decidió ignorar. Vive en memoria a propósito: si
// recarga, el problema ya se resolvió solo.
let ignorada = null
// Una versión nueva encontrada con el video en pantalla completa: se enseña
// al salir de ella, no encima de la clase.
let pendiente = null
// Adónde iba cuando falló un chunk viejo, para llevarla ahí al actualizar.
let destino = null

function avisarVersionNueva(version) {
	if (hayVideoEnPantallaCompleta()) {
		pendiente = version
		return
	}
	pendiente = null
	toast(__('There is a new version of TanArtistic'), {
		id: ID_AVISO_VERSION,
		description: __('Update when you finish what you are doing.'),
		duration: Infinity,
		action: {
			label: __('Update'),
			onClick: () =>
				destino ? window.location.assign(destino) : window.location.reload(),
		},
		onDismiss: () => {
			ignorada = version
		},
	})
}

function vigilarVersion() {
	const enMarcha = versionEnMarcha()
	// Sin build no hay nada que comparar: pasa con `yarn dev`.
	if (!enMarcha) return

	const revisar = async () => {
		if (document.visibilityState !== 'visible') return
		const publicada = await versionPublicada()
		if (!publicada || publicada === enMarcha || publicada === ignorada) return
		avisarVersionNueva(publicada)
	}

	document.addEventListener('visibilitychange', () => {
		if (document.visibilityState === 'visible') revisar()
	})
	setInterval(revisar, CADA)

	const alSalirDePantallaCompleta = () => {
		if (pendiente && !hayVideoEnPantallaCompleta()) avisarVersionNueva(pendiente)
	}
	document.addEventListener('fullscreenchange', alSalirDePantallaCompleta)
	document.addEventListener('webkitfullscreenchange', alSalirDePantallaCompleta)
}

function vigilarChunksPerdidos() {
	/* Un chunk que ya no existe. Pasa si se publicó con la app abierta y ella
	   abre una pantalla que todavía no había visitado: el código viejo pide un
	   archivo del build anterior y el servidor ya no lo tiene. Vite lo avisa con
	   `vite:preloadError`; se deja que el error siga (la navegación falla y se
	   queda donde estaba, en vez de pintar una pantalla en blanco) y se ofrece
	   actualizar. El router dice adónde iba, y es ahí donde la lleva el botón. */
	window.addEventListener('vite:preloadError', () => avisarVersionNueva(null))
	router.onError((error, to) => {
		if (to && CHUNK_PERDIDO.test(String(error?.message))) {
			destino = router.resolve(to).href
		}
	})
}

/** Una sola vez, desde main.js. */
export function arrancarAppInstalable() {
	escucharInstalacion()
	vigilarVersion()
	vigilarChunksPerdidos()
	// Después de `load`, para no competir con el arranque de la escuela.
	if (document.readyState === 'complete') registrarServiceWorker()
	else window.addEventListener('load', registrarServiceWorker, { once: true })
}
