<template>
	<Dialog
		v-model:open="abierto"
		:title="__('Purchase history')"
	>
		<template #body-content>
			<div class="text-body font-medium text-ink-gray-9">
				{{ nombre || alumna }}
			</div>
			<div class="break-all text-support text-ink-gray-6">{{ alumna }}</div>

			<div v-if="historial.loading" class="mt-8 flex justify-center pb-6">
				<LoadingIndicator class="size-5 text-ink-gray-5" />
			</div>

			<ErrorMessage
				v-else-if="historial.error"
				class="mt-4"
				:message="mensajeDelServidor(historial.error) || __('We could not load her history.')"
			/>

			<template v-else-if="datos">
				<!-- Dónde está hoy, antes de la historia: es lo primero que se
				     pregunta al atender. -->
				<p class="mt-4 rounded-md bg-surface-gray-1 p-3 text-support text-ink-gray-8">
					{{ resumenMembresia }}
				</p>

				<p
					v-if="avisoStripe"
					class="mt-3 text-support text-ink-amber-8"
				>
					{{ avisoStripe }}
				</p>

				<p
					v-if="!datos.eventos.length"
					class="mt-6 text-center text-body text-ink-gray-6"
				>
					{{ __('No purchases on record.') }}
				</p>

				<!-- La más nueva arriba. -->
				<ol v-else class="mt-4 space-y-0">
					<li
						v-for="(e, i) in datos.eventos"
						:key="i"
						class="relative flex gap-3 pb-4 pl-1"
					>
						<div class="flex flex-col items-center">
							<span
								class="mt-1.5 size-2.5 shrink-0 rounded-full"
								:class="COLOR_PUNTO[e.estado] || COLOR_PUNTO.neutro"
							/>
							<span
								v-if="i < datos.eventos.length - 1"
								class="mt-1 w-px flex-1 bg-outline-gray-2"
							/>
						</div>
						<div class="min-w-0 flex-1">
							<div class="flex items-start justify-between gap-2">
								<div class="min-w-0 text-base font-medium text-ink-gray-9">
									{{ e.titulo }}
								</div>
								<div
									v-if="e.monto"
									class="shrink-0 text-base tabular-nums"
									:class="e.estado === 'mal' ? 'text-ink-red-4' : 'text-ink-gray-9'"
								>
									{{ e.monto }}
								</div>
							</div>
							<div class="mt-0.5 text-support text-ink-gray-6">
								{{ [fecha(e.fecha), e.metodo, e.detalle].filter(Boolean).join(' · ') }}
							</div>
						</div>
					</li>
				</ol>

				<a
					v-if="datos.enlace_stripe"
					:href="datos.enlace_stripe"
					target="_blank"
					rel="noopener"
					class="mt-2 inline-block text-support text-ink-gray-7 underline"
				>
					{{ __('See her in Stripe') }}
				</a>
			</template>
		</template>
	</Dialog>
</template>

<script setup>
import { createResource, Dialog, ErrorMessage, LoadingIndicator } from 'frappe-ui'
import { computed, watch } from 'vue'

const props = defineProps({
	alumna: { type: String, default: '' },
	nombre: { type: String, default: '' },
})

const abierto = defineModel('open', { type: Boolean, default: false })

// Se pide al abrirla y no antes: parte de la historia sale de Stripe en vivo, y
// no tiene sentido preguntar por cada tarjeta de la lista.
const historial = createResource({
	url: 'taar_lms.historial.de_alumna',
	makeParams: () => ({ alumna: props.alumna }),
})

watch(
	() => [abierto.value, props.alumna],
	([open, alumna]) => {
		if (open && alumna) historial.reload()
	}
)

const datos = computed(() => historial.data || null)

const COLOR_PUNTO = {
	ok: 'bg-surface-green-3',
	mal: 'bg-surface-red-5',
	neutro: 'bg-surface-gray-4',
}

const resumenMembresia = computed(() => {
	const m = datos.value?.membresia
	if (!m) return __('Never had a membership.')
	if (m.vitalicio) return __('Lifetime access.')
	// Estado y plan llegan en español desde el servidor, como en la ficha.
	let texto = __('Membership: {0}').format([m.estado, m.plan].filter(Boolean).join(' · '))
	if (m.hasta) {
		texto +=
			' · ' +
			(m.cancelara
				? __('ends on {0}').format(m.hasta)
				: __('until {0}').format(m.hasta))
	}
	if (m.de_disco) texto += ' · ' + __('came from Disco')
	return texto
})

const avisoStripe = computed(() => {
	const s = datos.value?.stripe
	if (s === 'error') return __('Stripe did not answer: card payments may be missing.')
	if (s === 'sin_clave') return __('Stripe is not connected: card payments are missing.')
	return ''
})

/* Las fechas llegan como "2026-10-12 14:33:00": Safari no entiende el espacio. */
const fecha = (texto) => {
	if (!texto) return ''
	const d = new Date(String(texto).replace(' ', 'T'))
	return d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })
}

const mensajeDelServidor = (error) => {
	if (!error) return ''
	return typeof error === 'string' ? error : error?.messages?.[0] || ''
}
</script>
