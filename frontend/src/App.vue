<template>
	<FrappeUIProvider>
		<Layout class="isolate text-p-base">
			<!-- Arriba del contenido y dentro del layout que toque: los tres
			     layouts pintan aquí su <slot />, así que la invitación acompaña a
			     la alumna por toda la escuela sin tocar ninguno de ellos. -->
			<BarraResena />
			<router-view />
		</Layout>
		<!-- El asistente de bienvenida vive aquí arriba y no dentro del catálogo,
		     que es donde estaba. Colgado del catálogo solo aparecía si la
		     dirección traía la marca del pago recién hecho, así que las alumnas
		     de siempre —que entran por el inicio de sesión— no lo veían nunca. -->
		<BienvenidaPago
			v-if="mostrarAsistente"
			v-model="mostrarAsistente"
			:session-id="sessionIdPago"
		/>
		<NotificationPanel />
		<InstallPrompt v-if="isMobile && !settings.data?.disable_pwa" />
		<Dialogs />
	</FrappeUIProvider>
</template>
<script setup>
import { FrappeUIProvider } from 'frappe-ui'
import { Dialogs } from '@/utils/dialogs'
import { computed, onUnmounted, ref, watch } from 'vue'
import { useScreenSize } from './utils/composables'
import { useSettings } from '@/stores/settings'
import { useRouter } from 'vue-router'
import DesktopLayout from './components/Layouts/DesktopLayout.vue'
import MobileLayout from './components/Layouts/MobileLayout.vue'
import NoSidebarLayout from './components/Layouts/NoSidebarLayout.vue'
import InstallPrompt from './components/InstallPrompt.vue'
import BarraResena from '@/components/BarraResena.vue'
import BienvenidaPago from '@/components/BienvenidaPago.vue'
import NotificationPanel from '@/components/Notifications/NotificationPanel.vue'
import { usersStore } from '@/stores/user'
import { sessionStore } from '@/stores/session'
import { recogerPagoPendiente, olvidarPagoPendiente } from '@/utils/pagoPendiente'

const { isMobile } = useScreenSize()
const router = useRouter()
const noSidebar = ref(false)
const { settings } = useSettings()

/* ── El asistente de bienvenida ──────────────────────────────────────────────
   Se abre por dos caminos que no se pisan: acaba de pagar (traemos el
   identificador de la sesión de Stripe) o ya está dentro y todavía no ha pasado
   por él. El segundo es el que alcanza a las alumnas que venían de antes. */
const sessionIdPago = ref(recogerPagoPendiente())
const mostrarAsistente = ref(false)

const { userResource } = usersStore()
// El store entero y no `const { isLoggedIn } = ...`: al desestructurarlo, pinia
// entrega el valor ya desenvuelto y no el computed, así que la variable se queda
// congelada en lo que valiera al cargar la página. Leyéndolo como propiedad
// dentro del computed sí sigue vivo.
const session = sessionStore()

const leFalta = computed(() => {
	if (!session.isLoggedIn) return false
	return !!userResource?.data?.taar_onboarding_pendiente
})

watch(
	[sessionIdPago, leFalta],
	([pago, falta]) => {
		if (pago || falta) mostrarAsistente.value = true
	},
	{ immediate: true }
)

watch(mostrarAsistente, (abierto) => {
	// Al cerrarse se olvida el pago guardado: si volviera a abrirse con el mismo
	// identificador, quien ya puso su contraseña vería la pantalla de nuevo.
	if (!abierto && sessionIdPago.value) {
		olvidarPagoPendiente()
		sessionIdPago.value = null
	}
})

router.beforeEach((to, from, next) => {
	if (to.query.fromLesson || to.path === '/persona') {
		noSidebar.value = true
	} else {
		noSidebar.value = false
	}
	next()
})

const Layout = computed(() => {
	if (noSidebar.value) {
		return NoSidebarLayout
	}
	if (isMobile.value) {
		return MobileLayout
	}
	return DesktopLayout
})

onUnmounted(() => {
	noSidebar.value = false
})
</script>
