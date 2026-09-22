<template>
	<!-- «¿Te aviso una hora antes?», justo después de «Voy a asistir». Es el
	     momento en que el aviso le sirve: acaba de decir que viene. El permiso se
	     pide desde este toque y desde ningún otro sitio sin contexto. -->
	<div
		v-if="visible"
		class="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 rounded-lg bg-surface-gray-2 px-3 py-2.5"
	>
		<component :is="icono" class="size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
		<p class="min-w-0 flex-1 text-support text-ink-gray-8">{{ texto }}</p>
		<Button
			v-if="boton"
			variant="solid"
			size="sm"
			:loading="ocupada"
			@click="accion"
		>
			{{ boton }}
		</Button>
		<button
			type="button"
			class="text-support text-ink-gray-6 underline underline-offset-2 hover:text-ink-gray-8"
			@click="cerrar"
		>
			{{ listo ? __('Close') : __('Not now') }}
		</button>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Button, toast } from 'frappe-ui'
import { BellOff, BellRing, Check, Download } from 'lucide-vue-next'
import { guiaInstalarAbierta } from '@/utils/appInstalable'
import {
	activarAvisos,
	estadoPush,
	plataforma,
	refrescarEstadoPush,
} from '@/utils/avisosPush'

const CLAVE_CERRADA = 'taar-aviso-una-hora-cerrado'
/** «Ahora no» la calla un mes: la siguiente sesión no vuelve a preguntar. */
const UN_MES = 30 * 24 * 60 * 60 * 1000

function leerCerrada() {
	try {
		const cuando = Number(localStorage.getItem(CLAVE_CERRADA))
		return Number.isFinite(cuando) && Date.now() - cuando < UN_MES
	} catch {
		return false
	}
}

const cerrada = ref(leerCerrada())
const ocupada = ref(false)
// Solo se confirma a quien lo acaba de activar aquí. A quien ya los tenía no
// se le enseña nada: la tarjeta sería ruido.
const listo = ref(false)

onMounted(refrescarEstadoPush)

const enTelefono = plataforma() !== 'computadora'

const visible = computed(() => {
	if (listo.value) return true
	if (cerrada.value) return false
	return ['sin-preguntar', 'con-permiso', 'falta-instalar', 'negado'].includes(
		estadoPush.value
	)
})

const icono = computed(() => {
	if (listo.value) return Check
	if (estadoPush.value === 'falta-instalar') return Download
	if (estadoPush.value === 'negado') return BellOff
	return BellRing
})

const texto = computed(() => {
	if (listo.value) return __("Done: I'll remind you here an hour before.")
	switch (estadoPush.value) {
		case 'falta-instalar':
			return __('On iPhone, reminders only arrive with the app installed.')
		case 'negado':
			return __(
				'Notifications are blocked for TanArtistic. Turn them on in your browser settings to get the reminder.'
			)
		default:
			return enTelefono
				? __('Want a reminder on this phone an hour before?')
				: __('Want a reminder on this computer an hour before?')
	}
})

const boton = computed(() => {
	if (listo.value || estadoPush.value === 'negado') return null
	return estadoPush.value === 'falta-instalar' ? __('See how') : __('Remind me')
})

async function accion() {
	if (estadoPush.value === 'falta-instalar') {
		guiaInstalarAbierta.value = true
		return
	}
	ocupada.value = true
	try {
		const estado = await activarAvisos()
		if (estado === 'activos') {
			listo.value = true
		} else if (estado === 'con-permiso') {
			toast.error(__('The reminders could not be turned on. Try again in a moment.'))
		}
	} finally {
		ocupada.value = false
	}
}

function cerrar() {
	if (listo.value) {
		listo.value = false
		return
	}
	cerrada.value = true
	try {
		localStorage.setItem(CLAVE_CERRADA, String(Date.now()))
	} catch {
		// Vuelve a salir al recargar. Molesto, no roto.
	}
}
</script>
