<template>
	<!-- Franja de invitación a dejar la reseña. Va en el flujo, arriba del
	     contenido: así nunca tapa nada (ni el menú inferior del móvil) y se va
	     con el scroll, pero vuelve a saludar en cada pantalla de la escuela. -->
	<div
		v-if="visible"
		class="flex shrink-0 items-center gap-2 px-3 py-2 text-white sm:gap-3 sm:px-5"
		:style="{ backgroundColor: 'var(--taar-primary)' }"
	>
		<Sparkles class="hidden size-4 shrink-0 sm:block" />
		<p class="min-w-0 flex-1 text-xs leading-snug sm:text-sm">
			{{
				__('Tell us your experience and get {0}% off').format(
					invitacion.data.porcentaje
				)
			}}
		</p>
		<router-link
			:to="{ name: 'Opinion' }"
			class="shrink-0 whitespace-nowrap rounded-md bg-white px-3 py-1.5 text-xs font-medium text-[#07181f] sm:text-sm"
		>
			{{ __('Write my review') }}
		</router-link>
		<button
			type="button"
			class="grid size-7 shrink-0 place-items-center rounded text-white/80 hover:text-white"
			:aria-label="__('Close')"
			@click="cerrar()"
		>
			<X class="size-4" />
		</button>
	</div>
</template>

<script setup>
import { createResource } from 'frappe-ui'
import { Sparkles, X } from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { sessionStore } from '@/stores/session'

const CLAVE_CERRADA = 'taar-barra-resena-cerrada'

const { isLoggedIn, user } = sessionStore()
const route = useRoute()

// Quién está invitada lo decide el servidor. Misma clave de caché que usa la
// página de la reseña: frappe-ui devuelve el mismo recurso, así que se pregunta
// una vez y al enviar la reseña esta barra se apaga sola.
const invitacion = createResource({
	url: 'taar_lms.api.mi_invitacion_resena',
	auto: isLoggedIn,
	cache: ['invitacion-resena', user],
})

// Cerrarla la calla el resto de la sesión, no para siempre: la idea es no dar
// la lata hoy, pero seguir recordándoselo mientras no haya enviado su reseña.
const cerrada = ref(sessionStorage.getItem(CLAVE_CERRADA) === '1')

const cerrar = () => {
	cerrada.value = true
	sessionStorage.setItem(CLAVE_CERRADA, '1')
}

const visible = computed(
	() =>
		!cerrada.value &&
		// Estando ya en la página de la reseña, invitarla otra vez sobra.
		route.name !== 'Opinion' &&
		invitacion.data?.invitada &&
		!invitacion.data?.ya_enviada
)
</script>
