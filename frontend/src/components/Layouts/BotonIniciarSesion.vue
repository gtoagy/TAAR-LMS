<template>
	<!-- Solo para quien no ha entrado. «Iniciar sesión» vivía dentro de «Más» y
	     la alumna que llegaba sin sesión veía el catálogo con candados sin
	     enterarse de por qué. Va arriba a la derecha, donde iría su campana: en
	     la barra superior del móvil y en la cabecera de las pantallas que no la
	     llevan (la ficha del curso). -->
	<Button
		v-if="!session.isLoggedIn"
		variant="solid"
		size="md"
		class="shrink-0"
		@click="entrar"
	>
		{{ __('Log in') }}
	</Button>
</template>

<script setup>
import { Button } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

// El store entero: desestructurado, `isLoggedIn` se queda congelado (App.vue).
const session = sessionStore()

/** Al entrar vuelve a la pantalla donde estaba, no al inicio. */
function entrar() {
	const aqui = window.location.pathname + window.location.search
	window.location.href = `/login?redirect-to=${encodeURIComponent(aqui)}`
}
</script>
