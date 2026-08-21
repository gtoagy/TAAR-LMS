<template>
	<div
		class="relative flex h-screen-dvh flex-col pt-[env(safe-area-inset-top)]"
	>
		<div
			class="flex min-h-0 flex-1 flex-col overflow-y-auto pb-4"
			id="scrollContainer"
		>
			<slot />
		</div>

		<div class="relative z-20">
			<!-- Dropdown menu -->
			<div
				class="fixed bottom-16 end-2 w-[80%] space-y-4 rounded-md bg-surface-base p-5 text-base shadow-md"
				v-if="showMenu"
				ref="menu"
			>
				<div
					v-for="link in otherLinks"
					:key="link.label"
					class="flex cursor-pointer items-center gap-x-2"
					@click="handleClick(link)"
				>
					<component
						:is="typeof link.icon === 'string' ? icons[link.icon] : link.icon"
						class="h-4 w-4 stroke-1.5 text-ink-gray-5"
					/>
					<div>{{ __(link.label) }}</div>
				</div>
			</div>

			<!-- Menú inferior: en flujo (no fixed) para que el área de scroll
			     termine físicamente arriba de él y nada quede oculto detrás -->
			<div
				v-if="sidebarSettings.data"
				class="taar-barra-movil standalone:pb-[max(1rem,env(safe-area-inset-bottom))] z-10 flex w-full items-center justify-around border-t border-outline-gray-2 bg-surface-base"
			>
				<!-- Con etiqueta: tres iconos sueltos no le dicen nada a quien
				     entra por primera vez desde el móvil, que es la mayoría.
				     Iconos y letra un punto más pequeños desde que las
				     notificaciones bajaron aquí: con una pestaña más, al tamaño
				     anterior las palabras se tocaban en un teléfono estrecho. -->
				<button
					v-for="tab in sidebarLinks"
					:key="tab.label"
					:data-notifications-trigger="
						tab.panel === 'notifications' ? '' : null
					"
					:class="isVisible(tab) ? 'flex' : 'hidden'"
					class="flex-col items-center justify-center gap-1 px-1 py-2.5 transition active:scale-95"
					@click="handleClick(tab)"
				>
					<span class="relative">
						<component
							:is="icons[tab.icon]"
							class="h-5 w-5 stroke-1.5"
							:class="[isActive(tab) ? 'text-ink-gray-9' : 'text-ink-gray-5']"
						/>
						<!-- Las no leídas van encima del icono: al lado, como en el
						     panel lateral del ordenador, aquí no caben. -->
						<span
							v-if="tab.panel === 'notifications' && unreadCount"
							class="absolute -end-2 -top-1.5 grid h-4 min-w-[1rem] place-items-center rounded-full bg-surface-gray-7 px-1 text-[9px] leading-none text-white"
						>
							{{ unreadCount > 9 ? '9+' : unreadCount }}
						</span>
					</span>
					<span
						class="text-[10px] leading-none"
						:class="[isActive(tab) ? 'text-ink-gray-9' : 'text-ink-gray-5']"
					>
						{{ __(tab.label) }}
					</span>
				</button>
				<button
					class="flex flex-col items-center justify-center gap-1 px-1 py-2.5 transition active:scale-95"
					@click="toggleMenu"
				>
					<component
						:is="icons['List']"
						class="h-5 w-5 stroke-1.5 text-ink-gray-5"
					/>
					<span class="text-[10px] leading-none text-ink-gray-5">
						{{ __('More') }}
					</span>
				</button>
			</div>
		</div>
	</div>
</template>
<script setup>
import { getSidebarLinks } from '@/utils'
import { useRouter } from 'vue-router'
import { call, createResource } from 'frappe-ui'
import { inject, markRaw, onMounted, onUnmounted, ref, watch } from 'vue'
import { sessionStore } from '@/stores/session'
import { useSettings } from '@/stores/settings'
import { usersStore } from '@/stores/user'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import * as icons from 'lucide-vue-next'
import { panelVisible, toggleNotifications } from '@/stores/notifications'

const { logout, user } = sessionStore()
let { isLoggedIn } = sessionStore()
const { sidebarSettings } = useSettings()
const router = useRouter()
let { userResource } = usersStore()
const sidebarLinks = ref([])
const otherLinks = ref([])
const showMenu = ref(false)
const menu = ref(null)
const isModerator = ref(false)
const isInstructor = ref(false)
const socket = inject('$socket')
const unreadCount = ref(0)

// El mismo recurso que usa el panel lateral del ordenador, con su misma clave
// de caché: así, al marcar una notificación como leída, la insignia de la barra
// se entera sin pedir nada más.
const unreadNotifications = createResource({
	cache: 'Unread Notifications Count',
	url: 'frappe.client.get_count',
	makeParams() {
		return {
			doctype: 'Notification Log',
			filters: {
				for_user: user,
				read: 0,
			},
		}
	},
	onSuccess(data) {
		unreadCount.value = data
	},
	auto: user ? true : false,
})

onMounted(() => {
	socket.on('publish_lms_notifications', () => {
		unreadNotifications.reload()
	})
})

onUnmounted(() => {
	socket.off('publish_lms_notifications')
})

const handleOutsideClick = (e) => {
	if (menu.value && !menu.value.contains(e.target)) {
		showMenu.value = false
	}
}

watch(showMenu, (val) => {
	if (val) {
		setTimeout(() => {
			document.addEventListener('click', handleOutsideClick)
		}, 0)
	} else {
		document.removeEventListener('click', handleOutsideClick)
	}
})

const destructureSidebarLinks = () => {
	let links = []
	sidebarLinks.value.forEach((link) => {
		link.items?.forEach((item) => {
			links.push(item)
		})
	})
	sidebarLinks.value = links
}

const filterLinksToShow = (data) => {
	Object.keys(data).forEach((key) => {
		if (!parseInt(data[key])) {
			sidebarLinks.value = sidebarLinks.value.filter(
				(link) => link.label.toLowerCase().split(' ').join('_') !== key
			)
		}
	})
}

const addOtherLinks = async () => {
	if (user) {
		addLink('Profile', 'UserRound')
		await addAyuda()
		addLink('Log out', 'LogOut')
	} else {
		await addAyuda()
		addLink('Log in', 'LogIn')
	}
}

// Los dos WhatsApp. En el móvil no hay panel lateral donde dejarlos siempre a
// la vista, así que van aquí: es el sitio donde se mira cuando algo no
// funciona, justo antes de rendirse y cerrar la aplicación.
const addAyuda = async () => {
	const enlaces = await call('taar_lms.api.enlaces_de_ayuda')
	if (enlaces?.soporte)
		addLink('Soporte', markRaw(WhatsAppIcon), enlaces.soporte)
	// Quién puede ver la comunidad lo decide el servidor, que solo manda el
	// enlace a quien ha pagado. Aquí solo se pinta lo que llegue.
	if (enlaces?.comunidad)
		addLink('Comunidad', markRaw(WhatsAppIcon), enlaces.comunidad)
}

const addLink = (label, icon, to = '') => {
	if (otherLinks.value.some((link) => link.label === label)) return
	otherLinks.value.push({
		label: label,
		icon: icon,
		to: to,
	})
}

const updateSidebarLinks = () => {
	sidebarLinks.value = getSidebarLinks(true)
	destructureSidebarLinks()
	sidebarSettings.reload(
		{},
		{
			onSuccess: async (data) => {
				filterLinksToShow(data)
				await addPrograms()
				if (isModerator.value || isInstructor.value) {
					addQuizzes()
					addAssignments()
					addProgrammingExercises()
				}
				addOtherLinks()
			},
		}
	)
}

const addQuizzes = () => {
	addLink('Quizzes', 'CircleHelp', 'Quizzes')
}

const addAssignments = () => {
	addLink('Assignments', 'Pencil', 'Assignments')
}

const addProgrammingExercises = () => {
	addLink('Programming Exercises', 'Code', 'ProgrammingExercises')
}

const addPrograms = async () => {
	if (sidebarLinks.value.some((link) => link.label === 'Programs')) return
	let canAddProgram = await checkIfCanAddProgram()
	if (!canAddProgram) return
	let activeFor = ['Programs', 'ProgramDetail']
	let index = 1

	sidebarLinks.value.splice(index, 0, {
		label: 'Programs',
		icon: 'Route',
		to: 'Programs',
		activeFor: activeFor,
	})
}

watch(
	userResource,
	async () => {
		await userResource.promise
		if (userResource.data) {
			isModerator.value = userResource.data.is_moderator
			isInstructor.value = userResource.data.is_instructor
		}
		updateSidebarLinks()
	},
	{ immediate: true }
)

const checkIfCanAddProgram = async () => {
	if (!userResource.data) return false
	if (isModerator.value || isInstructor.value) {
		return true
	}
	const programs = await call('lms.lms.utils.get_programs')
	return programs.enrolled.length > 0 || programs.published.length > 0
}

let isActive = (tab) => {
	// Las notificaciones no son una página: están «activas» cuando su panel
	// está abierto.
	if (tab.panel === 'notifications') return panelVisible.value
	return tab.activeFor?.includes(router.currentRoute.value.name)
}

const handleClick = (tab) => {
	if (tab.panel === 'notifications') {
		toggleNotifications()
		if (showMenu.value) toggleMenu()
	} else if (tab.label == 'Log in') window.location.href = '/login'
	else if (tab.label == 'Log out')
		logout.submit().then(() => {
			isLoggedIn = false
		})
	else if (tab.label == 'Profile')
		router.push({
			name: 'Profile',
			params: {
				username: userResource.data?.username,
			},
		})
	else if (tab.to?.startsWith('http')) {
		window.open(tab.to, '_blank')
		toggleMenu()
	} else router.push({ name: tab.to })
}

const isVisible = (tab) => {
	if (tab.label == 'Log in') return !isLoggedIn
	else if (tab.label == 'Log out') return isLoggedIn
	else return true
}

const toggleMenu = () => {
	showMenu.value = !showMenu.value
}
</script>
