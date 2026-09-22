<template>
	<!-- La invitación a instalar la app. Va en el flujo, arriba del contenido,
	     como la de la reseña: nunca tapa la píldora ni la hoja de «Más», y sale
	     de una en una con ella (utils/avisosDeArriba.js). -->
	<div
		v-if="visible"
		class="taar-invitacion-instalar flex shrink-0 items-center gap-3 border-b border-outline-gray-1 ps-4"
	>
		<Download class="size-4 shrink-0 taar-invitacion-icono" aria-hidden="true" />
		<p class="min-w-0 flex-1 py-2.5 text-body text-ink-gray-8">
			{{
				conAvisos
					? __('Install TanArtistic to get the live session reminders on your phone.')
					: __('Install TanArtistic and open your classes with one tap.')
			}}
		</p>
		<Button variant="solid" size="md" :loading="instalando" @click="instalar">
			{{ ios ? __('See how') : __('Install') }}
		</Button>
		<button
			type="button"
			class="grid size-11 shrink-0 place-items-center rounded-full text-ink-gray-6 active:bg-surface-gray-2"
			:aria-label="__('Close')"
			@click="cerrar"
		>
			<X class="size-4" />
		</button>
	</div>

	<!-- La guía del iPhone. Existe porque iOS no tiene ningún aviso de «instalar
	     esta app»: si no se lo pedimos nosotros, no pasa. -->
	<Dialog v-model:open="guiaAbierta" :title="__('Install TanArtistic on your iPhone')">
		<template #default>
			<p class="text-support text-ink-gray-6">
				{{
					__(
						'It takes less than a minute. TanArtistic stays as one more app on your phone: with its own icon and without the browser bar.'
					)
				}}
			</p>

			<ol class="mt-5 space-y-4">
				<li v-for="(paso, i) in pasos" :key="paso.titulo" class="flex gap-3">
					<span
						class="grid size-7 shrink-0 place-items-center rounded-full text-label font-semibold tabular-nums taar-invitacion-numero"
						aria-hidden="true"
					>
						{{ i + 1 }}
					</span>
					<div class="min-w-0 flex-1">
						<p class="flex items-center gap-2 text-body font-medium text-ink-gray-9">
							{{ paso.titulo }}
							<component
								:is="paso.icono"
								class="size-4 shrink-0 text-ink-gray-6"
								aria-hidden="true"
							/>
						</p>
						<p class="mt-0.5 text-support text-ink-gray-6">{{ paso.detalle }}</p>
					</div>
				</li>
			</ol>

			<!-- Se avisa ANTES, que es la diferencia entre un paso más y «la app
			     no sirve». La app instalada guarda su sesión aparte de Safari: la
			     primera vez pide entrar otra vez, y quien no lo espera cree que
			     se instaló mal y la borra. -->
			<div class="mt-5 flex gap-3 rounded-lg bg-surface-gray-2 p-3">
				<KeyRound class="mt-0.5 size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
				<p class="text-support text-ink-gray-7">
					<span class="font-medium text-ink-gray-9">
						{{ __('You will sign in again.') }}
					</span>
					{{
						__(
							'The installed app keeps its session apart from the browser. It is normal, not an error. If you do not remember your password, the sign-in screen has "Forgot password?".'
						)
					}}
				</p>
			</div>

			<p class="mt-5 text-support text-ink-gray-6">
				{{
					conAvisos
						? __(
								'When you finish, open TanArtistic from its new icon and turn on notifications in your profile.'
							)
						: __('When you finish, open TanArtistic from its new icon.')
				}}
			</p>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button, Dialog, toast } from 'frappe-ui'
import { Check, Download, KeyRound, Plus, Share, X } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import { avisoDeArriba } from '@/utils/avisosDeArriba'
import { configuracionPush } from '@/utils/avisosPush'
import {
	esIOS,
	eventoInstalar,
	guiaInstalarAbierta,
	instalada,
} from '@/utils/appInstalable'

/**
 * La invitación a instalar TanArtistic en el teléfono. Reemplaza al
 * InstallPrompt de upstream, que abría un diálogo en Android y en iPhone salía
 * una sola vez en la vida. Dos caminos detrás del mismo botón:
 * - Android: Chrome avisa con `beforeinstallprompt` que se puede instalar, y el
 *   botón instala en el acto.
 * - iPhone y iPad: no existe ese evento ni nada parecido, así que el botón abre
 *   la guía con los pasos.
 * Las reglas, en docs/app-instalable.md.
 */

const props = defineProps({
	// El banner, solo en el móvil. La guía se monta siempre: los avisos la abren
	// también desde un iPad a lo ancho, que no cuenta como móvil.
	conBanner: { type: Boolean, default: true },
})

const CLAVE_CERRADA = 'taar-instalar-cerrada'
/** Cerrarla la calla una semana y no para siempre: suficiente para no dar la lata. */
const UNA_SEMANA = 7 * 24 * 60 * 60 * 1000

const session = sessionStore()
const ios = esIOS()

// En iPhone, sin instalar no llega ningún aviso: ahí la invitación promete los
// recordatorios. Solo si el servidor los tiene encendidos para esta cuenta, que
// mientras se prueban es una sola. En Android llegan igual desde Chrome, así
// que allá no se promete nada que instalar no dé.
const conAvisos = computed(() => ios && !!configuracionPush.data?.habilitado)

function leerCerrada() {
	try {
		const cuando = Number(localStorage.getItem(CLAVE_CERRADA))
		return Number.isFinite(cuando) && Date.now() - cuando < UNA_SEMANA
	} catch {
		// Sin localStorage, mejor enseñarla que esconderla.
		return false
	}
}
const cerrada = ref(leerCerrada())

function cerrar() {
	cerrada.value = true
	try {
		localStorage.setItem(CLAVE_CERRADA, String(Date.now()))
	} catch {
		// Vuelve a salir al recargar. Molesto, no roto.
	}
}

// Solo con sesión: instalar sin cuenta no lleva a nada, y la guía avisa de que
// habrá que volver a entrar.
const visible = avisoDeArriba(
	'instalar',
	computed(
		() =>
			props.conBanner &&
			session.isLoggedIn &&
			!instalada.value &&
			!cerrada.value &&
			'serviceWorker' in navigator &&
			(ios || !!eventoInstalar.value)
	)
)

/* ── Instalar ──────────────────────────────────────────────────────────────── */
const instalando = ref(false)
const guiaAbierta = guiaInstalarAbierta

async function instalar() {
	if (ios) {
		guiaAbierta.value = true
		return
	}
	const evento = eventoInstalar.value
	if (!evento) return
	instalando.value = true
	try {
		await evento.prompt()
		const { outcome } = await evento.userChoice
		// El evento se gasta al usarlo. Si dice que no, Chrome mandará otro más
		// adelante por su cuenta.
		eventoInstalar.value = null
		if (outcome === 'accepted') {
			toast.success(__('TanArtistic is installed'), {
				description: __('Open it from its icon on your home screen.'),
			})
		}
	} catch {
		toast.error(__('It could not be installed'), {
			description: __('Try it from your browser menu.'),
		})
	} finally {
		instalando.value = false
	}
}

/* ── La guía del iPhone ────────────────────────────────────────────────────── */

// Todos los navegadores de iOS son Safari por dentro, así que instalar funciona
// desde cualquiera. Lo que cambia es DÓNDE está Compartir, y una guía que señala
// el lugar equivocado se lee como «esto no se puede».
// CriOS = Chrome, FxiOS = Firefox, EdgiOS = Edge, OPiOS = Opera.
const safari = !/CriOS|FxiOS|EdgiOS|OPiOS/.test(navigator.userAgent)
const ipad =
	/iPad/.test(navigator.userAgent) ||
	(navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)

const pasos = computed(() => [
	{
		icono: Share,
		titulo: safari ? __('Tap the Share button') : __('Open the browser menu'),
		detalle: !safari
			? __(
					'Look for Share. If you do not find it, open this same page in Safari: there it is in plain sight.'
				)
			: ipad
			? __('It is the square with the arrow pointing up, at the top right.')
			: __(
					'It is the square with the arrow pointing up. Depending on your iPhone it is in the bottom bar or inside the three dots button.'
				),
	},
	{
		icono: Plus,
		titulo: __('Choose "Add to Home Screen"'),
		detalle: __('It is further down the list; scroll a little.'),
	},
	{
		icono: Check,
		titulo: __('Confirm with "Add"'),
		detalle: __('The TanArtistic icon appears on your home screen.'),
	},
])
</script>

<style>
.taar-invitacion-instalar {
	background: rgb(128 127 236 / 0.08);
}
.taar-invitacion-icono {
	color: var(--taar-nav-icono-activo);
}
.taar-invitacion-numero {
	background: rgb(128 127 236 / 0.15);
	color: var(--taar-nav-texto-activo);
}
</style>
