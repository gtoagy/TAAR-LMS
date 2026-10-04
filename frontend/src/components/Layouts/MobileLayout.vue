<template>
	<div
		class="relative flex h-screen-dvh flex-col pt-[env(safe-area-inset-top)]"
	>
		<BarraSuperiorMovil />

		<!-- El área de scroll llega hasta abajo y la píldora flota encima; el
		     hueco de abajo (--nav-safe) es para que la última tarjeta no quede
		     detrás de ella. Deslizar hacia abajo recarga, solo con la app
		     instalada: sin barra del navegador no hay otro botón de recargar. -->
		<DeslizarParaRecargar>
			<div
				class="taar-area-scroll flex min-h-0 flex-1 flex-col overflow-y-auto pb-[var(--nav-safe)]"
				id="scrollContainer"
			>
				<slot />
			</div>
		</DeslizarParaRecargar>

		<BarraMovil />
	</div>
</template>
<script setup>
import BarraMovil from '@/components/Layouts/BarraMovil.vue'
import BarraSuperiorMovil from '@/components/Layouts/BarraSuperiorMovil.vue'
import DeslizarParaRecargar from '@/components/Layouts/DeslizarParaRecargar.vue'
</script>

<style>
/*
 * Una pantalla con `h-full` en la raíz mide lo mismo que el área de scroll, y si
 * su contenido es más largo se desborda de esa caja: el hueco reservado para la
 * píldora (--nav-safe) queda en medio y el final de la pantalla, detrás de
 * ella. Pasaba en Membresía. Aquí la pantalla llena el alto que haya y crece
 * con su contenido, así el hueco queda siempre al final.
 */
.taar-area-scroll > .h-full {
	height: auto;
	flex: 1 0 auto;
}
</style>
