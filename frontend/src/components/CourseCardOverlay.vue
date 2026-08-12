<template>
	<div class="border-2 rounded-md min-w-80 max-w-sm">
		<VideoPreview
			:video-link="course.data?.video_link"
			:fallback-image="course.data?.image"
		/>
		<div class="p-5">
			<div class="text-4xl-semibold text-ink-gray-9 mb-4">
				{{ priceLabel }}
			</div>
			<div v-if="!readOnlyMode">
				<div v-if="course.data?.membership" class="space-y-2 mb-8">
					<router-link
						:to="{
							name: 'Lesson',
							params: {
								courseName: course.data?.name,
								chapterNumber: course?.data?.current_lesson
									? course?.data?.current_lesson.split('-')[0]
									: 1,
								lessonNumber: course?.data?.current_lesson
									? course?.data?.current_lesson.split('-')[1]
									: 1,
							},
						}"
					>
						<Button variant="solid" size="md" class="w-full">
							<template #prefix>
								<span class="lucide-book-text size-4" />
							</template>
							<span>
								{{ __('Continue Learning') }}
							</span>
						</Button>
					</router-link>
					<CertificationLinks :courseName="course.data.name" class="w-full" />
				</div>
				<Badge
					v-else-if="course.data?.disable_self_learning && !isAdmin"
					theme="blue"
					size="lg"
					class="mb-4"
				>
					{{ __('Contact the Administrator to enroll for this course') }}
				</Badge>
				<div
					v-else-if="protectedCourse && !isAdmin"
					class="space-y-2 mb-8"
				>
					<!-- Curso reservado al plan anual: hay que decirlo antes de que
					     alguien pague el mensual creyendo que lo incluye. -->
					<p
						v-if="soloPlanAnual"
						class="rounded-md bg-surface-gray-2 px-3 py-2 text-sm text-ink-gray-7"
					>
						{{
							__(
								'This course comes with the annual membership. The monthly plan does not include it.'
							)
						}}
					</p>
					<!-- Ya tiene derecho a este curso: avisar antes de que lo pague
					     por segunda vez. -->
					<p
						v-else-if="isMember && !necesitaMejorarPlan"
						class="rounded-md bg-surface-gray-2 px-3 py-2 text-sm text-ink-gray-7"
					>
						{{ __('This course is already included in your membership.') }}
					</p>
					<router-link
						v-if="incluidoEnMembresia && (!isMember || necesitaMejorarPlan)"
						:to="{ name: 'Membresia' }"
						class="block"
					>
						<Button variant="solid" size="md" class="w-full">
							<template #prefix>
								<span class="lucide-crown size-4" />
							</template>
							{{
								necesitaMejorarPlan
									? __('Upgrade to annual')
									: soloPlanAnual
										? __('See the annual membership')
										: __('Become a member')
							}}
						</Button>
					</router-link>
					<Button
						v-if="ventaIndividual"
						:variant="incluidoEnMembresia ? 'subtle' : 'solid'"
						size="md"
						class="w-full"
						@click="comprarCurso()"
					>
						<template #prefix>
							<span class="lucide-credit-card size-4" />
						</template>
						{{ __('Buy this course') }}
					</Button>
					<p
						v-if="ventaIndividual"
						class="text-sm text-ink-gray-5 text-center"
					>
						{{ __('One-time payment, lifetime access.') }}
					</p>
				</div>
				<Button
					v-else-if="!isAdmin"
					@click="enrollStudent()"
					variant="solid"
					class="w-full mb-8"
					size="md"
				>
					<template #prefix>
						<span class="lucide-book-text size-4" />
					</template>
					<span>
						{{ __('Enroll Now') }}
					</span>
				</Button>
				<Button
					v-if="canGetCertificate"
					@click="fetchCertificate()"
					variant="subtle"
					class="w-full mt-2"
					size="md"
				>
					<template #prefix>
						<span class="lucide-graduation-cap size-4" />
					</template>
					{{ __('Get Certificate') }}
				</Button>
			</div>
			<section v-if="hasCourseStats" class="space-y-3">
				<div class="text-base text-ink-gray-9 mb-1">
					{{ __('This course includes:') }}
				</div>
				<div
					v-if="enrolledLabel"
					class="flex items-center gap-3 text-ink-gray-8"
				>
					<span class="lucide-users size-4 shrink-0 text-ink-gray-7" />
					<span>{{ enrolledLabel }} {{ __('enrolled') }}</span>
				</div>
				<div
					v-if="course.data?.video_link"
					class="flex items-center gap-3 text-ink-gray-8"
				>
					<span class="lucide-monitor-play size-4 shrink-0 text-ink-gray-7" />
					<span>{{ __('On demand course video') }}</span>
				</div>
				<div
					v-if="course.data?.lessons"
					class="flex items-center gap-3 text-ink-gray-8"
				>
					<span class="lucide-book-open size-4 shrink-0 text-ink-gray-7" />
					<span>
						{{ course.data?.lessons }}
						{{ course.data?.lessons === 1 ? __('Lesson') : __('Lessons') }}
					</span>
				</div>
				<div
					v-if="(course.data?.quiz_count || 0) > 0"
					class="flex items-center gap-3 text-ink-gray-8"
				>
					<span class="lucide-help-circle size-4 shrink-0 text-ink-gray-7" />
					<span>
						{{ course.data?.quiz_count }}
						{{
							course.data?.quiz_count === 1
								? __('Quiz topic')
								: __('Quiz topics')
						}}
					</span>
				</div>
				<div
					v-if="course.data?.enable_certification"
					class="flex items-center gap-3 text-ink-gray-8"
				>
					<span class="lucide-award size-4 shrink-0 text-ink-gray-7" />
					<span>{{ __('Certificate of completion') }}</span>
				</div>
			</section>
		</div>
	</div>
</template>
<script setup lang="ts">
import { computed, inject, watch } from 'vue'
import { Badge, Button, call, createResource, toast } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { formatEnrollments } from '@/utils'
import CertificationLinks from '@/components/CertificationLinks.vue'
import VideoPreview from '@/components/VideoPreview.vue'
import { useTelemetry } from 'frappe-ui/frappe'
import type {
	CourseDetails,
	CourseInstructorInfo,
	Resource,
	SessionUser,
} from '@/types/api'

const router = useRouter()
const user = inject<SessionUser>('$user')!
const readOnlyMode = (window as Window & { read_only_mode?: boolean })
	.read_only_mode
const { capture } = useTelemetry()

const props = withDefaults(
	defineProps<{
		course: Resource<CourseDetails | null>
	}>(),
	{}
)

function enrollStudent() {
	if (!user.data) {
		toast.warning(__('You need to login first to enroll for this course'))
		setTimeout(() => {
			window.location.href = `/login?redirect-to=${window.location.pathname}`
		}, 500)
		return
	}
	const courseName = props.course.data?.name
	if (!courseName) return
	call('frappe.client.insert', {
		doc: {
			doctype: 'LMS Enrollment',
			course: courseName,
			member: user.data.name,
		},
	})
		.then(() => {
			capture('enrolled_in_course', { course: courseName })
			toast.success(__('You have been enrolled in this course'))
			setTimeout(() => {
				router.push({
					name: 'Lesson',
					params: {
						courseName,
						chapterNumber: 1,
						lessonNumber: 1,
					},
				})
			}, 1000)
		})
		.catch((err: { messages?: string[] } | string) => {
			const msg = typeof err === 'string' ? err : err.messages?.[0] ?? 'Error'
			toast.warning(__(msg))
			console.error(err)
		})
}

const is_instructor = (): boolean => {
	let user_is_instructor = false
	props.course.data?.instructors.forEach((instructor: CourseInstructorInfo) => {
		if (!user_is_instructor && instructor.name == user.data?.name) {
			user_is_instructor = true
		}
	})
	return user_is_instructor
}

interface CourseAccessInfo {
	venta_individual: boolean
	incluido_en_membresia: boolean
	price_display: string | null
	is_member: boolean
	enrolled: boolean
}

const accessInfo = createResource({
	url: 'taar_lms.api.get_course_access_info',
	makeParams() {
		return { curso: props.course.data?.name }
	},
}) as Resource<CourseAccessInfo | null>

watch(
	() => props.course.data?.name,
	(name) => {
		if (name) accessInfo.reload()
	},
	{ immediate: true }
)

const ventaIndividual = computed<boolean>(() =>
	Boolean(accessInfo.data?.venta_individual)
)
const incluidoEnMembresia = computed<boolean>(() =>
	Boolean(accessInfo.data?.incluido_en_membresia)
)
const isMember = computed<boolean>(() => Boolean(accessInfo.data?.is_member))
const soloPlanAnual = computed<boolean>(() =>
	Boolean(accessInfo.data?.solo_plan_anual)
)
// Miembro cuyo plan no llega a este curso: no le sirve "hacerse miembro", ya lo es.
const necesitaMejorarPlan = computed<boolean>(
	() => isMember.value && !accessInfo.data?.cubierto_por_mi_plan
)
const protectedCourse = computed<boolean>(
	() => ventaIndividual.value || incluidoEnMembresia.value
)

function comprarCurso() {
	// Los invitados también pueden comprar: pagan en Stripe y la cuenta
	// se crea sola con el email del pago.
	const courseName = props.course.data?.name
	if (!courseName) return
	capture('buy_course_clicked', { course: courseName })
	// Misma puerta que los botones de la landing; al cancelar en Stripe se
	// vuelve a la ficha del curso, que es desde donde se hizo clic.
	const volver = encodeURIComponent(`/lms/courses/${courseName}`)
	window.location.href = `/comprar/curso/${encodeURIComponent(
		courseName
	)}?volver=${volver}`
}

const priceLabel = computed<string>(() => {
	if (ventaIndividual.value && accessInfo.data?.price_display) {
		return accessInfo.data.price_display
	}
	if (incluidoEnMembresia.value) return __('Included in the membership')
	if (protectedCourse.value) return ''
	if (props.course.data?.paid_course) return props.course.data?.price || ''
	return __('Free')
})

const enrolledLabel = computed<string>(() =>
	formatEnrollments(props.course.data?.enrollments)
)

const hasCourseStats = computed<boolean>(() =>
	Boolean(
		enrolledLabel.value ||
			props.course.data?.video_link ||
			props.course.data?.lessons ||
			(props.course.data?.quiz_count ?? 0) > 0 ||
			props.course.data?.enable_certification
	)
)

const canGetCertificate = computed<boolean>(() => {
	return Boolean(
		props.course.data?.enable_certification &&
			(props.course.data?.membership?.progress ?? 0) >= 100
	)
})

const certificate = createResource({
	url: 'lms.lms.doctype.lms_certificate.lms_certificate.create_certificate',
	makeParams(values: { course?: string }) {
		return {
			course: values.course,
		}
	},
	onSuccess(data: { name: string; template: string }) {
		window.open(
			`/api/method/frappe.utils.print_format.download_pdf?doctype=LMS+Certificate&name=${
				data.name
			}&format=${encodeURIComponent(data.template)}`,
			'_blank'
		)
	},
}) as Resource<{ name: string; template: string } | null>

const fetchCertificate = () => {
	certificate.submit({
		course: props.course.data?.name,
		member: user.data?.name,
	})
}

const isAdmin = computed<boolean>(() => {
	return Boolean(user.data?.is_moderator) || is_instructor()
})
</script>
