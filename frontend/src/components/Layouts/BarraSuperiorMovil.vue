<template>
	<!-- La barra superior del móvil, con el único <h1> de la pantalla. El título
	     sale de la ruta (useTituloMovil) y las pantallas no lo repiten: su
	     cabecera se queda con el subtítulo y las acciones. Solo va en las
	     pantallas de PANTALLAS_CON_BARRA; en las demás no se pinta nada. -->
	<header
		v-if="titulo"
		class="relative z-30 flex h-[var(--topbar-h)] shrink-0 items-center justify-center border-b border-outline-gray-1 bg-surface-base px-4"
	>
		<h1 class="truncate text-heading font-semibold text-ink-gray-9">
			{{ titulo }}
		</h1>
	</header>
</template>

<script setup>
import { useTituloMovil } from '@/utils/navegacionMovil'

const { titulo } = useTituloMovil()
</script>
