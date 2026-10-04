<template>
	<SkeletonLoader v-if="isLoading" variant="header" />
	<header
		v-else
		class="sticky top-0 z-10 flex items-center justify-between gap-2 border-b bg-surface-base px-3 py-2.5 sm:px-5"
	>
		<div class="flex min-w-0 items-center gap-2">
			<slot name="left-header" />
		</div>
		<div class="flex shrink-0 items-center gap-2">
			<slot name="right-header" />
			<!-- Las pantallas con esta cabecera no llevan la barra superior del
			     móvil, que es donde sale este botón en las demás. -->
			<BotonIniciarSesion v-if="isMobile" />
		</div>
	</header>
</template>

<script setup lang="ts">
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import BotonIniciarSesion from '@/components/Layouts/BotonIniciarSesion.vue'
import { useScreenSize } from '@/utils/composables'

const { isMobile } = useScreenSize()

withDefaults(defineProps<{ isLoading?: boolean }>(), {
	isLoading: false,
})
</script>
