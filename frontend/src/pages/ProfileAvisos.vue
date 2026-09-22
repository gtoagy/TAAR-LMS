<template>
	<!-- Solo en el perfil propio: nadie ve los aparatos de otra. El servidor lo
	     vuelve a comprobar (mis_dispositivos filtra por la sesión). -->
	<div v-if="esPropio" class="mb-10 mt-7 space-y-8">
		<section>
			<h2 class="mb-1 text-heading font-semibold text-ink-gray-9">
				{{ __('Notifications on your phone') }}
			</h2>
			<p class="text-support text-ink-gray-7">
				{{
					__(
						'They arrive even with TanArtistic closed: when someone replies to you in a lesson, when someone mentions you, when your teacher comments on your assignment, and an hour before a live session you signed up for.'
					)
				}}
			</p>

			<!-- Este aparato, el que tiene en la mano. -->
			<div
				class="mt-4 flex flex-wrap items-center gap-x-3 gap-y-2 rounded-lg border border-outline-gray-2 px-4 py-3"
			>
				<component :is="estado.icono" class="size-5 shrink-0 text-ink-gray-6" aria-hidden="true" />
				<div class="min-w-0 flex-1">
					<p class="text-body font-medium text-ink-gray-9">{{ estado.titulo }}</p>
					<p v-if="estado.detalle" class="mt-0.5 text-support text-ink-gray-7">
						{{ estado.detalle }}
					</p>
				</div>
				<Button
					v-if="estado.boton"
					variant="solid"
					size="md"
					:loading="activando"
					@click="accionEsteAparato"
				>
					{{ estado.boton }}
				</Button>
			</div>

			<!-- Silenciar no borra nada: para las vacaciones, o para no enterarse
			     de cada respuesta un domingo. Al volver se enciende y ya. -->
			<div
				v-if="configuracionPush.data?.habilitado"
				class="mt-3 flex items-center justify-between gap-4 rounded-lg border border-outline-gray-2 px-4 py-3"
			>
				<div class="min-w-0">
					<p class="text-body font-medium text-ink-gray-9">
						{{ __('Notify me') }}
					</p>
					<p class="mt-0.5 text-support text-ink-gray-7">
						{{
							silenciado
								? __('Muted. Your devices stay registered and nothing reaches them.')
								: __('On all your devices.')
						}}
					</p>
				</div>
				<Switch :model-value="!silenciado" :disabled="guardandoSilencio" @update:model-value="cambiarSilencio" />
			</div>
		</section>

		<section v-if="configuracionPush.data?.habilitado">
			<h2 class="mb-1 text-heading font-semibold text-ink-gray-9">
				{{ __('Your devices') }}
			</h2>
			<p class="text-support text-ink-gray-7">
				{{ __('Where the notifications arrive. Each one is yours: nobody else sees this list.') }}
			</p>

			<p v-if="dispositivos.loading && !dispositivos.data" class="mt-4 text-support text-ink-gray-6">
				{{ __('Loading...') }}
			</p>
			<div
				v-else-if="!dispositivos.data?.length"
				class="mt-4 rounded-lg border border-dashed border-outline-gray-2 px-4 py-6 text-center"
			>
				<p class="text-body font-medium text-ink-gray-9">
					{{ __('No device registered yet') }}
				</p>
				<p class="mt-1 text-support text-ink-gray-7">
					{{ __('Turn on notifications on this device with the button above. On iPhone, install TanArtistic on your home screen first.') }}
				</p>
			</div>
			<ul v-else class="mt-4 divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2">
				<li
					v-for="d in dispositivos.data"
					:key="d.name"
					class="flex items-start gap-3 px-4 py-3"
				>
					<component
						:is="d.plataforma === 'computadora' ? Monitor : Smartphone"
						class="mt-0.5 size-5 shrink-0 text-ink-gray-6"
						aria-hidden="true"
					/>
					<div class="min-w-0 flex-1">
						<div v-if="editando === d.name" class="flex items-center gap-2">
							<FormControl
								v-model="borrador"
								class="flex-1"
								:maxlength="40"
								:placeholder="d.nombre"
								@keydown.enter="guardarNombre(d)"
								@keydown.esc="editando = null"
							/>
							<Button variant="solid" size="md" @click="guardarNombre(d)">
								{{ __('Save') }}
							</Button>
						</div>
						<div v-else class="flex flex-wrap items-center gap-x-2 gap-y-1">
							<span class="text-body font-medium text-ink-gray-9">{{ d.nombre }}</span>
							<span
								v-if="d.este"
								class="rounded-full bg-surface-gray-2 px-2 py-0.5 text-label font-medium text-ink-gray-8"
							>
								{{ __('This device') }}
							</span>
						</div>
						<p
							class="mt-0.5 text-support"
							:class="d.en_pausa || d.fallos ? 'text-ink-red-4' : 'text-ink-gray-7'"
						>
							{{ situacion(d) }}
						</p>
					</div>
					<div v-if="editando !== d.name" class="flex shrink-0 items-center">
						<Button
							variant="ghost"
							size="md"
							:label="__('Rename')"
							@click="empezarAEditar(d)"
						>
							<template #icon><Pencil class="size-4" /></template>
						</Button>
						<Button
							variant="ghost"
							size="md"
							:label="__('Remove')"
							@click="porQuitar = d"
						>
							<template #icon><Trash2 class="size-4" /></template>
						</Button>
					</div>
				</li>
			</ul>

			<!-- La prueba va a TODOS sus aparatos: decirlo evita que alguien pruebe
			     uno y se desconcierte cuando suenan los tres. -->
			<div
				v-if="dispositivos.data?.length"
				class="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
			>
				<p class="text-support text-ink-gray-7">
					{{ __('The test reaches all your devices at once. Try it with the app closed.') }}
				</p>
				<Button variant="subtle" size="md" :loading="probando" @click="probar">
					<template #prefix><BellRing class="size-4" /></template>
					{{ __('Send a test notification') }}
				</Button>
			</div>
		</section>

		<Dialog
			:open="!!porQuitar"
			:title="__('Remove {0}?').format(porQuitar?.nombre || '')"
			:actions="[
				{
					label: __('Remove'),
					variant: 'solid',
					theme: 'red',
					onClick: ({ close }) => quitar(close),
				},
			]"
			@update:open="(abierto) => !abierto && (porQuitar = null)"
		>
			<template #default>
				<p class="text-body text-ink-gray-7">
					{{
						porQuitar?.este
							? __('This device stops receiving notifications. If you open TanArtistic here again with notifications allowed, it registers itself again.')
							: __('That device stops receiving notifications. If it opens TanArtistic again, it registers itself again.')
					}}
				</p>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { Button, Dialog, FormControl, Switch, call, createResource, toast } from 'frappe-ui'
import {
	BellOff,
	BellRing,
	Download,
	Monitor,
	Pencil,
	Smartphone,
	Trash2,
	TriangleAlert,
} from 'lucide-vue-next'
import { guiaInstalarAbierta } from '@/utils/appInstalable'
import {
	activarAvisos,
	configuracionPush,
	endpointLocal,
	estadoPush,
	refrescarEstadoPush,
} from '@/utils/avisosPush'

const props = defineProps({
	profile: { type: Object, required: true },
})

const $user = inject('$user')
const dayjs = inject('$dayjs')
const esPropio = computed(() => $user.data?.name === props.profile.data?.name)

const METODOS = 'taar_lms.avisos_push'

/* ── Este aparato ─────────────────────────────────────────────────────────── */

const activando = ref(false)

const estado = computed(() => {
	switch (estadoPush.value) {
		case 'activos':
			return { icono: BellRing, titulo: __('This device receives notifications.') }
		case 'con-permiso':
			return {
				icono: TriangleAlert,
				titulo: __('You allowed notifications, but this device is not registered.'),
				detalle: __('Nothing reaches it until it is registered.'),
				boton: __('Register this device'),
			}
		case 'sin-preguntar':
			return {
				icono: BellOff,
				titulo: __('This device does not receive notifications yet.'),
				boton: __('Turn on here'),
			}
		case 'negado':
			return {
				icono: BellOff,
				titulo: __('Notifications are blocked for TanArtistic on this browser.'),
				detalle: __('To receive them, allow them in your browser or phone settings.'),
			}
		case 'falta-instalar':
			return {
				icono: Download,
				titulo: __('On iPhone and iPad, notifications only arrive with the app installed.'),
				detalle: __('Install TanArtistic on your home screen and turn them on from there.'),
				boton: __('See how'),
			}
		case 'no-soportado':
			return {
				icono: BellOff,
				titulo: __('This browser cannot receive notifications.'),
			}
		default:
			return {
				icono: BellOff,
				titulo: __('Notifications are not available yet.'),
			}
	}
})

async function accionEsteAparato() {
	if (estadoPush.value === 'falta-instalar') {
		guiaInstalarAbierta.value = true
		return
	}
	activando.value = true
	try {
		const resultado = await activarAvisos()
		if (resultado === 'con-permiso') {
			toast.error(__('This device could not be registered. Try again in a moment.'))
		}
		await cargarDispositivos()
	} finally {
		activando.value = false
	}
}

/* ── Silencio ─────────────────────────────────────────────────────────────── */

const silenciado = ref(!!configuracionPush.data?.silenciado)
watch(
	() => configuracionPush.data?.silenciado,
	(valor) => (silenciado.value = !!valor)
)
const guardandoSilencio = ref(false)

async function cambiarSilencio(recibir) {
	// Se mueve en el acto: un interruptor que tarda invita a tocarlo dos veces, y
	// la segunda deshace la primera.
	const antes = silenciado.value
	silenciado.value = !recibir
	guardandoSilencio.value = true
	try {
		await call(`${METODOS}.silenciar`, { silenciado: !recibir })
		configuracionPush.fetch()
	} catch {
		silenciado.value = antes
		toast.error(__('The change was not saved.'))
	} finally {
		guardandoSilencio.value = false
	}
}

/* ── Los dispositivos ─────────────────────────────────────────────────────── */

const dispositivos = createResource({ url: `${METODOS}.mis_dispositivos` })

async function cargarDispositivos() {
	await dispositivos.fetch({ endpoint: await endpointLocal() })
}

function situacion(d) {
	if (d.en_pausa) return __('Stopped receiving after several failed attempts')
	if (d.fallos) {
		return d.fallos === 1
			? __('1 failed attempt')
			: __('{0} failed attempts').format(d.fallos)
	}
	if (d.ultimo_envio) {
		return __('Last notification {0}').format(dayjs(d.ultimo_envio).fromNow())
	}
	return __('Ready to receive')
}

const editando = ref(null)
const borrador = ref('')

function empezarAEditar(d) {
	editando.value = d.name
	borrador.value = d.nombre || ''
}

async function guardarNombre(d) {
	editando.value = null
	if ((d.nombre || '') === borrador.value.trim()) return
	try {
		await call(`${METODOS}.renombrar`, { dispositivo: d.name, nombre: borrador.value })
		await cargarDispositivos()
	} catch {
		toast.error(__('The name was not changed.'))
	}
}

const porQuitar = ref(null)

async function quitar(close) {
	const d = porQuitar.value
	try {
		await call(`${METODOS}.quitar`, { dispositivo: d.name })
		close()
		porQuitar.value = null
		await cargarDispositivos()
		// Quitar este aparato no le retira el permiso al navegador: en el
		// siguiente arranque se registraría solo. Se lo decimos al estado ya.
		if (d.este) estadoPush.value = 'con-permiso'
		toast.success(__('Device removed'))
	} catch {
		toast.error(__('The device was not removed.'))
	}
}

const probando = ref(false)

async function probar() {
	probando.value = true
	try {
		const { enviados, total, fallidos } = await call(`${METODOS}.probar`)
		if (enviados) {
			toast.success(__('Test notification sent'), {
				description:
					enviados === 1
						? __('It should appear in a few seconds.')
						: __('Sent to {0} devices.').format(enviados),
			})
		} else if (fallidos) {
			toast.error(__('It could not be delivered'), {
				description: __('{0} of {1} devices rejected it.').format(fallidos, total),
			})
		} else {
			toast.info(__('No device registered yet'))
		}
		await cargarDispositivos()
	} catch {
		toast.error(__('The test notification was not sent.'))
	} finally {
		probando.value = false
	}
}

onMounted(async () => {
	if (!esPropio.value) return
	await refrescarEstadoPush()
	if (configuracionPush.data?.habilitado) cargarDispositivos()
})
</script>
