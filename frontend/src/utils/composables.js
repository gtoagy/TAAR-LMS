import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'

// Un teléfono girado sigue siendo un teléfono, pero `innerWidth` no lo sabe: en
// horizontal un móvil mide unos 850px y cruzaba el umbral, así que la aplicación
// cambiaba de layout a media sesión. Y cambiar de layout no es cosa de estilos:
// Vue tira la vista entera y la vuelve a montar, con lo que el vídeo que se
// estuviera viendo se recargaba desde el segundo cero y se salía de la pantalla
// completa.
//
// El lado corto de la pantalla no cambia al girar: en un teléfono siempre queda
// por debajo del umbral y en una tableta (768) siempre por encima. Se comprueba
// una sola vez, porque el aparato no cambia a mitad de sesión.
let esTelefonoCache = null
const esTelefono = () => {
	if (esTelefonoCache === null) {
		const dedo = window.matchMedia?.('(pointer: coarse)')?.matches
		const ladoCorto = Math.min(
			window.screen?.width ?? Infinity,
			window.screen?.height ?? Infinity
		)
		esTelefonoCache = Boolean(dedo) && ladoCorto < 640
	}
	return esTelefonoCache
}

export function useScreenSize() {
	const size = reactive({
		width: window.innerWidth,
		height: window.innerHeight,
	})

	const enTelefono = esTelefono()

	// La ventana estrecha sigue contando, para que en el ordenador se pueda
	// probar la vista móvil encogiendo el navegador.
	const isMobile = computed(() => enTelefono || size.width < 640)

	const onResize = () => {
		size.width = window.innerWidth
		size.height = window.innerHeight
	}

	onMounted(() => {
		window.addEventListener('resize', onResize)
	})

	onUnmounted(() => {
		window.removeEventListener('resize', onResize)
	})

	return {
		size,
		isMobile,
	}
}
export function useSwipe() {
	const swipe = reactive({
		initialX: null,
		initialY: null,
		currentX: null,
		currentY: null,
		diffX: null,
		diffY: null,
		absDiffX: null,
		absDiffY: null,
		direction: null,
	})

	const onTouchStart = (e) => {
		swipe.initialX = e.touches[0].clientX
		swipe.initialY = e.touches[0].clientY
		swipe.direction = null
		swipe.diffX = null
		swipe.diffY = null
		swipe.absDiffX = null
		swipe.absDiffY = null
	}

	const onTouchMove = (e) => {
		swipe.currentX = e.touches[0].clientX
		swipe.currentY = e.touches[0].clientY

		swipe.diffX = swipe.initialX - swipe.currentX
		swipe.diffY = swipe.initialY - swipe.currentY

		swipe.absDiffX = Math.abs(swipe.diffX)
		swipe.absDiffY = Math.abs(swipe.diffY)
	}

	const onTouchEnd = (e) => {
		let { diffX, diffY, absDiffX, absDiffY } = swipe
		if (absDiffX > absDiffY) {
			if (diffX > 0) {
				swipe.direction = 'left'
			} else {
				swipe.direction = 'right'
			}
		} else {
			if (diffY > 0) {
				swipe.direction = 'up'
			} else {
				swipe.direction = 'down'
			}
		}
	}

	onMounted(() => {
		window.addEventListener('touchstart', onTouchStart)
		window.addEventListener('touchend', onTouchEnd)
		window.addEventListener('touchmove', onTouchMove)
	})

	onUnmounted(() => {
		window.removeEventListener('touchstart', onTouchStart)
		window.removeEventListener('touchend', onTouchEnd)
		window.removeEventListener('touchmove', onTouchMove)
	})

	return swipe
}

export function useLocalStorage(key, initialValue) {
	let value = ref(null)
	let storedValue = localStorage.getItem(key)
	value.value = storedValue ? JSON.parse(storedValue) : initialValue

	watch(value, (newValue) => {
		localStorage.setItem(key, JSON.stringify(newValue))
	})
	return value
}
