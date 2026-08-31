<template>
	<div v-if="lesson.data" class="">
		<header
			v-if="!embedded"
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-base px-3 py-2.5 sm:px-5"
		>
			<!-- Una flecha en vez del rastro "Cursos / Curso / Lección": en el
			     móvil no cabía y se partía por la mitad, y en cualquier tamaño
			     dice lo mismo con menos ruido. Sube a la ficha del curso, que es
			     el escalón de arriba, y enseña el nombre del curso, que es lo
			     único que se perdía al quitar el rastro. -->
			<router-link
				:to="{ name: 'CourseDetail', params: { courseName: courseName } }"
				class="flex min-w-0 items-center gap-2 hover:opacity-70"
			>
				<span
					class="lucide-arrow-left size-5 shrink-0 text-ink-gray-7 rtl:rotate-180"
				/>
				<span class="truncate text-p-base font-medium text-ink-gray-9">
					{{ lesson.data.course_title }}
				</span>
			</router-link>
			<div class="flex items-center gap-x-2">
				<Tooltip v-if="canGoZen() && isAdmin" :text="__('Zen Mode')">
					<Button @click="goFullScreen()">
						<template #icon>
							<span class="lucide-focus size-4" />
						</template>
					</Button>
				</Tooltip>
				<CertificationLinks :courseName="courseName" />
				<!-- El temario, a un toque. En pantalla ancha vive en su columna. -->
				<Button
					class="md:hidden"
					:label="__('Course content')"
					@click="mostrarTemario = true"
				>
					<template #icon>
						<span class="lucide-list size-4 text-ink-gray-7" />
					</template>
				</Button>
			</div>
		</header>
		<div
			:class="
				embedded
					? 'grid grid-cols-1 h-full'
					: 'grid grid-cols-1 md:grid-cols-[70%,30%] md:h-[94vh]'
			"
		>
			<div v-if="lesson.data.no_preview" class="border-e">
				<div class="shadow rounded-md w-3/4 mt-10 mx-auto text-center p-4">
					<div class="flex items-center justify-center mt-4 gap-x-2">
						<span class="lucide-lock-keyhole size-4 text-ink-gray-5" />
						<div class="text-xl-semibold text-ink-gray-7">
							{{ __('This lesson is locked') }}
						</div>
					</div>
					<div class="mt-1 mb-4 text-ink-gray-7">
						{{ __('You do not have access to this course yet.') }}
					</div>
					<!-- A la ficha del curso, que es donde están todas las salidas:
					     entrar con la membresía, subir de plan o comprarlo suelto. El
					     botón anterior intentaba inscribir en el acto y en un curso de
					     pago solo devolvía un error, dejando a quien llegaba aquí sin
					     ningún camino. -->
					<div class="flex items-center justify-center gap-x-2">
						<router-link
							:to="{
								name: 'CourseDetail',
								params: { courseName: courseName },
							}"
						>
							<Button variant="solid">
								{{ __('View the course') }}
							</Button>
						</router-link>
						<Button v-if="!user.data" @click="redirectToLogin()">
							<template #prefix>
								<span class="lucide-log-in size-4" />
							</template>
							{{ __('Login') }}
						</Button>
					</div>
					<Badge
						theme="blue"
						size="lg"
						v-if="lesson.data.disable_self_learning"
						class="mt-4"
					>
						{{ __('Contact the Administrator to enroll for this course.') }}
					</Badge>
				</div>
			</div>
			<div
				v-else
				ref="lessonContainer"
				class="bg-surface-base"
				:class="{
					'overflow-y-auto': zenModeEnabled,
				}"
			>
				<div
					class="border-e pt-5 pb-10 h-full"
					:class="{
						'w-full md:w-3/5 mx-auto border-none !pt-10': zenModeEnabled,
					}"
				>
					<div class="px-5">
						<div
							class="flex flex-col space-y-3 md:space-y-0 md:flex-row md:items-center justify-between"
						>
							<div class="flex flex-col">
								<div class="text-5xl-semibold text-ink-gray-9">
									{{ lesson.data.title }}
								</div>

								<div
									v-if="zenModeEnabled"
									class="relative flex items-center gap-x-2 text-sm text-ink-gray-7 group w-fit mt-2"
								>
									<span>
										{{ lesson.data.chapter_title }} -
										{{ lesson.data.course_title }}
									</span>
									<span class="lucide-info size-3" />
									<div
										class="hidden group-hover:block rounded bg-surface-gray-10 px-2 py-1 text-xs text-ink-base shadow-xl absolute start-0 top-full mt-2"
									>
										{{ Math.ceil(lesson.data.membership.progress) }}%
										{{ __('completed') }}
									</div>
								</div>
							</div>

							<div
								v-if="!zenModeEnabled"
								class="flex items-center gap-x-2 mt-2 md:mt-0"
							>
								<router-link
									v-if="isAdmin && !embedded"
									:to="{
										name: 'CourseDetail',
										params: { courseName: courseName },
										hash: '#course editor',
										query: {
											editLesson: `${chapterNumber}-${lessonNumber}`,
											lessonMode: 'edit',
										},
									}"
								>
									<Button>
										<template #prefix>
											<span class="lucide-pencil size-4" />
										</template>
										{{ __('Edit') }}
									</Button>
								</router-link>
								<Tooltip v-else-if="canGoZen()" :text="__('Zen Mode')">
									<Button @click="goFullScreen()">
										<template #icon>
											<span class="lucide-focus size-4" />
										</template>
									</Button>
								</Tooltip>
								<BotonLeccionCompleta
									v-if="lesson.data.membership"
									:lesson="lesson.data.name"
									:course="courseName"
									:completada="leccionCompletada"
									@marcada="alMarcarAMano"
									@desmarcada="alDesmarcar"
								/>
								<Button v-if="lesson.data.prev" @click="switchLesson('prev')">
									<template #prefix>
										<span class="lucide-chevron-left size-4" />
									</template>
									<span>{{ __('Previous') }}</span>
								</Button>
								<Button v-if="lesson.data.next" @click="switchLesson('next')">
									<template #suffix>
										<span class="lucide-chevron-right size-4" />
									</template>
									<span>{{ __('Next') }}</span>
								</Button>
								<router-link
									v-else
									:to="{
										name: 'CourseDetail',
										params: { courseName: courseName },
									}"
								>
									<Button @click="markProgress()">
										{{ __('Back to Course') }}
									</Button>
								</router-link>
							</div>

							<div
								v-if="zenModeEnabled"
								class="flex items-center gap-x-2 mt-2 md:mt-0"
							>
								<Button @click="showDiscussionsInZenMode()">
									<template #icon>
										<span class="lucide-message-circle-question size-4" />
									</template>
								</Button>
								<BotonLeccionCompleta
									v-if="lesson.data.membership"
									:lesson="lesson.data.name"
									:course="courseName"
									:completada="leccionCompletada"
									@marcada="alMarcarAMano"
									@desmarcada="alDesmarcar"
								/>
								<Button v-if="lesson.data.prev" @click="switchLesson('prev')">
									<template #prefix>
										<span class="lucide-chevron-left size-4" />
									</template>
									<span>
										{{ __('Previous') }}
									</span>
								</Button>

								<Button v-if="lesson.data.next" @click="switchLesson('next')">
									<template #suffix>
										<span class="lucide-chevron-right size-4" />
									</template>
									<span>
										{{ __('Next') }}
									</span>
								</Button>

								<router-link
									v-else
									:to="{
										name: 'CourseDetail',
										params: { courseName: courseName },
									}"
								>
									<Button @click="markProgress()">
										{{ __('Back to Course') }}
									</Button>
								</router-link>
							</div>
						</div>

						<!-- Fuera en el móvil: quien está dentro de una lección ya sabe
					     de quién es el curso, y ahí cada línea que sobra empuja el
					     vídeo hacia abajo. -->
					<div
						v-if="!zenModeEnabled"
						class="hidden md:flex items-center mt-4 md:mt-2"
					>
							<span
								class="h-6 me-1"
								:class="{
									'avatar-group overlap': lesson.data.instructors?.length > 1,
								}"
							>
								<UserAvatar
									v-for="instructor in lesson.data.instructors"
									:user="instructor"
								/>
							</span>
							<CourseInstructors
								v-if="lesson.data?.instructors"
								:instructors="lesson.data.instructors"
							/>
						</div>

						<div
							v-if="
								lesson.data.instructor_content &&
								JSON.parse(lesson.data.instructor_content)?.blocks?.length >
									1 &&
								allowInstructorContent()
							"
							class="bg-surface-gray-2 p-3 rounded-md mt-6"
						>
							<div class="text-ink-gray-5 font-medium">
								{{ __('Instructor Notes') }}
							</div>
							<div
								id="instructor-content"
								class="ProseMirror prose prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-outline-gray-2 prose-th:border-outline-gray-2 prose-td:relative prose-th:relative prose-th:bg-surface-gray-2 prose-sm max-w-none !whitespace-normal"
							></div>
						</div>
						<div
							v-else-if="lesson.data.instructor_notes"
							class="ProseMirror prose prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-outline-gray-2 prose-th:border-outline-gray-2 prose-td:relative prose-th:relative prose-th:bg-surface-gray-2 prose-sm max-w-none !whitespace-normal mt-8"
						>
							<LessonContent :content="lesson.data.instructor_notes" />
						</div>
						<div
							v-if="lesson.data.content"
							@mouseup="toggleInlineMenu"
							class="ProseMirror prose prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-outline-gray-2 prose-th:border-outline-gray-2 prose-td:relative prose-th:relative prose-th:bg-surface-gray-2 prose-sm max-w-none !whitespace-normal mt-8"
						>
							<div id="editor"></div>
						</div>
						<div
							v-else
							class="ProseMirror prose prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-outline-gray-2 prose-th:border-outline-gray-2 prose-td:relative prose-th:relative prose-th:bg-surface-gray-2 prose-sm max-w-none !whitespace-normal mt-8"
						>
							<LessonContent
								v-if="lesson.data?.body"
								:content="lesson.data.body"
								:youtube="lesson.data.youtube"
								:quizId="lesson.data.quiz_id"
							/>
						</div>
					</div>
					<div
						v-if="lesson.data && (allowDiscussions || tabs.length > 1)"
						class="mt-10 pb-5 pt-5 sm:pb-20 border-t px-5"
						ref="discussionsContainer"
					>
						<TabButtons
							v-if="tabs.length > 1"
							:buttons="tabs"
							v-model="currentTab"
							class="w-fit mb-10"
						/>
						<Notes
							v-if="currentTab === 'Notes'"
							:lesson="lesson.data?.name"
							v-model:notes="notes"
							@updateNotes="updateNotes"
						/>
						<Discussions
							v-else-if="allowDiscussions"
							:title="'Questions'"
							:newLabel="__('Ask a question')"
							:doctype="'Course Lesson'"
							:docname="lesson.data.name"
							:key="lesson.data.name"
							:emptyStateText="
								__('Ask a question to get help from the community.')
							"
						/>
					</div>
				</div>
			</div>
			<!-- Columna fija en pantalla ancha. En el móvil ya no cuelga del final
			     de la página —donde había que pasar las notas y las preguntas para
			     llegar a él—: ahora sale del botón de la barra. -->
			<div v-if="!embedded" class="hidden md:sticky md:top-10 md:block md:h-[94vh]">
				<StudentLessonSidebar
					:courseName="courseName"
					:courseTitle="lesson.data.course_title"
					:progress="lessonProgress"
					:selectedLessonNumber="`${chapterNumber}-${lessonNumber}`"
					:completedLesson="completedLesson"
					:uncompletedLesson="uncompletedLesson"
					:withProgress="lesson.data.membership ? true : false"
				/>
			</div>
		</div>
	</div>
	<PanelLateral v-if="lesson.data && !embedded" v-model="mostrarTemario">
		<StudentLessonSidebar
			:courseName="courseName"
			:courseTitle="lesson.data.course_title"
			:progress="lessonProgress"
			:selectedLessonNumber="`${chapterNumber}-${lessonNumber}`"
			:completedLesson="completedLesson"
			:uncompletedLesson="uncompletedLesson"
			:withProgress="lesson.data.membership ? true : false"
		/>
	</PanelLateral>
	<InlineLessonMenu
		v-if="lesson.data?.name"
		v-model="showInlineMenu"
		:lesson="lesson.data?.name"
		v-model:notes="notes"
		@updateNotes="updateNotes"
	/>
	<VideoStatistics
		v-if="isAdmin"
		v-model="showStatsDialog"
		:lessonName="lesson.data?.name"
		:lessonTitle="lesson.data?.title"
	/>
</template>
<script setup>
import {
	Badge,
	Button,
	call,
	createListResource,
	createResource,
	TabButtons,
	Tooltip,
	usePageMeta,
} from 'frappe-ui'
import {
	computed,
	watch,
	inject,
	ref,
	onMounted,
	onBeforeUnmount,
	nextTick,
} from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
	getEditorTools,
	enablePlyr,
	highlightText,
	sanitizeEditorJs,
} from '@/utils'
import { sessionStore } from '@/stores/session'
import { useSidebar } from '@/stores/sidebar'
import { useSettings } from '@/stores/settings'
import {
	resolveDwellSeconds,
	resolveVideoPercent,
	isVideoComplete,
	shouldStartDwellTimer,
	shouldAttachVideoFallback,
} from '@/utils/lessonProgress'
import BotonLeccionCompleta from '@/components/BotonLeccionCompleta.vue'
import EditorJS from '@editorjs/editorjs'
import LessonContent from '@/components/LessonContent.vue'
import CourseInstructors from '@/components/CourseInstructors.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import Discussions from '@/components/Discussions.vue'
import CertificationLinks from '@/components/CertificationLinks.vue'
import VideoStatistics from '@/components/Modals/VideoStatistics.vue'
import { hasVideoContent } from '@/utils/video'
import CourseOutline from '@/components/CourseOutline.vue'
import PanelLateral from '@/components/PanelLateral.vue'
import StudentLessonSidebar from '@/components/StudentLessonSidebar.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Notes from '@/components/Notes/Notes.vue'
import InlineLessonMenu from '@/components/Notes/InlineLessonMenu.vue'
import { getLmsRoute } from '@/utils/basePath'
import { useScreenSize } from '@/utils/composables'

const { isMobile } = useScreenSize()

const user = inject('$user')
const socket = inject('$socket')
const router = useRouter()
const route = useRoute()
const allowDiscussions = ref(false)
const editor = ref(null)
const instructorEditor = ref(null)
const lessonProgress = ref(0)
const lessonContainer = ref(null)
const zenModeEnabled = ref(false)
const showStatsDialog = ref(false)
const hasQuiz = ref(false)
const discussionsContainer = ref(null)
const timer = ref(0)
const { brand } = sessionStore()
const sidebarStore = useSidebar()
const plyrSources = ref([])
const showInlineMenu = ref(false)
const mostrarTemario = ref(false)
const currentTab = ref(null)
const completedLesson = ref(null)
// La otra cara de `completedLesson`: la lección que se acaba de desmarcar, para
// que el panel pueda apagar su palomita sin recargar el temario entero.
const uncompletedLesson = ref(null)
// Estado de la lección en pantalla. Vive aparte de `lesson.data.progress`
// porque ese valor lo trae el servidor al cargar y no se mueve después: sin
// esto, el `timeupdate` del vídeo —que salta cuatro veces por segundo— lanzaría
// una ráfaga de peticiones sobre una lección ya marcada.
const leccionCompletada = ref(false)
const settingsStore = useSettings()
let timerInterval = null

const tabs = ref([])

const props = defineProps({
	courseName: {
		type: String,
		required: true,
	},
	chapterNumber: {
		type: String,
		required: true,
	},
	lessonNumber: {
		type: String,
		required: true,
	},
	embedded: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits([
	'select-lesson',
	'lesson-completed',
	'progress-updated',
])

// Exposed for the parent so the CourseEditor preview can render the same
// Prev / Next / Zen-mode controls as the student header but place them in
// the page-level LayoutHeader instead of inside the lesson body.
defineExpose({
	switchLesson: (direction) => switchLesson(direction),
	goFullScreen: () => goFullScreen(),
	canGoZen: () => canGoZen(),
	hasPrev: computed(() => Boolean(lesson.data?.prev)),
	hasNext: computed(() => Boolean(lesson.data?.next)),
	lessonHasVideo: () => lessonHasVideo.value,
	showVideoStats: () => showVideoStats(),
	lessonName: () => lesson.data?.name,
	lessonTitle: () => lesson.data?.title,
})

let collapsedByLesson = false
const isCourseAdmin = () =>
	Boolean(user.data?.is_moderator || user.data?.is_instructor)

onMounted(() => {
	startTimer()
	marcarPrimeraLeccion()
	// Keep the app sidebar open for admins/instructors so they can navigate
	// while reviewing; only collapse it for students to maximise reading space.
	if (!props.embedded && !isCourseAdmin()) {
		sidebarStore.isSidebarCollapsed = true
		collapsedByLesson = true
	}
	document.addEventListener('fullscreenchange', attachFullscreenEvent)
	socket.on('update_lesson_progress', (data) => {
		if (data.course === props.courseName) {
			lessonProgress.value = data.progress
			emit('progress-updated', data.progress)
		}
	})
})

// Que una alumna llegue a abrir una lección es el último escalón del embudo, y
// el que de verdad importa: es la diferencia entre haber pagado y haber
// empezado. No sirve mirar el progreso del curso, porque ese registro solo nace
// cuando la lección se termina —al acabarse el vídeo—, no al abrirla.
//
// La marca en el navegador evita llamar al servidor cada vez que abre una
// lección durante meses: al servidor solo le interesa la primera.
const marcarPrimeraLeccion = () => {
	const CLAVE = 'taar-primera-leccion'
	try {
		if (localStorage.getItem(CLAVE)) return
		localStorage.setItem(CLAVE, '1')
	} catch (e) {
		/* sin almacenamiento se llama igual: es idempotente en el servidor */
	}
	call('taar_lms.api.marcar_paso', { paso: 'leccion' }).catch(() => {})
}

const attachFullscreenEvent = () => {
	if (document.fullscreenElement) {
		zenModeEnabled.value = true
		allowDiscussions.value = false
	} else {
		zenModeEnabled.value = false
		if (!hasQuiz.value) {
			allowDiscussions.value = true
		}
	}
}

onBeforeUnmount(() => {
	document.removeEventListener('fullscreenchange', attachFullscreenEvent)
	if (!props.embedded && collapsedByLesson)
		sidebarStore.isSidebarCollapsed = false
	trackVideoWatchDuration()
})

const lesson = createResource({
	url: 'lms.lms.utils.get_lesson',
	makeParams(values) {
		return {
			course: props.courseName,
			chapter: values ? values.chapter : props.chapterNumber,
			lesson: values ? values.lesson : props.lessonNumber,
		}
	},
	auto: true,
})

const setupLesson = (data) => {
	if (Object.keys(data).length === 0) {
		router.push({
			name: 'CourseDetail',
			params: { courseName: props.courseName },
		})
		return
	}
	if (data.is_scorm_package) {
		router.push({
			name: 'SCORMChapter',
			params: {
				courseName: props.courseName,
				chapterName: data.chapter_name,
			},
		})
	}
	lessonProgress.value = data.membership?.progress
	if (data.content) editor.value = renderEditor('editor', data.content)
	if (
		data.instructor_content &&
		JSON.parse(data.instructor_content)?.blocks?.length > 1
	)
		instructorEditor.value = renderEditor(
			'instructor-content',
			data.instructor_content
		)
	editor.value?.isReady.then(() => {
		checkIfDiscussionsAllowed()
	})
	checkQuiz()
}

const checkQuiz = () => {
	if (!editor.value && lesson.body) {
		const quizRegex = /\{\{ Quiz\(".*"\) \}\}/
		hasQuiz.value = quizRegex.test(lesson.body)
		if (!hasQuiz.value && !zenModeEnabled) {
			allowDiscussions.value = true
		} else {
			allowDiscussions.value = false
		}
	}
}

const renderEditor = (holder, content) => {
	if (document.getElementById(holder))
		document.getElementById(holder).innerHTML = ''
	return new EditorJS({
		holder: holder,
		tools: getEditorTools(),
		data: sanitizeEditorJs(JSON.parse(content)),
		readOnly: true,
		defaultBlock: 'embed',
		i18n: {
			direction: document.documentElement.dir === 'rtl' ? 'rtl' : 'ltr',
		},
	})
}

// Video-ended fires markProgress + trackVideoWatchDuration in parallel,
// and trackVideoWatchDuration's getPlyrSourceDetails calls markProgress
// again. Without an in-flight guard the two save_progress requests race
// and the second one fails with TimestampMismatchError on LMS Enrollment.
let progressSubmitting = false
// Qué lección se está guardando ahora mismo. Hace falta porque "Siguiente"
// marca y navega en el mismo gesto: cuando el servidor contesta, `lesson.data`
// ya es la lección de al lado, y sin esto la palomita caería sobre ella.
let leccionEnVuelo = null
const markProgress = () => {
	if (progressSubmitting) return
	// Only enrolled students record progress; a moderator previewing has no
	// membership row so save_progress would no-op server-side but still
	// flip the in-memory `completedLesson` and show a green tick that
	// vanishes on refresh.
	if (
		!user.data ||
		!lesson.data ||
		!lesson.data.membership ||
		leccionCompletada.value
	)
		return
	progressSubmitting = true
	leccionEnVuelo = lesson.data.name
	progress.submit(
		{},
		{
			onSuccess() {
				progressSubmitting = false
			},
			onError(err) {
				progressSubmitting = false
				console.error(err)
			},
		}
	)
}

const progress = createResource({
	url: 'lms.lms.doctype.course_lesson.course_lesson.save_progress',
	makeParams() {
		return {
			lesson: lesson.data.name,
			course: props.courseName,
		}
	},
	onSuccess(data) {
		lessonProgress.value = data
		const name = leccionEnVuelo
		// El porcentaje es del curso entero y vale siempre; lo demás solo si
		// seguimos en la lección que se marcó.
		if (name === lesson.data?.name) leccionCompletada.value = true
		uncompletedLesson.value = null
		completedLesson.value = name
		// Tell the parent (CourseEditor preview) so it can flip the
		// sidebar's green tick and update the percentage without waiting
		// for a refresh of the course resource.
		if (name) emit('lesson-completed', name)
		emit('progress-updated', data)
	},
})

// El botón manual habla con el servidor por su cuenta y vuelve con el
// porcentaje ya recalculado; aquí solo hay que repartirlo por la pantalla.
const alMarcarAMano = (data) => {
	const name = lesson.data?.name
	lessonProgress.value = data.progress
	leccionCompletada.value = true
	uncompletedLesson.value = null
	completedLesson.value = name
	if (name) emit('lesson-completed', name)
	emit('progress-updated', data.progress)
}

const alDesmarcar = (data) => {
	lessonProgress.value = data.progress
	leccionCompletada.value = false
	completedLesson.value = null
	uncompletedLesson.value = lesson.data?.name
	emit('progress-updated', data.progress)
}

const notes = createListResource({
	doctype: 'LMS Lesson Note',
	filters: {
		lesson: lesson.data?.name,
		member: user.data?.name,
	},
	fields: ['name', 'color', 'highlighted_text', 'note'],
	cache: ['notes', lesson.data?.name, user.data?.name],
	onSuccess(data) {
		data.forEach((note) => {
			setTimeout(() => {
				highlightText(note)
			}, 500)
		})
	},
})

const switchLesson = (direction) => {
	trackVideoWatchDuration()
	// Pasar de lección cuenta como haberla terminado. Hacia atrás no: volver
	// sobre lo anterior no es haber avanzado.
	if (direction === 'next') markProgress()
	let lessonIndex =
		direction === 'prev'
			? lesson.data.prev.split('.')
			: lesson.data.next.split('.')

	const [chapterNumber, lessonNumber] = lessonIndex
	// In the embedded editor preview, navigate the parent's selection so the
	// pane swaps in place instead of routing away to /lesson/...
	if (props.embedded) {
		emit('select-lesson', { chapterNumber, lessonNumber })
		return
	}

	router.push({
		name: 'Lesson',
		params: {
			courseName: props.courseName,
			chapterNumber,
			lessonNumber,
		},
	})
}

watch(
	[() => route.params.chapterNumber, () => route.params.lessonNumber],
	async (
		[newChapterNumber, newLessonNumber],
		[oldChapterNumber, oldLessonNumber]
	) => {
		if (newChapterNumber || newLessonNumber) {
			plyrSources.value = []
			await nextTick()
			resetLessonState(newChapterNumber, newLessonNumber)
			updateNotes()
			checkIfDiscussionsAllowed()
			checkQuiz()
		}
	}
)

const resetLessonState = (newChapterNumber, newLessonNumber) => {
	editor.value = null
	instructorEditor.value = null
	allowDiscussions.value = false
	lesson.submit({
		chapter: newChapterNumber,
		lesson: newLessonNumber,
	})
	videoFallbackArmed = false
	fallbackGeneration++
	clearInterval(timerInterval)
	timer.value = 0
	// El estado de la lección anterior no vale para la que entra; el watch de
	// `lesson.data` lo repone en cuanto el servidor contesta.
	leccionCompletada.value = false
	uncompletedLesson.value = null
}

const trackVideoWatchDuration = () => {
	if (!lesson.data?.membership) return
	let videoDetails = getVideoDetails()
	videoDetails = videoDetails.concat(getPlyrSourceDetails())
	call('lms.lms.api.track_video_watch_duration', {
		lesson: lesson.data.name,
		videos: videoDetails,
	})
}

// Cuánto hay que ver de un vídeo para darlo por visto. Configurable en Ajustes
// porque el final de un vídeo casi nunca es contenido: son la despedida y los
// créditos, y exigir el último segundo dejaba lecciones sin cerrar.
const umbralVideo = computed(() =>
	resolveVideoPercent(settingsStore.settings?.data?.video_completion_percent)
)

const getVideoDetails = () => {
	let details = []
	const videos = document.querySelectorAll('video')
	if (videos.length > 0) {
		videos.forEach((video) => {
			if (isVideoComplete(video.currentTime, video.duration, umbralVideo.value))
				markProgress()
			details.push({
				source: video.src,
				watch_time: video.currentTime,
			})
		})
	}
	return details
}

const getPlyrSourceDetails = () => {
	let details = []
	plyrSources.value.forEach((source) => {
		if (isVideoComplete(source.currentTime, source.duration, umbralVideo.value))
			markProgress()
		let src = cleanYouTubeUrl(source.source)
		details.push({
			source: src,
			watch_time: source.currentTime,
		})
	})
	return details
}

const cleanYouTubeUrl = (url) => {
	if (!url) return url
	const urlObj = new URL(url)
	urlObj.searchParams.delete('t')
	return urlObj.toString()
}

watch(
	() => lesson.data,
	async (data) => {
		// Se elige una lección desde el panel y el panel se aparta solo: dejarlo
		// abierto sobre la lección recién abierta obliga a cerrarlo a mano.
		mostrarTemario.value = false
		leccionCompletada.value = Boolean(data?.progress)
		setupLesson(data)
		// Settings drive dwell + enforcement; if they haven't resolved yet
		// the timer reads undefined and falls back to 30s. Await the
		// resource so the admin-configured dwell time wins from the first
		// lesson load.
		if (settingsStore.settings?.promise) {
			try {
				await settingsStore.settings.promise
			} catch {}
		}
		startTimer()
		await getPlyrSource()
		updateNotes()
		const hasVideoListener =
			plyrSources.value.length > 0 || !!document.querySelector('video')
		const enforceVideo = Number(
			settingsStore.settings?.data?.enforce_video_completion ?? 0
		)
		// When the lesson has video AND enforcement is on, suppress dwell so
		// completion is gated on play-to-end. When enforcement is off, dwell
		// runs for every lesson type — including YouTube/Plyr — so admins can
		// set a short dwell to mark video lessons complete without a full
		// playthrough.
		if (!shouldStartDwellTimer({ hasVideo: hasVideoListener, enforceVideo })) {
			clearInterval(timerInterval)
		}
		if (
			shouldAttachVideoFallback({ hasVideo: hasVideoListener, enforceVideo })
		) {
			document.querySelectorAll('video').forEach((video) => {
				if (video._lmsErrorAttached) return
				video._lmsErrorAttached = true
				const gen = fallbackGeneration
				video.addEventListener(
					'error',
					() => {
						if (gen !== fallbackGeneration) return
						fallbackToDwellTimer('html5-video-error')
					},
					{ once: true }
				)
			})
		}
	}
)

const getPlyrSource = async () => {
	await nextTick()
	if (plyrSources.value.length == 0) {
		plyrSources.value = await enablePlyr()
		const enforceVideo = Number(
			settingsStore.settings?.data?.enforce_video_completion ?? 0
		)
		if (
			shouldAttachVideoFallback({
				hasVideo: plyrSources.value.length > 0,
				enforceVideo,
			})
		) {
			plyrSources.value.forEach((player) => {
				let readyFired = false
				const gen = fallbackGeneration
				player.on('ready', () => {
					readyFired = true
				})
				player.on('error', (event) => {
					if (gen !== fallbackGeneration) return
					fallbackToDwellTimer(
						'plyr-error: ' + (event?.detail?.message || 'unknown')
					)
				})
				setTimeout(() => {
					if (gen !== fallbackGeneration) return
					if (videoYaCargado(player, readyFired)) return
					fallbackToDwellTimer('plyr-sin-cargar-' + ESPERA_VIDEO / 1000 + 's')
				}, ESPERA_VIDEO)
			})
		}
	}
	updateVideoWatchDuration()
}

const updateVideoWatchDuration = () => {
	if (lesson.data.videos && lesson.data.videos.length > 0) {
		lesson.data.videos.forEach((video) => {
			if (video.source.includes('youtube') || video.source.includes('vimeo')) {
				updatePlyrVideoTime(video)
			} else {
				updateVideoTime(video)
			}
		})
	}
	attachVideoEndedListeners()
}

const attachVideoEndedListeners = () => {
	const onVideoEnded = () => {
		markProgress()
		trackVideoWatchDuration()
	}

	// El umbral se mira mientras el vídeo corre, no solo al terminarlo: si se
	// comprobara únicamente al salir de la lección, quien ve el noventa por
	// ciento y se queda ahí no vería nunca aparecer su palomita. `markProgress`
	// ya se protege sola de repetirse, que es lo que hace esto viable con un
	// evento que salta cuatro veces por segundo.
	const onTimeUpdate = (player) => {
		if (isVideoComplete(player.currentTime, player.duration, umbralVideo.value))
			markProgress()
	}

	document.querySelectorAll('video').forEach((video) => {
		if (!video._lmsEndedAttached) {
			video.addEventListener('ended', onVideoEnded)
			video.addEventListener('timeupdate', () => onTimeUpdate(video))
			video._lmsEndedAttached = true
		}
	})

	plyrSources.value.forEach((plyrSource) => {
		if (!plyrSource._lmsEndedAttached) {
			plyrSource.on('ended', onVideoEnded)
			plyrSource.on('timeupdate', () => onTimeUpdate(plyrSource))
			plyrSource.on('statechange', (event) => {
				if (event.detail?.code === 0) onVideoEnded()
			})
			plyrSource._lmsEndedAttached = true
		}
	})
}

const updatePlyrVideoTime = (video) => {
	plyrSources.value.forEach((plyrSource) => {
		let lastWatchedTime = 0
		let isSeeking = false

		plyrSource.on('ready', () => {
			if (plyrSource.source === video.source) {
				plyrSource.embed.seekTo(video.watch_time, true)
				plyrSource.play()
				plyrSource.pause()
			}
		})
	})
}

const updateVideoTime = (video) => {
	const videos = document.querySelectorAll('video')
	if (videos.length > 0) {
		videos.forEach((vid) => {
			if (vid.src === video.source) {
				let watch_time = video.watch_time < vid.duration ? video.watch_time : 0
				if (vid.readyState >= 1) {
					vid.currentTime = watch_time
				} else {
					vid.addEventListener('loadedmetadata', () => {
						vid.currentTime = watch_time
					})
				}
			}
		})
	}
}

// Cuánto se espera antes de dar un vídeo por perdido. Los vídeos de la escuela
// están alojados en Vimeo, y con datos móviles el reproductor tarda: quince
// segundos se quedaban cortos y el aviso saltaba con el vídeo ya en pantalla.
const ESPERA_VIDEO = 30000

/**
 * Si el reproductor ya tiene el vídeo, mire por donde se mire.
 *
 * No basta con esperar el evento `ready`: Plyr no lo vuelve a emitir si el
 * reproductor ya estaba listo cuando nos suscribimos, así que hay que
 * preguntarle por su estado. Y si sabe cuánto dura el vídeo es que lo cargó
 * —esa duración se la acaba de decir Vimeo—, que es la prueba definitiva.
 */
const videoYaCargado = (player, readyFired) => {
	if (readyFired || player?.ready) return true
	const duracion = Number(player?.duration)
	return Number.isFinite(duracion) && duracion > 0
}

let videoFallbackArmed = false
let fallbackGeneration = 0

/**
 * Pasa a marcar la lección por tiempo. En silencio, a propósito.
 *
 * Antes esto avisaba con un "el vídeo no se pudo cargar". El aviso salía en el
 * teléfono con el vídeo reproduciéndose delante, porque los vídeos viven dentro
 * de un marco de Vimeo y desde fuera no hay forma fiable de saber qué pasa ahí
 * dentro: cualquier tropiezo del reproductor llegaba aquí como un fallo.
 *
 * Y aunque fuera cierto, el aviso no le sirve a quien lo lee: no puede hacer
 * nada con esa información. Lo que necesita es escribir, y para eso tiene el
 * Soporte en el panel. Lo que de verdad la protege es esto de aquí abajo —que
 * su lección se marque igual—, y eso sigue funcionando.
 *
 * `reason` se queda en la consola: si algún día hay que investigar de verdad
 * por qué un vídeo no carga, ahí está el rastro.
 */
const fallbackToDwellTimer = (reason) => {
	// Solo importa para una alumna inscrita cuyo progreso se está siguiendo: en
	// la vista previa del editor no hay nada que marcar.
	if (props.embedded || !lesson.data?.membership) return
	if (videoFallbackArmed) return
	videoFallbackArmed = true
	console.warn('[Lesson] video fallback engaged:', reason)
	clearInterval(timerInterval)
	timer.value = 0
	startTimer()
}

const startTimer = () => {
	if (!lesson.data?.membership) return
	const dwell = resolveDwellSeconds(
		settingsStore.settings?.data?.lesson_dwell_time
	)
	if (dwell === null) return
	timerInterval = setInterval(() => {
		timer.value++
		if (timer.value >= dwell) {
			clearInterval(timerInterval)
			markProgress()
		}
	}, 1000)
}

onBeforeUnmount(() => {
	clearInterval(timerInterval)
})

const checkIfDiscussionsAllowed = () => {
	hasQuiz.value = false
	if (lesson.data?.content) {
		try {
			JSON.parse(lesson.data.content)?.blocks?.forEach((block) => {
				if (block.type === 'quiz') {
					hasQuiz.value = true
				}
			})
		} catch {
			// legacy markdown lessons
		}
	}

	if (
		!hasQuiz.value &&
		!zenModeEnabled.value &&
		(lesson.data?.membership ||
			user.data?.is_moderator ||
			user.data?.is_instructor)
	) {
		allowDiscussions.value = true
	} else {
		allowDiscussions.value = false
	}
}

const isAdmin = computed(() => {
	let isInstructor = lesson.data?.instructors?.includes(user.data?.name)
	return user.data?.is_moderator || isInstructor
})

// The video-statistics button only makes sense when the lesson actually has a
// video; showing it for text-only lessons opened an empty modal and logged a
// console error.
const lessonHasVideo = computed(() => hasVideoContent(lesson.data))

const allowInstructorContent = () => {
	if (window.read_only_mode) return false
	return isAdmin.value
}

const toggleInlineMenu = async () => {
	showInlineMenu.value = false
	await nextTick()
	let selection = window.getSelection()
	if (selection.toString()) {
		showInlineMenu.value = true
	}
}

const showVideoStats = () => {
	showStatsDialog.value = true
}

const canGoZen = () => {
	// En el teléfono la pantalla completa no cambia nada: el navegador ya ocupa
	// todo el alto, así que el botón solo ocupa sitio en una fila apretada.
	if (isMobile.value) return false
	if (
		user.data?.is_moderator ||
		user.data?.is_instructor ||
		user.data?.is_evaluator
	)
		return true
	if (lesson.data?.membership) return true
	return false
}

const goFullScreen = () => {
	if (lessonContainer.value.requestFullscreen) {
		lessonContainer.value.requestFullscreen()
	} else if (lessonContainer.value.mozRequestFullScreen) {
		lessonContainer.value.mozRequestFullScreen()
	} else if (lessonContainer.value.webkitRequestFullscreen) {
		lessonContainer.value.webkitRequestFullscreen()
	} else if (lessonContainer.value.msRequestFullscreen) {
		lessonContainer.value.msRequestFullscreen()
	}
}

const showDiscussionsInZenMode = () => {
	if (allowDiscussions.value) {
		allowDiscussions.value = false
	} else {
		allowDiscussions.value = true
		currentTab.value = 'Community'
		scrollDiscussionsIntoView()
	}
}

const scrollDiscussionsIntoView = () => {
	nextTick(() => {
		discussionsContainer.value?.scrollIntoView({
			behavior: 'smooth',
			block: 'center',
			inline: 'nearest',
		})
	})
}

const updateNotes = () => {
	if (!user.data) return
	notes.update({
		filters: {
			lesson: lesson.data?.name,
			member: user.data?.name,
		},
	})
	notes.reload()
}

watch(allowDiscussions, () => {
	if (!isAdmin.value) {
		if (!tabs.value.find((tab) => tab.value === 'Notes')) {
			tabs.value.push({
				label: __('Notes'),
				value: 'Notes',
			})
		}
		currentTab.value = 'Notes'
	} else {
		currentTab.value = allowDiscussions.value ? 'Community' : null
	}
	if (allowDiscussions.value) {
		if (!tabs.value.find((tab) => tab.value === 'Community')) {
			// "Comunidad" prometía otra cosa —un foro, gente— cuando lo que hay
			// debajo son las dudas de esa lección. Y ahora hay una Comunidad de
			// verdad en el panel lateral, que es el grupo de WhatsApp.
			tabs.value.push({
				label: __('Questions'),
				value: 'Community',
			})
		}
	}
})

const redirectToLogin = () => {
	window.location.href = `/login?redirect-to=${getLmsRoute(
		`courses/${props.courseName}`
	)}`
}

usePageMeta(() => {
	return {
		title: lesson?.data?.title,
		icon: brand.favicon,
	}
})
</script>
<style>
.avatar-group {
	display: inline-flex;
	align-items: center;
}

.avatar-group .avatar {
	transition: margin 0.1s ease-in-out;
}

.lesson-content p {
	margin-bottom: 1rem;
	line-height: 1.7;
}

.lesson-content li {
	line-height: 1.7;
}

.lesson-content ol {
	list-style: auto;
	margin: revert;
	padding: 1rem;
}

.lesson-content ul {
	list-style: auto;
	padding: 1rem;
	margin: revert;
}

.lesson-content img {
	border: 1px solid theme('colors.gray.200');
	border-radius: 0.5rem;
}

.lesson-content code {
	display: block;
	overflow-x: auto;
	padding: 1rem 1.25rem;
	background: #011627;
	color: #d6deeb;
	border-radius: 0.5rem;
	margin: 1rem 0;
}

.lesson-content a {
	color: theme('colors.gray.900');
	text-decoration: underline;
	font-weight: 500;
}

.embed-tool__caption,
.cdx-simple-image__caption {
	display: none;
}

.ce-block__content {
	max-width: unset;
}

.codex-editor__redactor {
	padding-bottom: 0px !important;
}

.codeBoxHolder {
	display: flex;
	flex-direction: column;
	justify-content: flex-start;
	align-items: flex-start;
}

.codeBoxTextArea {
	width: 100%;
	min-height: 30px;
	padding: 10px;
	border-radius: 2px 2px 2px 0;
	border: none !important;
	outline: none !important;
	font: 14px monospace;
}

.codeBoxSelectDiv {
	display: flex;
	flex-direction: column;
	justify-content: flex-start;
	align-items: flex-start;
	position: relative;
}

.codeBoxSelectInput {
	border-radius: 0 0 20px 2px;
	padding: 2px 26px;
	padding-top: 0;
	padding-inline-end: 0;
	text-align: start;
	cursor: pointer;
	border: none !important;
	outline: none !important;
}

.codeBoxSelectDropIcon {
	position: absolute !important;
	inset-inline-start: 10px !important;
	bottom: 0 !important;
	width: unset !important;
	height: unset !important;
	font-size: 16px !important;
}

.codeBoxSelectPreview {
	display: none;
	flex-direction: column;
	justify-content: flex-start;
	align-items: flex-start;
	border-radius: 2px;
	box-shadow: 0 3px 15px -3px rgba(13, 20, 33, 0.13);
	position: absolute;
	top: 100%;
	margin: 5px 0;
	max-height: 30vh;
	overflow-x: hidden;
	overflow-y: auto;
	z-index: 10000;
}

.codeBoxSelectItem {
	width: 100%;
	padding: 5px 20px;
	margin: 0;
	cursor: pointer;
}

.codeBoxSelectItem:hover {
	opacity: 0.7;
}

.codeBoxSelectedItem {
	background-color: lightblue !important;
}

.codeBoxShow {
	display: flex !important;
}

.dark {
	color: #abb2bf;
	background-color: #282c34;
}

.light {
	color: #383a42;
	background-color: #fafafa;
}

.codeBoxTextArea {
	line-height: 1.7;
}

.tc-table {
	border-inline-start: 1px solid #e8e8eb;
}

.plyr__volume input[type='range'] {
	display: none;
}

.plyr__control--overlaid {
	background: radial-gradient(
		circle,
		rgba(0, 0, 0, 0.4) 0%,
		rgba(0, 0, 0, 0.5) 50%
	);
}

.plyr__control:hover {
	background: none;
}

.plyr--video {
	border: 1px solid theme('colors.gray.200');
	border-radius: 8px;
}

:root {
	--plyr-range-fill-background: white;
	--plyr-video-control-background-hover: transparent;
}
</style>
