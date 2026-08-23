<template>
	<!-- En el móvil sobra: el rastro «Cursos» repite el nombre de la pestaña que
	     ya está marcada en la barra de abajo, y se queda con una franja de
	     pantalla que en un teléfono hace falta. De sm en adelante, igual. -->
	<LayoutHeader class="hidden sm:flex">
		<template #left-header>
			<Breadcrumbs :items="breadcrumbs" />
		</template>
		<template #right-header>
			<Dropdown
				placement="right"
				side="bottom"
				v-if="canCreateCourse()"
				:options="courseMenu"
			>
				<template v-slot="{ open }">
					<Button variant="solid">
						<template #prefix>
							<span class="lucide-plus size-4" />
						</template>
						{{ __('Create') }}
						<template #suffix>
							<span
								:class="[
									'lucide-chevron-down ms-1 size-4 transform transition-transform',
									open ? 'rotate-180' : '',
								]"
							/>
						</template>
					</Button>
				</template>
			</Dropdown>
		</template>
	</LayoutHeader>

	<!-- En móvil la página crece con su contenido; solo en sm+ llena la altura -->
	<div class="flex flex-col p-5 pb-10 sm:min-h-0 sm:flex-1">
		<div
			class="mb-5 flex flex-col justify-between space-y-4 lg:flex-row lg:items-center lg:space-y-0"
		>
			<div class="text-xl-semibold text-ink-gray-9">
				{{ __('All Courses') }}
			</div>
			<!-- gap y no space-y: el selector de categoría viene envuelto en un
			     display:contents, que se come el margen y lo dejaba pegado al
			     buscador. -->
			<div class="flex flex-col gap-4 lg:flex-row lg:items-center">
				<TabButtons :buttons="courseTabs" v-model="currentTab" class="w-fit" />

				<FormControl
					v-model="title"
					:placeholder="__('Search')"
					type="text"
					class="w-full lg:w-40"
					@input="updateCourses()"
				>
					<template #prefix>
						<span class="lucide-search size-4 text-ink-gray-5" />
					</template>
				</FormControl>

				<ClearableCombobox
					v-if="categories.data?.length"
					v-model="currentCategory"
					:options="categories.data.filter((c) => c.value)"
					:placeholder="__('Category')"
					@update:modelValue="updateCourses()"
					class="w-full lg:w-40"
				/>

				<Tooltip
					v-if="settings.data?.certifications"
					:text="__('Only show courses that offer a certificate')"
				>
					<FormControl
						type="checkbox"
						v-model="certification"
						:label="__('Certification')"
						@change="updateCourses()"
					/>
				</Tooltip>
			</div>
		</div>
		<SkeletonLoader
			v-if="courses.list.loading && !courses.data"
			variant="cards"
			:count="8"
		/>
		<div
			v-else-if="courses.data?.length"
			class="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4"
		>
			<template v-for="course in courses.data" :key="course.name">
				<!-- Prelanzamiento: la tarjeta se ve, pero no se abre. Un <div> y
				     no un enlace desactivado a propósito: así no sale el cursor de
				     mano, no se llega con el tabulador y el lector de pantalla no
				     lo canta como enlace. Prometer una puerta que da a una ficha
				     vacía es peor que no ponerla. -->
				<div v-if="esEscaparate(course)">
					<CourseCard :course="course" />
				</div>
				<router-link v-else :to="courseCardRoute(course)">
					<CourseCard :course="course" />
				</router-link>
			</template>
		</div>
		<!-- Esta pantalla es lo primero que ve una alumna al terminar el asistente
		     de bienvenida, así que tiene que estar escrita y no salir a medio
		     traducir. Y "Mis cursos" vacío no significa lo mismo que el catálogo
		     vacío: uno dice "todavía no tienes", el otro "todavía no hay". -->
		<div v-else-if="!courses.list.loading" class="flex-1">
			<EmptyStateLayout
				v-if="currentTab === 'enrolled'"
				icon="lucide-book-open"
				:title="__('You have no courses yet')"
				:description="
					__(
						'As soon as your payment is confirmed they appear here. It usually takes a few seconds.'
					)
				"
			/>
			<EmptyStateLayout
				v-else
				icon="lucide-book-open"
				:title="__('No courses found')"
				:description="
					__('There are no courses right now. New ones are on the way!')
				"
			/>
		</div>
		<div
			v-if="!courses.list.loading && courses.hasNextPage"
			class="flex justify-center mt-5"
		>
			<Button @click="courses.next()">
				{{ __('Load More') }}
			</Button>
		</div>
	</div>
	<NewCourseModal
		v-if="showCourseModal"
		v-model="showCourseModal"
		:courses="courses"
	/>

	<CourseImportModal
		v-if="showCourseImportModal"
		v-model="showCourseImportModal"
	/>
</template>
<script setup>
import {
	Breadcrumbs,
	Button,
	call,
	createListResource,
	Dropdown,
	FormControl,
	TabButtons,
	Tooltip,
	usePageMeta,
} from 'frappe-ui'
import { recordarPagoPendiente } from '@/utils/pagoPendiente'
import ClearableCombobox from '@/components/Controls/ClearableCombobox.vue'
import { computed, inject, onMounted, ref, watch } from 'vue'
import { sessionStore } from '@/stores/session'
import { useSettings } from '@/stores/settings'
import { canCreateCourse, courseCardRoute } from '@/utils'
import CourseCard from '@/components/CourseCard.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import EmptyStateLayout from '@/components/Layouts/EmptyStateLayout.vue'
import LayoutHeader from '@/components/Layouts/LayoutHeader.vue'
import { useRouter } from 'vue-router'
import NewCourseModal from '@/pages/Courses/NewCourseModal.vue'
import CourseImportModal from '@/pages/Courses/CourseImportModal.vue'

const user = inject('$user')
const dayjs = inject('$dayjs')
const start = ref(0)
const pageLength = ref(30)
const currentCategory = ref(null)
const title = ref('')
const certification = ref(false)
const filters = ref({})
const currentTab = ref('live')
const { brand } = sessionStore()
const { settings } = useSettings()
const courseCount = ref(0)
const router = useRouter()
const showCourseModal = ref(false)
const showCourseImportModal = ref(false)

onMounted(() => {
	setFiltersFromQuery()
	updateCourses()
	getCourseCount()

	// Al volver de Stripe con la membresía recién pagada, el identificador de la
	// sesión se guarda en el navegador y el asistente lo recoge desde App.vue.
	// Antes se abría aquí y la dirección se limpiaba a renglón seguido: quien
	// cerraba la ventana sin querer o recargaba se quedaba sin ninguna forma de
	// volver a ella, habiendo pagado ya.
	const queries = new URLSearchParams(location.search)
	if (queries.get('membresia') === 'activada') {
		recordarPagoPendiente(queries.get('session_id'), 'membresia')
		router.replace({ query: { tab: queries.get('tab') || undefined } })
	}
})

const setFiltersFromQuery = () => {
	let queries = new URLSearchParams(location.search)
	title.value = queries.get('title') || ''
	currentCategory.value = queries.get('category') || null
	certification.value = queries.get('certification') || false
	const tab = queries.get('tab')
	if (tab) currentTab.value = tab
	if (queries.get('newCourse') == '1') {
		showCourseModal.value = true
	}
}

const courses = createListResource({
	doctype: 'LMS Course',
	url: 'lms.lms.utils.get_courses',
	cache: ['courses', user.data?.name],
	pageLength: pageLength.value,
	start: start.value,
})

const categories = createListResource({
	doctype: 'LMS Category',
	url: 'lms.lms.utils.get_course_categories',
	cache: ['course_categories'],
	auto: true,
})

const getCourseCount = () => {
	if (!user.data) return
	if (!user.data.is_moderator) return
	call('frappe.client.get_count', {
		doctype: 'LMS Course',
	}).then((data) => {
		courseCount.value = data
	})
}

const updateCourses = () => {
	updateFilters()
	courses.update({
		filters: filters.value,
	})
	courses.reload()
}

const updateFilters = () => {
	updateCategoryFilter()
	updateTitleFilter()
	updateCertificationFilter()
	updateTabFilter()
	updateStudentFilter()
	setQueryParams()
}

const updateCategoryFilter = () => {
	if (currentCategory.value) {
		filters.value['category'] = currentCategory.value
	} else {
		delete filters.value['category']
	}
}

const updateTitleFilter = () => {
	if (title.value) {
		filters.value['title'] = ['like', `%${title.value}%`]
	} else {
		delete filters.value['title']
	}
}

const updateCertificationFilter = () => {
	if (certification.value) {
		filters.value['certification'] = 1
	} else {
		delete filters.value['certification']
	}
}

const updateTabFilter = () => {
	delete filters.value['live']
	delete filters.value['created']
	delete filters.value['published_on']
	delete filters.value['upcoming']

	if (currentTab.value == 'enrolled' && user.data?.is_student) {
		filters.value['enrolled'] = 1
		delete filters.value['published']
	} else {
		delete filters.value['published']
		delete filters.value['enrolled']

		if (currentTab.value == 'live') {
			// Sin `upcoming = 0`: los prelanzamientos entran en el catálogo. Es
			// el servidor quien los aparta de la consulta principal para volver a
			// pegarlos arriba del todo, y así su sitio no depende de la página en
			// la que caigan.
			filters.value['published'] = 1
			filters.value['live'] = 1
		} else if (currentTab.value == 'upcoming') {
			filters.value['upcoming'] = 1
		} else if (currentTab.value == 'new') {
			filters.value['published'] = 1
			filters.value['published_on'] = [
				'>=',
				dayjs().add(-3, 'month').format('YYYY-MM-DD'),
			]
		} else if (currentTab.value == 'created') {
			filters.value['created'] = 1
		} else if (currentTab.value == 'unpublished') {
			filters.value['published'] = 0
		}
	}
}

const updateStudentFilter = () => {
	if (!user.data || (user.data?.is_student && currentTab.value != 'enrolled')) {
		filters.value['published'] = 1
	}
}

const setQueryParams = () => {
	let queries = new URLSearchParams(location.search)
	let filterKeys = {
		title: title.value,
		category: currentCategory.value,
		certification: certification.value,
	}

	Object.keys(filterKeys).forEach((key) => {
		if (filterKeys[key]) {
			queries.set(key, filterKeys[key])
		} else {
			queries.delete(key)
		}
	})

	let queryString = ''
	if (queries.toString()) {
		queryString = `?${queries.toString()}`
	}

	history.replaceState({}, '', `${location.pathname}${queryString}`)
}

watch(currentTab, () => {
	updateCourses()
})

const courseTabs = computed(() => {
	const gestiona =
		user.data?.is_moderator ||
		user.data?.is_instructor ||
		user.data?.is_evaluator

	// "Publicado" solo dice algo frente a "Sin publicar": para el alumno, que
	// nunca ve los borradores, es jerga de administración.
	let tabs = [
		{
			label: gestiona ? __('Published') : __('All courses'),
			value: 'live',
		},
	]
	// "Próximamente" es una herramienta de quien prepara el catálogo. Para la
	// alumna era una pestaña más que casi siempre lleva a una pantalla vacía.
	if (gestiona) {
		tabs.push({ label: __('Upcoming'), value: 'upcoming' })
		tabs.push({ label: __('Created'), value: 'created' })
		tabs.push({ label: __('Unpublished'), value: 'unpublished' })
	} else if (user.data) {
		tabs.push({ label: __('My courses'), value: 'enrolled' })
	}
	return tabs
})

const courseMenu = computed(() => {
	return [
		{
			label: __('New Course'),
			icon: 'book-open',
			onClick() {
				showCourseModal.value = true
			},
		},
		{
			label: __('Import via Data Import Tool'),
			icon: 'upload',
			onClick() {
				router.push({
					name: 'NewDataImport',
					params: { doctype: 'LMS Course' },
				})
			},
		},
		{
			label: __('Import via ZIP'),
			icon: 'folder-plus',
			onClick() {
				showCourseImportModal.value = true
			},
		},
	]
})

// Quien lleva el catálogo entra igual al curso en prelanzamiento: la tarjeta
// apagada es para la alumna, y desde aquí es la única puerta para ir a montarlo.
const gestionaCatalogo = computed(() =>
	Boolean(user.data?.is_moderator || user.data?.is_instructor)
)

const esEscaparate = (course) =>
	Boolean(course.upcoming) && !gestionaCatalogo.value

const breadcrumbs = computed(() => [
	{
		label: __('Courses'),
		route: { name: 'Courses' },
	},
])

usePageMeta(() => {
	return {
		title: __('Courses'),
		icon: brand.favicon,
	}
})
</script>
