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
			<Button
				variant="solid"
				:label="archivoListo ? __('Save file') : __('Download')"
				:loading="descargando"
				@click="descargar"
			>
				<template #prefix>
					<span class="lucide-download size-4" />
				</template>
			</Button>
		</div>

		<p v-if="fallo" class="mt-2 text-p-sm text-ink-red-6">
			{{ __('The file could not be downloaded. Please try again.') }}
		</p>

		<!-- El visor incrustado solo donde se puede usar de verdad. En un móvil
		     el navegador mete su propio lector dentro del marco y queda un
		     recuadro que no se deja ampliar ni desplazar; ahí vale más el botón
		     de arriba, que entrega el archivo sin sacar a nadie de la lección. -->
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
import { computed, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { entregarArchivo, traerArchivo } from '@/utils/descargar'

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

const descargando = ref(false)
const fallo = ref(false)
// El archivo ya bajado se guarda: si el teléfono pide un segundo toque para
// abrir la hoja de compartir, ese toque no vuelve a descargar nada.
const archivo = shallowRef(null)
const archivoListo = ref(false)

const descargar = async () => {
	if (descargando.value) return
	fallo.value = false
	try {
		if (!archivo.value) {
			descargando.value = true
			archivo.value = await traerArchivo(url.value, nombre.value)
		}
		const resultado = await entregarArchivo(archivo.value)
		archivoListo.value = resultado === 'pendiente'
	} catch (error) {
		console.error(error)
		fallo.value = true
	} finally {
		descargando.value = false
	}
}

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
