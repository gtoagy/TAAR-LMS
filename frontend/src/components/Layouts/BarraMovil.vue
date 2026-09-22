<template>
	<template v-if="pestanas.length || gruposMas.length">
		<!-- Fondo de la hoja de «Más». Va detrás de la píldora, que sigue a mano:
		     tocar otra pestaña con la hoja abierta navega directo. -->
		<Transition name="taar-fondo">
			<div
				v-if="hojaAbierta"
				class="absolute inset-0 z-10 bg-black/20"
				aria-hidden="true"
				@click="hojaAbierta = false"
			/>
		</Transition>

		<Transition name="taar-hoja">
			<div
				v-if="hojaAbierta"
				id="taar-hoja-mas"
				role="dialog"
				:aria-label="__('More')"
				class="taar-hoja-mas"
			>
				<template v-for="(grupo, g) in gruposMas" :key="grupo.label">
					<div v-if="g > 0" class="mx-3 my-1 border-t border-outline-gray-1" />
					<button
						v-for="item in grupo.items"
						:key="item.label"
						type="button"
						class="flex min-h-11 w-full items-center gap-3 rounded-2xl px-3 text-start text-body text-ink-gray-8 active:bg-surface-gray-2"
						:class="esDeLaRuta(item, route) ? 'bg-surface-gray-2 font-medium text-ink-gray-9' : ''"
						:data-notifications-trigger="item.panel === 'notifications' ? '' : null"
						@click="abrir(item)"
					>
						<component
							:is="icono(item)"
							class="size-5 shrink-0 stroke-1.5 text-ink-gray-6"
						/>
						<span class="min-w-0 flex-1 truncate">{{ __(item.label) }}</span>
						<span
							v-if="item.panel === 'notifications' && noLeidas"
							class="taar-contador"
						>
							{{ contador }}
						</span>
					</button>
				</template>
			</div>
		</Transition>

		<!-- La píldora. `taar-barra-movil` no es decorativa: con ella index.css la
		     esconde cuando el vídeo entra en la pantalla completa de respaldo de
		     Plyr, que si no quedaría flotando encima de la clase. -->
		<nav
			class="taar-barra-movil taar-pildora"
			:aria-label="__('Main navigation')"
		>
			<div class="relative flex h-full">
				<!-- El selector. Mide exactamente una columna y se desplaza en
				     múltiplos de su propio ancho: con columnas iguales, 100% es un
				     salto exacto sin medir nada. Se mueve el selector y no el icono,
				     para que el ojo siga de dónde a dónde fue. -->
				<span
					aria-hidden="true"
					class="taar-pildora-selector"
					:class="indiceActivo === null ? 'opacity-0' : 'opacity-100'"
					:style="{
						width: `${100 / columnas}%`,
						transform: `translateX(${(indiceActivo ?? 0) * 100}%)`,
					}"
				>
					<span class="taar-pildora-relleno" />
				</span>

				<router-link
					v-for="(tab, i) in pestanas"
					:key="tab.label"
					:to="{ name: tab.to }"
					class="taar-pestana"
					:class="{ 'taar-pestana-activa': indiceActivo === i }"
					:aria-current="indiceActivo === i ? 'page' : undefined"
					@click="hojaAbierta = false"
				>
					<component
						:is="icono(tab)"
						class="size-5"
						:stroke-width="indiceActivo === i ? 2 : 1.5"
					/>
					<span class="max-w-full truncate text-label">
						{{ __(tab.etiquetaCorta || tab.label) }}
					</span>
				</router-link>

				<button
					type="button"
					class="taar-pestana"
					:class="{ 'taar-pestana-activa': masActivo }"
					aria-haspopup="dialog"
					:aria-expanded="hojaAbierta"
					aria-controls="taar-hoja-mas"
					@click="alternarHoja"
				>
					<span class="relative">
						<Ellipsis class="size-5" :stroke-width="masActivo ? 2 : 1.5" />
						<!-- Las notificaciones viven en «Más»: su contador se ve aquí. -->
						<span
							v-if="noLeidas"
							class="taar-contador absolute -end-2.5 -top-1.5"
						>
							{{ contador }}
						</span>
					</span>
					<span class="text-label">{{ __('More') }}</span>
				</button>
			</div>
		</nav>
	</template>
</template>

<script setup>
import { computed, inject, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { useEventListener } from '@vueuse/core'
import * as icons from 'lucide-vue-next'
import { Ellipsis } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/user'
import {
	closeNotifications,
	panelVisible,
	toggleNotifications,
} from '@/stores/notifications'
import { esDeLaRuta, useNavegacionMovil } from '@/utils/navegacionMovil'

/**
 * La barra inferior del móvil: una píldora flotante con cuatro destinos y «Más».
 * Las reglas, en docs/navegacion-y-tipografia.md.
 */
const route = useRoute()
const router = useRouter()
const { logout, user } = sessionStore()
const { userResource } = usersStore()
const socket = inject('$socket')

const hojaAbierta = ref(false)
const { pestanas, gruposMas, indiceActivo } = useNavegacionMovil(hojaAbierta)

// Las pestañas con ruta, más «Más». Sin «En vivo» la barra queda en cuatro
// columnas y el selector sigue cuadrando, porque divide entre las que haya.
const columnas = computed(() => pestanas.value.length + 1)
const masActivo = computed(() => indiceActivo.value === pestanas.value.length)

const icono = (item) =>
	typeof item.icon === 'string' ? icons[item.icon] : item.icon

/* ── Notificaciones sin leer ─────────────────────────────────────────────────
   El mismo recurso y la misma clave de caché que el panel lateral del
   ordenador: al marcar una como leída, stores/notifications.js lo recarga y el
   contador se entera sin pedir nada más. */
const sinLeer = createResource({
	cache: 'Unread Notifications Count',
	url: 'frappe.client.get_count',
	makeParams() {
		return {
			doctype: 'Notification Log',
			filters: { for_user: user, read: 0 },
		}
	},
	auto: !!user,
})
const noLeidas = computed(() => (user ? sinLeer.data || 0 : 0))
const contador = computed(() => (noLeidas.value > 9 ? '9+' : noLeidas.value))

const alLlegarAviso = () => sinLeer.reload()
onMounted(() => socket?.on('publish_lms_notifications', alLlegarAviso))
// Con el handler: `off` sin él quitaría también el del panel lateral.
onUnmounted(() => socket?.off('publish_lms_notifications', alLlegarAviso))

/* ── La hoja de «Más» ──────────────────────────────────────────────────────── */
function alternarHoja() {
	if (panelVisible.value) {
		closeNotifications()
		return
	}
	hojaAbierta.value = !hojaAbierta.value
}

watch(
	() => route.fullPath,
	() => (hojaAbierta.value = false)
)
useEventListener(document, 'keydown', (e) => {
	if (e.key === 'Escape') hojaAbierta.value = false
})

function abrir(item) {
	hojaAbierta.value = false
	if (item.panel === 'notifications') return toggleNotifications()
	if (item.action === 'login') return (window.location.href = '/login')
	if (item.action === 'logout') return logout.submit()
	if (item.to === 'Profile') {
		return router.push({
			name: 'Profile',
			params: { username: userResource.data?.username },
		})
	}
	if (item.to?.startsWith('http')) return window.open(item.to, '_blank')
	if (item.to?.includes('@')) return (window.location.href = `mailto:${item.to}`)
	if (item.to && router.hasRoute(item.to)) router.push({ name: item.to })
}
</script>

<style>
/*
 * La píldora flota a 12px de los lados y justo encima del indicador de inicio del
 * iPhone (o a 12px del borde donde no lo hay). Las medidas viven en index.css
 * (--nav-h, --nav-borde, --nav-safe) porque el área de scroll y los avisos
 * tienen que librarla con el mismo número.
 */
.taar-pildora {
	position: absolute;
	inset-inline: 0.75rem;
	bottom: var(--nav-borde);
	z-index: 20;
	height: var(--nav-h);
	max-width: 28rem;
	margin-inline: auto;
	/* 56px de alto menos 6px arriba y abajo: cada pestaña mide 44, el mínimo del dedo. */
	padding: 0.375rem;
	border-radius: 9999px;
	background: var(--surface-base);
	/* El borde va como sombra para no comerse los 44px de la pestaña. */
	box-shadow:
		0 0 0 1px var(--outline-gray-2),
		0 8px 24px -12px rgb(7 24 31 / 0.28),
		0 2px 6px -2px rgb(7 24 31 / 0.08);
}

/* El contenido pasa por detrás. Sin soporte de desenfoque, fondo sólido. */
@supports ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {
	.taar-pildora {
		background: color-mix(in srgb, var(--surface-base) 85%, transparent);
		-webkit-backdrop-filter: blur(12px);
		backdrop-filter: blur(12px);
	}
}

.taar-pildora-selector {
	position: absolute;
	inset-block: 0;
	left: 0;
	pointer-events: none;
	/* Acelera, se pasa un pelo y se acomoda, como un objeto físico. Con
	   movimiento reducido, index.css lo deja en nada. */
	transition:
		transform 0.34s cubic-bezier(0.32, 1.14, 0.44, 1),
		opacity 0.2s ease;
}

/* Un poco más angosto que la columna, para no tocar a las vecinas. */
.taar-pildora-relleno {
	display: block;
	height: 100%;
	margin-inline: 0.25rem;
	border-radius: 9999px;
	background: rgb(128 127 236 / 0.15);
}

/* Icono y etiqueta en todas, con columnas iguales. */
.taar-pestana {
	position: relative;
	display: flex;
	flex: 1 1 0;
	min-width: 0;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 0.125rem;
	padding-inline: 0.125rem;
	border-radius: 9999px;
	color: var(--ink-gray-6);
	font-weight: 500;
	-webkit-tap-highlight-color: transparent;
}

/* «Membresía» mide 63px a 12px: sin el espaciado extra del preset cabe también
   en un teléfono de 375px (68px por columna). Si alguien sube mucho la letra
   del sistema, se corta con puntos suspensivos en vez de montarse. */
.taar-pestana .text-label {
	letter-spacing: 0;
}

/* #807fec sobre el selector no llega al 3:1 que pide un icono en claro: el
   activo va en su tono de enlaces. La etiqueta, en la tinta de la marca. */
.taar-pestana-activa {
	color: var(--taar-nav-texto-activo);
	font-weight: 600;
}
.taar-pestana-activa svg {
	color: var(--taar-nav-icono-activo);
}

.taar-pestana:focus-visible {
	outline: 2px solid var(--taar-primary);
	outline-offset: -2px;
}

.taar-contador {
	display: grid;
	place-items: center;
	height: 1rem;
	min-width: 1rem;
	padding-inline: 0.25rem;
	border-radius: 9999px;
	background: #605fd8;
	color: #ffffff;
	font-size: 0.6875rem;
	line-height: 1;
	font-weight: 600;
	font-variant-numeric: tabular-nums;
}

.taar-hoja-mas {
	position: absolute;
	inset-inline: 0.75rem;
	bottom: var(--nav-safe);
	z-index: 20;
	max-width: 28rem;
	max-height: calc(100% - var(--nav-safe) - env(safe-area-inset-top) - 1rem);
	margin-inline: auto;
	overflow-y: auto;
	padding: 0.375rem;
	border-radius: 1.5rem;
	background: var(--surface-base);
	box-shadow:
		0 0 0 1px var(--outline-gray-2),
		0 16px 40px -16px rgb(7 24 31 / 0.3);
}

.taar-hoja-enter-active,
.taar-hoja-leave-active {
	transition:
		transform 0.2s ease-out,
		opacity 0.2s ease-out;
}
.taar-hoja-enter-from,
.taar-hoja-leave-to {
	opacity: 0;
	transform: translateY(0.5rem);
}
.taar-fondo-enter-active,
.taar-fondo-leave-active {
	transition: opacity 0.2s ease-out;
}
.taar-fondo-enter-from,
.taar-fondo-leave-to {
	opacity: 0;
}
</style>
