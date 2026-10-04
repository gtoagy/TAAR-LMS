<template>
	<!-- Quien no ha entrado lo ve en todas las pantallas del móvil. «Iniciar
	     sesión» vivía dentro de «Más», y la alumna que llegaba sin sesión veía
	     el catálogo con candados sin enterarse de por qué. Va fuera del área de
	     scroll: no se va al bajar ni se monta sobre las cabeceras fijas de las
	     pantallas. -->
	<div
		v-if="!session.isLoggedIn"
		class="taar-sin-sesion flex shrink-0 items-center gap-3 border-b border-outline-gray-1 px-4 py-2"
	>
		<p class="min-w-0 flex-1 text-support text-ink-gray-8">
			<span class="font-medium text-ink-gray-9">
				{{ __('Already have an account?') }}
			</span>
			{{ __('Log in to see your courses.') }}
		</p>
		<Button variant="solid" size="md" class="shrink-0" @click="entrar">
			<template #prefix>
				<LogIn class="size-4" aria-hidden="true" />
			</template>
			{{ __('Log in') }}
		</Button>
	</div>
</template>

<script setup>
import { Button } from 'frappe-ui'
import { LogIn } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'

// El store entero: desestructurado, `isLoggedIn` se queda congelado (App.vue).
const session = sessionStore()

/** Al entrar vuelve a la pantalla donde estaba, no al inicio. */
function entrar() {
	const aqui = window.location.pathname + window.location.search
	window.location.href = `/login?redirect-to=${encodeURIComponent(aqui)}`
}
</script>

<style>
.taar-sin-sesion {
	background: rgb(128 127 236 / 0.08);
}
</style>
