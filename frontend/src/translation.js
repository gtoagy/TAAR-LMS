import { ref } from 'vue'
import { createResource } from 'frappe-ui'

/**
 * Las traducciones llegan por red, y antes llegaban con la escuela ya pintada.
 * `window.translatedMessages` no es reactivo, así que lo que se pintaba en
 * inglés se quedaba en inglés hasta que otra cosa obligara a repintar ese
 * componente: el botón de la invitación a instalar decía «Install» al lado de
 * su frase ya en español. Dos arreglos, y hacen falta los dos:
 * - main.js espera a `traduccionesListas()` antes de montar, con un tope.
 * - `__()` lee `version`: lo que alcance a pintarse antes (red lenta, el tope)
 *   se repinta solo cuando llegan.
 */
const version = ref(0)

/** Cuánto se espera a las traducciones antes de pintar sin ellas. */
const TOPE = 3000

export default function translationPlugin(app) {
	app.config.globalProperties.__ = translate
	window.__ = translate
}

function translate(message) {
	version.value
	let translatedMessages = window.translatedMessages || {}
	let translatedMessage = translatedMessages[message] || message

	const hasPlaceholders = /{\d+}/.test(message)
	if (!hasPlaceholders) {
		return translatedMessage
	}
	return {
		format: function (...args) {
			return translatedMessage.replace(
				/{(\d+)}/g,
				function (match, number) {
					return typeof args[number] != 'undefined'
						? args[number]
						: match
				}
			)
		},
	}
}

/** Se resuelve cuando llegan las traducciones, cuando fallan o al pasar el tope. */
export function traduccionesListas() {
	if (window.translatedMessages) return Promise.resolve()
	return new Promise((resolve) => {
		setTimeout(resolve, TOPE)
		createResource({
			url: 'lms.lms.api.get_translations',
			cache: 'translations',
			auto: true,
			transform: (data) => {
				window.translatedMessages = data
				version.value++
				resolve()
			},
			onError: resolve,
		})
	})
}
