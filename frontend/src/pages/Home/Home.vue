<template>
	<div class="w-full px-5 pt-5 pb-10">
		<div class="space-y-2">
			<div class="flex items-center justify-between">
				<div class="text-3xl-bold text-ink-gray-9">
					{{ __('Hey') }}, {{ user.data?.full_name }} 👋
				</div>
				<div>
					<Tooltip v-if="!isAdmin" :text="__('Days in a row learning')">
						<div
							@click="showStreakModal = true"
							class="bg-surface-amber-2 px-2 py-1 rounded-md cursor-pointer"
						>
							<span> 🔥 </span>
							<span class="text-ink-gray-9">
								{{ streakInfo.data?.current_streak }}
							</span>
						</div>
					</Tooltip>
				</div>
			</div>

			<div class="text-xl text-ink-gray-6 leading-6">
				{{ subtitle }}
			</div>
		</div>

		<div
			v-if="isHomeLoading"
			class="flex flex-1 items-center justify-center py-20"
		>
			<LoadingIndicator class="size-5 text-ink-gray-5" />
		</div>
		<AdminHome
			v-else-if="isAdmin && currentTab === 'instructor'"
			:liveClasses="adminLiveClasses"
			:evals="adminEvals"
		/>
		<StudentHome v-else-if="currentTab === 'student'" />
	</div>
	<Streak v-model="showStreakModal" :streakInfo="streakInfo" />
</template>
<script setup lang="ts">
import { computed, inject, onMounted, ref } from 'vue'
import {
	call,
	createResource,
	LoadingIndicator,
	Tooltip,
	usePageMeta,
} from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { useRouter } from 'vue-router'
import StudentHome from '@/pages/Home/StudentHome.vue'
import AdminHome from '@/pages/Home/AdminHome.vue'
import Streak from '@/pages/Home/Streak.vue'

const user = inject<any>('$user')
const { brand } = sessionStore()
const router = useRouter()
const currentTab = ref<'student' | 'instructor'>('student')
const showStreakModal = ref(false)

const isAdmin = computed(() => {
	return (
		user.data?.is_moderator ||
		user.data?.is_instructor ||
		user.data?.is_evaluator
	)
})

const isHomeLoading = computed(() => {
	// El alumno no espera nada aquí: sus cursos los carga StudentHome.
	if (!isAdmin.value) return false
	return (
		(adminLiveClasses.loading && !adminLiveClasses.data) ||
		(adminEvals.loading && !adminEvals.data)
	)
})

const isPersonaCaptured = async () => {
	let persona = await call('frappe.client.get_single_value', {
		doctype: 'LMS Settings',
		field: 'persona_captured',
	})
	return persona
}

const identifyUserPersona = async () => {
	if (user.data?.is_system_manager && !user.data?.developer_mode) {
		let personaCaptured = await isPersonaCaptured()
		if (personaCaptured) return
		let courseCount = await call('frappe.client.get_count', {
			doctype: 'LMS Course',
			filters: {
				title: ['not like', '%A guide to Frappe Learning%'],
			},
		})
		if (!courseCount) {
			router.push({ name: 'PersonaForm' })
		}
	}
}

onMounted(() => {
	identifyUserPersona()
	if (isAdmin.value) {
		currentTab.value = 'instructor'
	} else {
		currentTab.value = 'student'
	}
})

const adminLiveClasses = createResource({
	url: 'lms.lms.api.get_admin_live_classes',
	auto: isAdmin.value ? true : false,
})

const adminEvals = createResource({
	url: 'lms.lms.api.get_admin_evals',
	auto: isAdmin.value ? true : false,
})

const streakInfo = createResource({
	url: 'lms.lms.api.get_streak_info',
	auto: true,
})

const subtitle = computed(() => {
	if (isAdmin.value) {
		let liveClassSuffix =
			adminLiveClasses.data?.length > 1 ? __('live classes') : __('live class')
		let evalSuffix =
			adminEvals.data?.length > 1 ? __('evaluations') : __('evaluation')
		if (adminLiveClasses.data?.length > 0 && adminEvals.data?.length > 0) {
			return __('You have {0} upcoming {1} and {2} {3} scheduled.').format(
				adminLiveClasses.data.length,
				liveClassSuffix,
				adminEvals.data.length,
				evalSuffix
			)
		} else if (adminLiveClasses.data?.length > 0) {
			return __('You have {0} upcoming {1}.').format(
				adminLiveClasses.data.length,
				liveClassSuffix
			)
		} else if (adminEvals.data?.length > 0) {
			return __('You have {0} {1} scheduled.').format(
				adminEvals.data.length,
				evalSuffix
			)
		}
		return __('Manage your courses and batches at a glance')
	}
	return __('Resume where you left off')
})

usePageMeta(() => {
	return {
		title: __('Home'),
		icon: brand.favicon,
	}
})
</script>
