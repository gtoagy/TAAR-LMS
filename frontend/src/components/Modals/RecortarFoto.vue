<template>
	<Dialog v-model="abierto" :options="{ title: __('Adjust your photo'), size: 'md' }">
		<template #body-content>
			<p class="mb-4 text-p-sm text-ink-gray-6">
				{{ __('Drag the photo to center it and use the slider to zoom.') }}
			</p>
			<div
				ref="marco"
				class="relative mx-auto touch-none select-none overflow-hidden rounded-full border bg-surface-gray-3"
				:style="{ width: `${LADO}px`, height: `${LADO}px` }"
				@mousedown="empezar"
				@touchstart="empezar"
			>
				<img
					v-if="origen"
					:src="origen"
					alt=""
					class="absolute origin-top-left max-w-none"
					:style="estiloImagen"
					draggable="false"
					@load="alCargar"
				/>
			</div>

			<!-- Los dos iconos ocupan lo mismo aunque se dibujen a distinto
			     tamaño; si no, la barra queda corrida hacia el pequeño. -->
			<div class="mt-5 flex items-center gap-3">
				<span class="grid w-6 shrink-0 place-items-center">
					<span class="lucide-image size-4 text-ink-gray-5" />
				</span>
				<!-- Barra con tirador de verdad: el control del navegador se queda
				     en 4 px de alto y con el dedo no hay quien lo agarre. -->
				<input
					v-model.number="zoom"
					type="range"
					min="1"
					max="4"
					step="0.01"
					class="barra-zoom w-full cursor-pointer"
				/>
				<span class="grid w-6 shrink-0 place-items-center">
					<span class="lucide-image size-6 text-ink-gray-5" />
				</span>
			</div>
		</template>

		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="abierto = false">{{ __('Cancel') }}</Button>
				<Button variant="solid" :disabled="!listaLaImagen" @click="recortar()">
					{{ __('Use this photo') }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { Button, Dialog } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

// Lado del recorte que se guarda. 512 basta de sobra para un avatar y deja el
// archivo ligero.
const SALIDA = 512
// Lado de la ventana de recorte en pantalla.
const LADO = 260

const abierto = defineModel({ type: Boolean })
const props = defineProps({
	origen: { type: String, default: '' },
})
const emit = defineEmits(['listo'])

const marco = ref(null)
const zoom = ref(1)
const dx = ref(0)
const dy = ref(0)
const anchoNatural = ref(0)
const altoNatural = ref(0)
const listaLaImagen = ref(false)

// Escala mínima para que la foto cubra el círculo entero: por debajo se verían
// huecos, y un avatar con esquinas vacías es peor que uno mal encuadrado.
const escalaBase = computed(() => {
	if (!anchoNatural.value || !altoNatural.value) return 1
	return Math.max(LADO / anchoNatural.value, LADO / altoNatural.value)
})

const escala = computed(() => escalaBase.value * zoom.value)
const anchoVisible = computed(() => anchoNatural.value * escala.value)
const altoVisible = computed(() => altoNatural.value * escala.value)

// Esquina de la imagen dentro del marco, ya centrada y con el arrastre encima.
const izquierda = computed(() => (LADO - anchoVisible.value) / 2 + dx.value)
const arriba = computed(() => (LADO - altoVisible.value) / 2 + dy.value)

const estiloImagen = computed(() => ({
	width: `${anchoVisible.value}px`,
	height: `${altoVisible.value}px`,
	transform: `translate(${izquierda.value}px, ${arriba.value}px)`,
}))

const alCargar = (evento) => {
	anchoNatural.value = evento.target.naturalWidth
	altoNatural.value = evento.target.naturalHeight
	listaLaImagen.value = true
	ajustarDentro()
}

// Que no se pueda arrastrar hasta dejar el círculo a medio llenar.
const ajustarDentro = () => {
	const margenX = Math.max(0, (anchoVisible.value - LADO) / 2)
	const margenY = Math.max(0, (altoVisible.value - LADO) / 2)
	dx.value = Math.min(margenX, Math.max(-margenX, dx.value))
	dy.value = Math.min(margenY, Math.max(-margenY, dy.value))
}

watch(zoom, ajustarDentro)

watch(abierto, (visible) => {
	if (!visible) return
	zoom.value = 1
	dx.value = 0
	dy.value = 0
	listaLaImagen.value = false
})

const punto = (evento) =>
	evento.touches?.length
		? { x: evento.touches[0].clientX, y: evento.touches[0].clientY }
		: { x: evento.clientX, y: evento.clientY }

const empezar = (evento) => {
	if (!listaLaImagen.value) return
	evento.preventDefault()
	const inicio = punto(evento)
	const dx0 = dx.value
	const dy0 = dy.value

	const mover = (e) => {
		const actual = punto(e)
		dx.value = dx0 + (actual.x - inicio.x)
		dy.value = dy0 + (actual.y - inicio.y)
		ajustarDentro()
	}
	const soltar = () => {
		window.removeEventListener('mousemove', mover)
		window.removeEventListener('mouseup', soltar)
		window.removeEventListener('touchmove', mover)
		window.removeEventListener('touchend', soltar)
	}

	window.addEventListener('mousemove', mover)
	window.addEventListener('mouseup', soltar)
	window.addEventListener('touchmove', mover, { passive: false })
	window.addEventListener('touchend', soltar)
}

const recortar = () => {
	const imagen = marco.value?.querySelector('img')
	if (!imagen) return

	// Lo que se ve del marco, traducido a coordenadas de la foto original.
	const lado = LADO / escala.value
	const sx = -izquierda.value / escala.value
	const sy = -arriba.value / escala.value

	const lienzo = document.createElement('canvas')
	lienzo.width = SALIDA
	lienzo.height = SALIDA
	const pincel = lienzo.getContext('2d')
	pincel.fillStyle = '#ffffff'
	pincel.fillRect(0, 0, SALIDA, SALIDA)
	pincel.drawImage(imagen, sx, sy, lado, lado, 0, 0, SALIDA, SALIDA)

	lienzo.toBlob(
		(blob) => {
			if (blob) emit('listo', blob)
			abierto.value = false
		},
		'image/jpeg',
		0.92
	)
}
</script>

<style scoped>
.barra-zoom {
	-webkit-appearance: none;
	appearance: none;
	/* Los controles de rango traen un ancho propio del navegador que le gana a
	   las utilidades; sin esto la barra se queda en 150 px y descentrada. */
	flex: 1 1 auto;
	width: 100%;
	min-width: 0;
	height: 20px;
	background: transparent;
}

.barra-zoom::-webkit-slider-runnable-track {
	height: 6px;
	border-radius: 999px;
	background: var(--surface-gray-4);
}

.barra-zoom::-webkit-slider-thumb {
	-webkit-appearance: none;
	margin-top: -6px;
	height: 18px;
	width: 18px;
	border-radius: 999px;
	border: 2px solid white;
	background: var(--surface-gray-7);
	box-shadow: 0 1px 2px rgb(0 0 0 / 0.2);
}

.barra-zoom::-moz-range-track {
	height: 6px;
	border-radius: 999px;
	background: var(--surface-gray-4);
}

.barra-zoom::-moz-range-thumb {
	height: 18px;
	width: 18px;
	border-radius: 999px;
	border: 2px solid white;
	background: var(--surface-gray-7);
}
</style>
