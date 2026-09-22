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
						class="text-label font-medium uppercase tracking-wide"
						:class="abierta ? 'text-red-700' : 'text-ink-gray-6'"
					>
						{{ abierta ? __('Live now') : __('Next live session') }}
					</span>
				</div>

				<p class="truncate text-heading font-semibold text-ink-gray-9">
					{{ sesion.titulo }}
				</p>

				<!-- La mayúscula va en el párrafo y no en el `span`: `::first-letter`
				     no existe para un elemento en línea. Y es `first-letter` y no
				     `capitalize`, que escribiría «17 De Septiembre». -->
				<p class="mt-0.5 text-support text-ink-gray-7 first-letter:uppercase">
					<span>{{ fechaLarga(sesion) }}</span>
					<span v-if="!abierta" class="text-ink-gray-6">
						· {{ cuantoFalta(sesion) }}
					</span>
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
					class="text-support text-ink-gray-6"
				>
					{{ __('Included in your membership') }}
				</span>

				<!-- Editar y cancelar viven junto a la sesión y no en el escritorio
				     de Frappe: quien la programó desde aquí tiene que poder
				     cambiarla o deshacerla desde aquí, sin aprenderse otra pantalla. -->
				<Button
					v-if="puedeModerar"
					variant="ghost"
					size="md"
					:label="__('Edit session')"
					@click="editando = true"
				>
					<template #icon>
						<Pencil class="size-4" />
					</template>
				</Button>
				<Button
					v-if="puedeModerar"
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

		<!-- Decir que vienes. No abre ninguna puerta: quien no lo pulse verá el
		     botón de entrar igual a su hora. Sirve para saber a cuánta gente
		     esperamos, para el aviso de la última hora, y para que la sesión
		     acabe en su calendario en vez de en su memoria. -->
		<div
			v-if="haySesionIniciada && puedeEntrar && !abierta"
			class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-outline-gray-1 pt-3"
		>
			<Button
				v-if="!apuntada"
				variant="subtle"
				size="sm"
				:loading="apuntarme.loading"
				@click="apuntarse"
			>
				<template #prefix>
					<CalendarPlus class="size-4" />
				</template>
				{{ __("I'm going") }}
			</Button>

			<template v-else>
				<span class="flex items-center gap-1.5 text-support text-ink-gray-7">
					<Check class="size-4 text-ink-gray-6" />
					{{ __("You're signed up") }}
				</span>

				<!-- Fuera de Apple es un enlace directo a Google Calendar. En Apple
				     abre un menú: el calendario del teléfono o Google Calendar,
				     porque el aparato no dice cuál de los dos usa ella. -->
				<Dropdown
					v-if="calendario.opciones"
					:options="calendario.opciones"
					align="start"
				>
					<button
						class="text-support text-ink-gray-7 underline underline-offset-2 hover:text-ink-gray-9"
					>
						{{ __('Add to my calendar') }}
					</button>
				</Dropdown>
				<a
					v-else
					:href="calendario.href"
					target="_blank"
					rel="noopener"
					class="text-support text-ink-gray-7 underline underline-offset-2 hover:text-ink-gray-9"
				>
					{{ __('Add to my calendar') }}
				</a>

				<button
					class="text-support text-ink-gray-6 underline underline-offset-2 hover:text-ink-gray-8"
					:disabled="desapuntarme.loading"
					@click="desapuntarse"
				>
					{{ __("I can't make it") }}
				</button>
			</template>

			<!-- Por debajo de tres no se enseña: «1 persona se ha anotado» dice
			     justo lo contrario de lo que se busca, y encima de la tarjeta
			     más visible del panel. Quien modera lo ve siempre, que para eso
			     es suyo el dato. -->
			<span
				v-if="apuntadas >= 3 || (puedeModerar && apuntadas > 0)"
				class="ml-auto text-label tabular-nums text-ink-gray-6"
			>
				{{ cuantas }}
			</span>
		</div>

		<ProgramarSesionModal v-if="editando" v-model="editando" :original="sesion" />

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
				<p class="text-body text-ink-gray-7">
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
import { Button, Dialog, Dropdown, createResource, toast } from 'frappe-ui'
import { CalendarPlus, Check, Pencil, Trash2, Video } from 'lucide-vue-next'
import { computed, inject, ref, watch } from 'vue'
import ProgramarSesionModal from '@/components/ProgramarSesionModal.vue'
import {
	ahora,
	calendarioDeEsteAparato,
	cuantoFalta,
	estaAbierta,
	fechaLarga,
	refrescarSesiones,
	sesionesEnVivo,
	zonaDelNavegador,
} from '@/utils/envivo'

const props = defineProps({
	sesion: { type: Object, required: true },
	puedeEntrar: { type: Boolean, default: false },
	// Esconder los botones no es la protección: `editar_sesion()` y
	// `cancelar_sesion()` vuelven a comprobar el rol en el servidor. Aquí solo se
	// evita enseñar algo que no lleva a ninguna parte.
	puedeModerar: { type: Boolean, default: false },
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

// El recurso de sesiones se guarda en el navegador, y a un invitado el servidor
// le responde 403 en vez de una respuesta vacía: el `fetch` falla y la tarjeta
// se queda pintada con lo último que hubo. Eso ya enseñaba el título y la hora
// de más, pero «ya estás anotada» es de una persona concreta y no puede quedarse
// en la pantalla de quien viene después en un ordenador prestado.
const usuario = inject('$user', null)
const haySesionIniciada = computed(() => !!usuario?.data)

const calendario = computed(() => calendarioDeEsteAparato(props.sesion))

const apuntada = computed(() => !!props.sesion.apuntada)
const apuntadas = computed(() => props.sesion.apuntadas || 0)

const cuantas = computed(() =>
	apuntadas.value === 1
		? __('1 person has signed up')
		: __('{0} people have signed up').format(apuntadas.value)
)

const apuntarme = createResource({ url: 'taar_lms.envivo.apuntarme' })
const desapuntarme = createResource({ url: 'taar_lms.envivo.desapuntarme' })

/**
 * Apunta el resultado en el recurso compartido en vez de volver a pedirlo.
 *
 * Lo que cambia son dos datos que ya vienen en la respuesta, y `refrescarSesiones()`
 * dejaría el botón muerto el viaje entero para enterarse de algo que ya sabemos.
 * Como la tarjeta del inicio mira este mismo objeto, las dos se enteran a la vez.
 */
function anotarEstado(datos) {
	const sesiones = sesionesEnVivo.data
	if (sesiones?.proxima?.nombre !== props.sesion.nombre) return
	sesiones.proxima.apuntada = datos.apuntada
	sesiones.proxima.apuntadas = datos.cuantas
}

function apuntarse() {
	apuntarme.submit(
		{ nombre: props.sesion.nombre, zona: zonaDelNavegador() },
		{
			onSuccess: anotarEstado,
			onError(err) {
				toast.error(
					err.messages?.[0] || err.message || __('You were not signed up.')
				)
			},
		}
	)
}

function desapuntarse() {
	desapuntarme.submit(
		{ nombre: props.sesion.nombre },
		{
			onSuccess: anotarEstado,
			onError(err) {
				toast.error(err.messages?.[0] || err.message || __('You were not signed up.'))
			},
		}
	)
}

const editando = ref(false)
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
