<template>
	<div class="mb-4">
		<div
			class="flex items-center gap-3 rounded-lg border border-outline-gray-2 bg-surface-base p-3"
			:class="mostrarVisor ? 'rounded-b-none border-b-0' : ''"
		>
			<span
				class="grid size-10 shrink-0 place-items-center rounded-md bg-surface-gray-2"
			>
				<span class="lucide-file-text size-5 text-ink-gray-7" />
			</span>
			<div class="min-w-0 flex-1">
				<div class="truncate text-p-base font-medium text-ink-gray-9">
					{{ nombre }}
				</div>
				<div class="text-p-sm text-ink-gray-5">PDF</div>
			</div>
			<a :href="url" :download="nombre" target="_blank" rel="noopener">
				<Button variant="solid" :label="__('Download')">
					<template #prefix>
						<span class="lucide-download size-4" />
					</template>
				</Button>
			</a>
		</div>

		<!-- El visor incrustado solo donde se puede usar de verdad. En un móvil
		     el navegador mete su propio lector dentro del marco y queda un
		     recuadro que no se deja ampliar ni desplazar; ahí vale más el botón
		     de arriba, que lo abre en el lector del teléfono. -->
		<iframe
			v-if="mostrarVisor"
			:src="url"
			type="application/pdf"
			class="h-[700px] w-full rounded-b-lg border border-outline-gray-2"
		/>
	</div>
</template>

<script setup>
import { Button } from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
	file: {
		type: String,
		required: true,
	},
})

const url = computed(() => encodeURI(props.file))

const nombre = computed(() => {
	const trozo = decodeURIComponent(props.file).split('/').pop() || 'archivo.pdf'
	return trozo.split('?')[0]
})

// Se mira el ancho a mano y no con el composable de la aplicación porque este
// bloque lo monta el editor con su propia instancia de Vue, fuera del árbol
// principal.
const anchoSuficiente = ref(false)
let consulta

const apuntar = (evento) => {
	anchoSuficiente.value = evento.matches
}

onMounted(() => {
	consulta = window.matchMedia('(min-width: 768px)')
	anchoSuficiente.value = consulta.matches
	consulta.addEventListener('change', apuntar)
})

onBeforeUnmount(() => {
	consulta?.removeEventListener('change', apuntar)
})

const mostrarVisor = computed(() => anchoSuficiente.value)
</script>
