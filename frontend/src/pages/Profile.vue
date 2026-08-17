<template>
	<NoPermission v-if="!$user.data" />
	<div v-else-if="profile.data">
		<header
			class="sticky group top-0 z-10 flex flex-col md:flex-row md:items-center justify-between border-b bg-surface-base px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs class="h-7" :items="breadcrumbs" />
			<Button v-if="isSessionUser()" class="invisible group-hover:visible">
				<template #icon>
					<span
						class="lucide-refresh-ccw size-4 text-ink-gray-7"
						@click="reloadUser()"
					/>
				</template>
			</Button>
		</header>
		<div class="group relative h-[130px] w-full">
			<img
				v-if="profile.data.cover_image"
				:src="profile.data.cover_image"
				class="h-[130px] w-full object-cover object-center"
			/>
			<div
				v-else
				:class="{ 'bg-surface-gray-2': !profile.data.cover_image }"
				class="h-[130px] w-full"
			></div>
			<!-- Siempre a la vista en el móvil: el botón aparecía solo al pasar el
			     ratón por encima, y en un teléfono no hay ratón, así que la
			     portada no había forma de cambiarla desde ahí. -->
			<!-- En el móvil se aparta a la esquina: sobre una portada de 130px, un
			     botón con texto en mitad de la foto tapa justo lo que se está
			     eligiendo. En el ordenador se queda centrado y sale al pasar el
			     ratón, que ahí no estorba. -->
			<div
				class="absolute bottom-3 end-3 flex gap-x-2 opacity-100 transition-opacity md:bottom-0 md:end-auto md:start-1/2 md:mb-4 md:-translate-x-1/2 md:opacity-0 focus-within:opacity-100 md:group-hover:opacity-100"
				v-if="isSessionUser()"
			>
				<!-- Directo al selector de archivos. Antes se abría un desplegable
				     donde había que elegir entre buscar una foto de archivo por
				     palabra clave o subir la propia; en una escuela de arte, la
				     foto siempre es una obra suya, así que el desvío sobraba. -->
				<FileUploader
					v-if="!readOnlyMode"
					:fileTypes="['image/*']"
					:validateFile="validarPortada"
					@success="(file) => coverImage.submit({ url: file.file_url })"
				>
					<template v-slot="{ progress, uploading, openFileSelector }">
						<Button
							class="shadow-sm md:hidden"
							variant="outline"
							:loading="uploading"
							:title="__('Change cover')"
							@click="openFileSelector"
						>
							<template #icon>
								<span class="lucide-image-up size-4 text-ink-gray-7" />
							</template>
						</Button>
						<Button
							class="hidden md:inline-flex"
							variant="outline"
							:loading="uploading"
							@click="openFileSelector"
						>
							<template #prefix>
								<span class="lucide-image-up size-4 text-ink-gray-7" />
							</template>
							{{ uploading ? `${progress}%` : __('Change cover') }}
						</Button>
					</template>
				</FileUploader>
			</div>
		</div>
		<div class="mx-auto -mt-10 md:-mt-4 max-w-4xl translate-x-0 px-5">
			<div class="flex flex-col md:flex-row items-center">
				<div>
					<div class="relative">
						<img
							v-if="profile.data.user_image"
							:src="profile.data.user_image"
							class="object-cover h-[100px] w-[100px] rounded-full border-4 border-white object-cover"
						/>
						<div
							v-else
							class="flex items-center justify-center h-[100px] w-[100px] rounded-full border-4 border-white bg-surface-gray-2 text-5xl-semibold text-ink-gray-7"
						>
							{{ profile.data.full_name.charAt(0).toUpperCase() }}
						</div>
						<Tooltip
							v-if="profile.data.open_to"
							:text="
								profile.data.open_to === 'Work'
									? __('Open to Work')
									: __('Hiring')
							"
							placement="right"
						>
							<div
								class="absolute bottom-3 end-1 p-0.5 bg-surface-base rounded-full"
							>
								<div
									class="rounded-full w-fit"
									:class="
										profile.data.open_to === 'Work'
											? 'bg-surface-green-3'
											: 'bg-purple-500'
									"
								>
									<span class="lucide-badge-check text-ink-base size-5" />
								</div>
							</div>
						</Tooltip>
					</div>
				</div>
				<div class="ms-6 mt-5">
					<h2 class="text-5xl-semibold text-ink-gray-9">
						{{ profile.data.full_name }}
					</h2>
					<!-- Sin titular ni LinkedIn: aquí no se busca trabajo. -->
					<div class="flex items-center gap-x-4 mt-2">
						<Instagram
							v-if="profile.data.instagram"
							class="size-4 text-ink-gray-5 cursor-pointer"
							@click="navigateTo(profile.data.instagram)"
						/>
					</div>
				</div>
				<Button
					v-if="isSessionUser() && !readOnlyMode"
					class="mt-3 sm:mt-0 md:ms-auto"
					@click="editProfile()"
				>
					<template #prefix>
						<span class="lucide-edit size-4 text-ink-gray-7" />
					</template>
					{{ __('Edit Profile') }}
				</Button>
			</div>

			<div class="mb-4 mt-10">
				<TabButtons
					class="inline-block"
					:buttons="getTabButtons()"
					v-model="activeTab"
				/>
			</div>
			<router-view :profile="profile" :key="profile.data?.name" />
		</div>
	</div>
	<EditProfile
		v-model="showProfileModal"
		v-model:reloadProfile="profile"
		:profile="profile"
	/>
</template>
<script setup>
import {
	Breadcrumbs,
	Button,
	call,
	createResource,
	FileUploader,
	TabButtons,
	Tooltip,
	toast,
	usePageMeta,
} from 'frappe-ui'
import { computed, inject, watch, ref, onMounted, watchEffect } from 'vue'
import { sessionStore } from '@/stores/session'
import { Instagram } from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import { convertToTitleCase } from '@/utils'
import UserAvatar from '@/components/UserAvatar.vue'
import NoPermission from '@/components/NoPermission.vue'
import EditProfile from '@/components/Modals/EditProfile.vue'

const { user, brand } = sessionStore()
const $user = inject('$user')
const route = useRoute()
const router = useRouter()
const activeTab = ref('')
const showProfileModal = ref(false)
const readOnlyMode = window.read_only_mode

const props = defineProps({
	username: {
		type: String,
		required: true,
	},
})

onMounted(() => {
	if ($user.data) profile.reload()
	setActiveTab()
})

const profile = createResource({
	url: 'lms.lms.api.get_profile_details',
	makeParams() {
		return {
			username: props.username,
		}
	},
})

const coverImage = createResource({
	url: 'frappe.client.set_value',
	makeParams(values) {
		return {
			doctype: 'User',
			name: profile.data?.name,
			fieldname: 'cover_image',
			value: values.url,
		}
	},
	onSuccess() {
		profile.reload()
	},
})

const validarPortada = (file) => {
	const extension = file.name.split('.').pop().toLowerCase()
	if (!['jpg', 'jpeg', 'png', 'webp'].includes(extension)) {
		return __('Only image file is allowed.')
	}
}

const setActiveTab = () => {
	let fragments = route.path.split('/')
	let sections = ['certificates', 'roles', 'slots', 'schedule']
	sections.forEach((section) => {
		if (fragments.includes(section)) {
			activeTab.value = convertToTitleCase(section)
		}
	})
	if (!activeTab.value) activeTab.value = 'About'
}

watchEffect(() => {
	if (activeTab.value) {
		let route = {
			About: { name: 'ProfileAbout' },
			Certificates: { name: 'ProfileCertificates' },
			Roles: { name: 'ProfileRoles' },
			Slots: { name: 'ProfileEvaluator' },
			Schedule: { name: 'ProfileEvaluationSchedule' },
		}[activeTab.value]
		router.push(route)
	}
})

watch(
	() => props.username,
	() => {
		profile.reload()
	}
)

const editProfile = () => {
	showProfileModal.value = true
}

const isSessionUser = () => {
	return $user.data?.name === profile.data?.name
}

const currentUserHasHigherAccess = () => {
	return $user.data?.is_evaluator || $user.data?.is_moderator
}

const isEvaluatorOrModerator = () => {
	return (
		profile.data?.roles?.includes('Batch Evaluator') ||
		profile.data?.roles?.includes('Moderator')
	)
}

const getTabButtons = () => {
	let buttons = [
		{ label: __('About'), value: 'About' },
		{ label: __('Certificates'), value: 'Certificates' },
	]
	if ($user.data?.is_moderator) {
		buttons.push({ label: __('Roles'), value: 'Roles' })
	}

	if (currentUserHasHigherAccess() && isEvaluatorOrModerator()) {
		buttons.push({ label: __('Slots'), value: 'Slots' })
		buttons.push({ label: __('Schedule'), value: 'Schedule' })
	}
	return buttons
}

const reloadUser = () => {
	call('frappe.sessions.clear')
		.then(() => {
			$user.reload().then(() => {
				profile.reload()
				toast.success(__('Session refreshed successfully'))
			})
		})
		.catch((err) => {
			toast.error(__('Failed to refresh session'))
			console.error(err)
		})
}

const navigateTo = (url) => {
	window.open(url, '_blank')
}

const breadcrumbs = computed(() => {
	let crumbs = [
		{
			label: __('People'),
		},
		{
			label: profile.data?.full_name,
			route: {
				name: 'Profile',
				params: {
					username: user.doc?.username,
				},
			},
		},
	]
	return crumbs
})

usePageMeta(() => {
	return {
		title: profile.data?.full_name,
		icon: brand.favicon,
	}
})
</script>
