<template>
	<div ref="raiz" class="relative flex min-h-0 flex-1 flex-col">
		<!-- Arranca escondido debajo de la barra superior (z-30), que lo tapa
		     hasta que el dedo lo saca. -->
		<div
			v-if="activo"
			ref="indicador"
			:role="recargando ? 'status' : undefined"
			:aria-hidden="!recargando"
			class="taar-recarga pointer-events-none absolute left-1/2 top-0 z-20 grid size-9 place-items-center rounded-full border border-outline-gray-2 bg-surface-base text-ink-gray-6 opacity-0 shadow-md"
		>
			<RotateCw
				class="size-4"
				:class="{ 'animate-spin': recargando }"
				:stroke-width="2.25"
			/>
			<span v-if="recargando" class="sr-only">{{ __('Reloading') }}</span>
		</div>
		<slot />
	</div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { RotateCw } from 'lucide-vue-next'
import { esInstalada } from '@/utils/appInstalable'

/**
 * Deslizar hacia abajo para recargar, solo con la app instalada. El mismo de
 * Wapido; las reglas, en docs/navegacion-y-tipografia.md.
 *
 * En una pestaña, Safari y Chrome ya traen el gesto. Al instalar la app
 * desaparece junto con la barra del navegador, y una pantalla atorada se
 * quedaba sin salida. Por eso solo actúa instalada: en la pestaña saldrían dos
 * indicadores.
 *
 * - Recarga la página entera, igual que el gesto del navegador. Refrescar solo
 *   los datos no saca a la app de un error ni trae la versión nueva, que son
 *   justo los casos en que alguien la jala.
 * - El indicador flota; el contenido no se mueve. Un `transform` sobre el
 *   contenido lo haría el contenedor de todo lo `position: fixed` de adentro.
 * - Se decide en el primer movimiento del dedo: iOS no deja cancelar un scroll
 *   que ya empezó.
 * - «Está hasta arriba» no mira `window` sino los contenedores con scroll entre
 *   el dedo y este componente, y eso incluye #scrollContainer, que es donde
 *   vive el scroll de la escuela.
 *
 * El indicador se pinta escribiendo el estilo en el nodo y no con estado de
 * Vue: el dedo manda decenas de eventos por segundo.
 */

/** El indicador avanza la mitad de lo que baja el dedo: se siente con peso. */
const RESISTENCIA = 0.5
/** Recorrido del indicador que dispara la recarga (unos 128 px de dedo). */
const DISPARA = 64
const TOPE = 96
/** Donde se queda el indicador mientras recarga. */
const REPOSO = 56
/** Lo que mide el círculo. */
const LADO = 36

const raiz = ref(null)
const indicador = ref(null)
const recargando = ref(false)
// Se decide una vez: el modo de la app no cambia a mitad de sesión.
const activo = esInstalada()

/** ¿Empezó dentro de algo con scroll propio que no está hasta arriba? */
function dentroDeAlgoDesplazado(objetivo) {
	let el = objetivo instanceof Element ? objetivo : null
	while (el && el !== raiz.value) {
		if (el.scrollTop > 0 && el.scrollHeight > el.clientHeight) {
			const { overflowY } = getComputedStyle(el)
			if (overflowY === 'auto' || overflowY === 'scroll') return true
		}
		el = el.parentElement
	}
	return false
}

let inicioX = 0
let inicioY = 0
let siguiendo = false // el toque empezó donde el gesto aplica
let jalando = false // ya se decidió que es un jalón hacia abajo
let distancia = 0

function pintar(d, animado) {
	const el = indicador.value
	if (!el) return
	const avance = Math.min(1, d / DISPARA)
	el.style.transition = animado
		? 'transform 200ms ease-out, opacity 200ms ease-out'
		: 'none'
	el.style.transform = `translate(-50%, ${d - LADO}px)`
	el.style.opacity = String(avance)
	el.classList.toggle('taar-recarga-lista', d >= DISPARA)
	const icono = el.firstElementChild
	if (icono && !recargando.value) icono.style.transform = `rotate(${avance * 270}deg)`
}

function alEmpezar(e) {
	jalando = false
	siguiendo =
		!recargando.value &&
		e.touches.length === 1 &&
		!dentroDeAlgoDesplazado(e.target)
	if (!siguiendo) return
	inicioX = e.touches[0].clientX
	inicioY = e.touches[0].clientY
}

function alMover(e) {
	if (!siguiendo) return
	const dx = e.touches[0].clientX - inicioX
	const dy = e.touches[0].clientY - inicioY
	if (!jalando) {
		if (dx === 0 && dy === 0) return
		// Hacia arriba o de lado es scroll normal: el gesto se retira hasta el
		// próximo toque.
		if (dy <= 0 || Math.abs(dx) >= dy) {
			siguiendo = false
			return
		}
		jalando = true
	}
	// Frena el rebote de iOS: lo único que se mueve es el indicador.
	if (e.cancelable) e.preventDefault()
	distancia = Math.min(TOPE, Math.max(0, dy) * RESISTENCIA)
	pintar(distancia, false)
}

function alSoltar(e) {
	siguiendo = false
	if (!jalando) return
	jalando = false
	if (e.type === 'touchend' && distancia >= DISPARA) {
		recargando.value = true
		pintar(REPOSO, true)
		// Un respiro para que se alcance a ver el giro antes de descargar la página.
		window.setTimeout(() => window.location.reload(), 150)
	} else {
		pintar(0, true)
	}
	distancia = 0
}

onMounted(() => {
	if (!activo || !raiz.value) return
	pintar(0, false)
	raiz.value.addEventListener('touchstart', alEmpezar, { passive: true })
	// No pasivo: es la única forma de que `preventDefault` frene el rebote.
	raiz.value.addEventListener('touchmove', alMover, { passive: false })
	raiz.value.addEventListener('touchend', alSoltar)
	raiz.value.addEventListener('touchcancel', alSoltar)
})

onUnmounted(() => {
	if (!raiz.value) return
	raiz.value.removeEventListener('touchstart', alEmpezar)
	raiz.value.removeEventListener('touchmove', alMover)
	raiz.value.removeEventListener('touchend', alSoltar)
	raiz.value.removeEventListener('touchcancel', alSoltar)
})
</script>

<style>
.taar-recarga {
	transform: translate(-50%, -2.25rem);
}
.taar-recarga-lista {
	color: var(--taar-nav-icono-activo);
}
</style>
