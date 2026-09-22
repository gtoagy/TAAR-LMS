<template>
	<div
		class="relative flex h-screen-dvh flex-col pt-[env(safe-area-inset-top)]"
	>
		<!-- El área de scroll llega hasta abajo y la píldora flota encima; el
		     hueco de abajo (--nav-safe) es para que la última tarjeta no quede
		     detrás de ella. -->
		<div
			class="flex min-h-0 flex-1 flex-col overflow-y-auto pb-[var(--nav-safe)]"
			id="scrollContainer"
		>
			<slot />
		</div>

		<BarraMovil />
	</div>
</template>
<script setup>
import BarraMovil from '@/components/Layouts/BarraMovil.vue'
</script>
