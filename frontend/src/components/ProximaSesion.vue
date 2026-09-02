<template>
	<div
		class="rounded-lg border p-4 sm:p-5"
		:class="
			abierta
				? 'border-red-300 bg-red-50'
				: 'border-outline-gray-2 bg-surface-base'
		"
	>
		<div class="flex flex-wrap items-start justify-between gap-3">
			<div class="min-w-0">
				<div class="mb-1 flex items-center gap-2">
					<span
						v-if="abierta"
						class="size-2 shrink-0 animate-pulse rounded-full bg-red-500"
					/>
					<Video v-else class="size-4 shrink-0 text-ink-gray-5" />
					<span
						class="text-xs font-medium uppercase tracking-wide"
						:class="abierta ? 'text-red-700' : 'text-ink-gray-5'"
					>
						{{ abierta ? __('Live now') : __('Next live session') }}
					</span>
				</div>

				<p class="truncate text-base font-medium text-ink-gray-9">
					{{ sesion.titulo }}
				</p>

				<!-- La mayúscula va en el párrafo y no en el `span`: `::first-letter`
				     no existe para un elemento en línea. Y es `first-letter` y no
				     `capitalize`, que escribiría «17 De Septiembre». -->
				<p class="mt-0.5 text-sm text-ink-gray-7 first-letter:uppercase">
					<span>{{ fechaLarga(sesion) }}</span>
					<span v-if="!abierta" class="text-ink-gray-5">
						· {{ cuantoFalta(sesion) }}
					</span>
				</p>

				<p v-if="sesion.descripcion" class="mt-2 text-sm text-ink-gray-7">
					{{ sesion.descripcion }}
				</p>
			</div>

			<div class="flex shrink-0 items-center gap-2">
				<!-- El botón solo existe si el servidor mandó el enlace. No se pinta uno
				     apagado «por si acaso»: un botón que no lleva a ninguna parte se
				     acaba pulsando igual. -->
				<Button v-if="sesion.entrar" variant="solid" size="md" @click="entrar">
					{{ __('Join the session') }}
				</Button>
				<span
					v-else-if="abierta && !puedeEntrar"
					class="text-sm text-ink-gray-6"
				>
					{{ __('Included in your membership') }}
				</span>

				<!-- Cancelar vive junto a la sesión y no en el escritorio de Frappe:
				     quien la programó desde aquí tiene que poder deshacerlo desde
				     aquí, sin aprenderse otra pantalla. -->
				<Button
					v-if="puedeCancelar"
					variant="ghost"
					size="md"
					:label="__('Cancel session')"
					@click="confirmando = true"
				>
					<template #icon>
						<Trash2 class="size-4" />
					</template>
				</Button>
			</div>
		</div>

		<!-- Se pregunta antes porque esto no se deshace, y porque lo que se borra
		     no está solo aquí: la reunión de Zoom desaparece con ella. -->
		<Dialog
			v-model:open="confirmando"
			:title="__('Cancel this session?')"
			:actions="[
				{
					label: __('Cancel session'),
					variant: 'solid',
					theme: 'red',
					loading: cancelarSesion.loading,
					onClick: ({ close }) => cancelar(close),
				},
			]"
		>
			<template #default>
				<p class="text-base text-ink-gray-7">
					{{
						__(
							'The Zoom meeting is deleted too, so a link someone already saved stops working. This cannot be undone.'
						)
					}}
				</p>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { Button, Dialog, createResource, toast } from 'frappe-ui'
import { Trash2, Video } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import {
	ahora,
	cuantoFalta,
	estaAbierta,
	fechaLarga,
	refrescarSesiones,
} from '@/utils/envivo'

const props = defineProps({
	sesion: { type: Object, required: true },
	puedeEntrar: { type: Boolean, default: false },
	// Esconder el botón no es la protección: `cancelar_sesion()` vuelve a
	// comprobar el rol en el servidor. Aquí solo se evita enseñar algo que no
	// lleva a ninguna parte.
	puedeCancelar: { type: Boolean, default: false },
})

const abierta = computed(() => estaAbierta(props.sesion, ahora.value))

// Al cruzar la hora hay que volver a preguntar: la respuesta que tenemos se
// pidió cuando todavía no tocaba, así que viene sin enlace por muy abierta que
// esté ahora la sesión.
watch(abierta, (ahoraAbierta) => {
	if (ahoraAbierta && !props.sesion.entrar) refrescarSesiones()
})

const entrar = () => {
	window.open(props.sesion.entrar, '_blank', 'noopener')
}

const confirmando = ref(false)

const cancelarSesion = createResource({
	url: 'taar_lms.envivo.cancelar_sesion',
})

function cancelar(close) {
	cancelarSesion.submit(
		{ nombre: props.sesion.nombre },
		{
			onSuccess() {
				refrescarSesiones()
				toast.success(__('Session cancelled.'))
				close()
			},
			onError(err) {
				toast.error(
					err.messages?.[0] || err.message || __('The session was not cancelled.')
				)
			},
		}
	)
}
</script>
