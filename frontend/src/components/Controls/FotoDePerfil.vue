<template>
	<div class="space-y-1.5">
		<FormLabel v-if="label" :label="__(label)" :required="required" />
		<div class="flex items-start gap-4">
			<div
				class="relative size-24 shrink-0 overflow-hidden rounded-full border bg-surface-gray-2 grid place-items-center"
			>
				<img v-if="modelValue" :src="modelValue" class="size-full object-cover" />
				<Image v-else class="size-5 stroke-1 text-ink-gray-5" />
			</div>
			<div class="flex flex-wrap items-center gap-2">
				<Button :loading="subiendo" @click="elegirArchivo()">
					{{
						subiendo
							? `${__('Uploading')} ${progreso}%`
							: modelValue
							? __('Replace')
							: __('Upload')
					}}
				</Button>
				<!-- Reencuadrar sin volver a subir: la foto que trae del teléfono
				     casi nunca queda centrada dentro del círculo. -->
				<Button v-if="modelValue && !subiendo" @click="ajustarActual()">
					{{ __('Adjust') }}
				</Button>
				<Button
					v-if="modelValue && !subiendo"
					variant="ghost"
					theme="red"
					@click="emit('update:modelValue', '')"
				>
					{{ __('Remove') }}
				</Button>
			</div>
		</div>

		<input
			ref="entrada"
			type="file"
			accept="image/*"
			class="hidden"
			@change="alElegir"
		/>

		<RecortarFoto v-model="recortando" :origen="origen" @listo="alRecortar" />
	</div>
</template>

<script setup>
import { Button, FileUploadHandler, FormLabel, toast } from 'frappe-ui'
import { Image } from 'lucide-vue-next'
import { ref } from 'vue'
import { validateFile } from '@/utils'
import RecortarFoto from '@/components/Modals/RecortarFoto.vue'

const props = defineProps({
	modelValue: { type: String, default: '' },
	label: { type: String, default: '' },
	required: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const entrada = ref(null)
const origen = ref('')
const recortando = ref(false)
const subiendo = ref(false)
const progreso = ref(0)

const elegirArchivo = () => {
	if (entrada.value) entrada.value.value = ''
	entrada.value?.click()
}

const alElegir = async (evento) => {
	const archivo = evento.target.files?.[0]
	if (!archivo) return
	if (await validateFile(archivo, true, 'image')) return
	origen.value = URL.createObjectURL(archivo)
	recortando.value = true
}

const ajustarActual = () => {
	origen.value = props.modelValue
	recortando.value = true
}

const alRecortar = async (blob) => {
	const archivo = new File([blob], 'foto-de-perfil.jpg', { type: 'image/jpeg' })
	subiendo.value = true
	progreso.value = 0

	const subida = new FileUploadHandler()
	subida.on('progress', ({ uploaded, total }) => {
		progreso.value = Math.round((uploaded / total) * 100)
	})

	try {
		const guardado = await subida.upload(archivo, {
			private: false,
			folder: 'Home/Attachments',
			optimize: true,
		})
		emit('update:modelValue', guardado.file_url)
	} catch (error) {
		toast.error(error?.message || __('Error Uploading File'))
	} finally {
		subiendo.value = false
	}
}
</script>
