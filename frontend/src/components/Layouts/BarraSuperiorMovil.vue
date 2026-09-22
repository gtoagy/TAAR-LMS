<template>
	<!-- La barra superior del móvil, con el único <h1> de la pantalla. El título
	     sale de la ruta (useTituloMovil) y las pantallas no lo repiten: su
	     cabecera se queda con el subtítulo y las acciones. Solo va en las
	     pantallas de PANTALLAS_CON_BARRA; en las demás no se pinta nada.

	     A los lados, lo que es de ella y no un destino: su perfil a la izquierda
	     y sus avisos a la derecha. Las dos columnas miden lo mismo aunque estén
	     vacías (sin sesión), para que el título quede siempre centrado. -->
	<header
		v-if="titulo"
		class="relative z-30 grid h-[var(--topbar-h)] shrink-0 grid-cols-[2.75rem_minmax(0,1fr)_2.75rem] items-center gap-2 border-b border-outline-gray-1 bg-surface-base px-3.5"
	>
		<router-link
			v-if="perfil"
			:to="perfil"
			class="taar-barra-boton"
			:aria-label="__('Profile')"
			:aria-current="enMiPerfil ? 'page' : undefined"
		>
			<Avatar
				size="xl"
				:label="userResource.data.full_name"
				:image="userResource.data.user_image"
				class="taar-barra-avatar"
				:class="{ 'taar-barra-avatar-activo': enMiPerfil }"
			/>
		</router-link>
		<span v-else />

		<h1 class="truncate text-center text-heading font-semibold text-ink-gray-9">
			{{ titulo }}
		</h1>

		<!-- `data-notifications-trigger`: sin él, el clic que abre el panel cuenta
		     como clic fuera del panel y lo vuelve a cerrar en el acto. -->
		<button
			v-if="userResource.data"
			type="button"
			class="taar-barra-boton justify-self-end text-ink-gray-7"
			data-notifications-trigger
			aria-haspopup="dialog"
			:aria-expanded="panelVisible"
			:aria-label="etiquetaAvisos"
			@click="toggleNotifications"
		>
			<Bell class="size-5" :stroke-width="1.75" />
			<span v-if="noLeidas" class="taar-contador absolute end-1.5 top-1.5">
				{{ contador }}
			</span>
		</button>
	</header>
</template>

<script setup>
import { computed, inject, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Avatar, createResource } from 'frappe-ui'
import { Bell } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/user'
import { panelVisible, toggleNotifications } from '@/stores/notifications'
import { useTituloMovil } from '@/utils/navegacionMovil'

const route = useRoute()
const { titulo } = useTituloMovil()
const { user } = sessionStore()
const { userResource } = usersStore()
const socket = inject('$socket')

const perfil = computed(() =>
	userResource.data?.username
		? { name: 'Profile', params: { username: userResource.data.username } }
		: null
)
const enMiPerfil = computed(
	() =>
		route.matched[0]?.name === 'Profile' &&
		route.params.username === userResource.data?.username
)

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
const etiquetaAvisos = computed(() =>
	noLeidas.value
		? __('Notifications ({0} unread)').format(noLeidas.value)
		: __('Notifications')
)

const alLlegarAviso = () => sinLeer.reload()
onMounted(() => socket?.on('publish_lms_notifications', alLlegarAviso))
// Con el handler: `off` sin él quitaría también el del panel lateral.
onUnmounted(() => socket?.off('publish_lms_notifications', alLlegarAviso))
</script>

<style>
/* 44px de lado: el mínimo del dedo, aunque el avatar mida 32 y la campana 20. */
.taar-barra-boton {
	position: relative;
	display: grid;
	place-items: center;
	width: 2.75rem;
	height: 2.75rem;
	border-radius: 9999px;
	-webkit-tap-highlight-color: transparent;
}
.taar-barra-boton:active {
	background: var(--surface-gray-2);
}
.taar-barra-boton:focus-visible {
	outline: 2px solid var(--taar-primary);
	outline-offset: -2px;
}

/* En su perfil, el avatar se marca con el mismo color que la pestaña activa:
   es el sitio donde está, aunque no sea una pestaña. */
.taar-barra-avatar-activo {
	box-shadow:
		0 0 0 2px var(--surface-base),
		0 0 0 4px var(--taar-nav-icono-activo);
}

/* El contador de avisos. El aro del color de fondo lo despega de la campana. */
.taar-contador {
	display: grid;
	place-items: center;
	height: 1rem;
	min-width: 1rem;
	padding-inline: 0.25rem;
	border-radius: 9999px;
	background: #605fd8;
	box-shadow: 0 0 0 2px var(--surface-base);
	color: #ffffff;
	font-size: 0.6875rem;
	line-height: 1;
	font-weight: 600;
	font-variant-numeric: tabular-nums;
}
</style>
