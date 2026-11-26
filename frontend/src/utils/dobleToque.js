// Doble toque a los lados del vídeo para saltar 10 s, como en YouTube.
//
// Plyr no lo trae, y con Vimeo hay un obstáculo: el iframe se traga los
// toques y la página nunca se entera. Por eso se ponen dos franjas
// transparentes encima de los costados; el centro sigue siendo del iframe.
//
// Las franjas solo aparecen en pantallas táctiles (CSS, pointer: coarse) y
// solo después de que el vídeo arrancó la primera vez: antes, el primer toque
// tiene que llegar al iframe para que el iPhone deje reproducir.

export const SALTO_SEGUNDOS = 10

// Tiempo máximo entre dos toques para que cuenten como doble toque, y para
// seguir sumando 10 s más con cada toque suelto una vez arrancada la racha.
const ENTRE_TOQUES_MS = 350
const RACHA_MS = 800
const BURBUJA_MS = 700

/**
 * Lleva la cuenta de los toques. Devuelve, por cada toque, cuántos segundos
 * acumulados hay que mostrar (0 si ese toque todavía no salta).
 */
export const crearContadorDeToques = () => {
	let zona = null
	let ultimo = -Infinity
	let acumulado = 0

	return (zonaTocada, ahora) => {
		const ventana = acumulado > 0 ? RACHA_MS : ENTRE_TOQUES_MS
		const sigue = zonaTocada === zona && ahora - ultimo < ventana
		zona = zonaTocada
		ultimo = ahora
		if (!sigue) {
			acumulado = 0
			return 0
		}
		acumulado += SALTO_SEGUNDOS
		return acumulado
	}
}

/**
 * @param {import('plyr')} player
 * @param {{ puedeAdelantar: () => boolean }} opciones
 */
export const activarDobleToque = (player, { puedeAdelantar }) => {
	const wrapper = player.elements?.wrapper
	const container = player.elements?.container
	if (!wrapper || !container || wrapper.querySelector('.taar-toque')) return

	const tocar = crearContadorDeToques()

	const crearZona = (zona) => {
		const el = document.createElement('div')
		el.className = `taar-toque taar-toque--${zona}`
		el.setAttribute('aria-hidden', 'true')
		const burbuja = document.createElement('span')
		burbuja.className = 'taar-toque__burbuja'
		el.appendChild(burbuja)

		let ocultar = null
		el.addEventListener('click', () => {
			const segundos = tocar(zona, Date.now())
			if (!segundos) return
			if (zona === 'adelante' && !puedeAdelantar()) return

			// Igual que los botones de Plyr: así no esconde los controles justo
			// después del salto.
			player.lastSeekTime = Date.now()
			if (zona === 'atras') player.rewind(SALTO_SEGUNDOS)
			else player.forward(SALTO_SEGUNDOS)

			burbuja.textContent =
				zona === 'atras' ? `« ${segundos} s` : `${segundos} s »`
			el.classList.add('taar-toque--visible')
			clearTimeout(ocultar)
			ocultar = setTimeout(
				() => el.classList.remove('taar-toque--visible'),
				BURBUJA_MS
			)
		})
		wrapper.appendChild(el)
	}

	crearZona('atras')
	crearZona('adelante')

	player.on('playing', () => container.classList.add('taar-toque-listo'))
}
