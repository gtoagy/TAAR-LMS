<template>
	<div
		v-if="course.title"
		class="flex flex-col h-full rounded-md overflow-auto text-ink-gray-9 bg-surface-elevation-1"
		style="min-height: 350px"
	>
		<div
			class="relative w-[100%] h-[168px] bg-cover bg-center bg-no-repeat border-t border-x rounded-t-md"
			:style="
				course.image
					? { backgroundImage: `url('${encodeURI(course.image)}')` }
					: {
							backgroundImage: gradientColor,
							backgroundBlendMode: 'screen',
					  }
			"
		>
			<!-- Un curso anunciado antes de tener contenido. Va encima de la
			     portada porque es lo primero que hay que entender de la tarjeta, y
			     con fondo propio para que se lea sobre cualquier foto.

			     Una palabra y no la fecha: en el escritorio la tarjeta baja a un
			     cuarto de pantalla, donde «Disponible a partir del 1 de
			     septiembre» se parte en dos líneas sobre la imagen. La fecha va en
			     la entradilla del curso, que se edita desde su ficha y no envejece
			     dentro del código. -->
			<span
				v-if="course.upcoming"
				class="absolute start-3 top-3 inline-flex items-center gap-x-1 rounded-md border border-outline-amber-1 bg-surface-amber-1 px-2 py-0.5 text-xs font-medium text-ink-amber-6"
			>
				<span class="lucide-clock size-3" />
				{{ __('Pre-launch') }}
			</span>
			<!-- <div class="flex items-center flex-wrap relative top-4 px-2 w-fit">
				<div
					v-if="course.featured"
					class="flex items-center gap-x-1 text-xs text-ink-amber-6 bg-surface-base border border-outline-amber-1 px-2 py-0.5 rounded-md me-1 mb-1"
				>
					<Star class="size-3 stroke-2" />
					<span>
						{{ __('Featured') }}
					</span>
				</div>
				<div
					v-if="course.tags"
					v-for="tag in course.tags?.split(', ')"
					class="text-xs border bg-surface-base text-ink-gray-9 px-2 py-0.5 rounded-md mb-1 me-1"
				>
					{{ tag }}
				</div>
			</div> -->
			<div
				v-if="!course.image"
				class="flex items-center justify-center text-white flex-1 font-extrabold my-auto px-5 text-center leading-6 h-full"
				:class="
					course.title.length > 32
						? 'text-xl'
						: course.title.length > 20
						? 'text-3xl'
						: 'text-4xl'
				"
			>
				{{ course.title }}
			</div>
		</div>
		<div class="flex flex-col flex-auto p-4 border-x-2 border-b-2 rounded-b-md">
			<div class="flex items-center justify-between mb-2">
				<div v-if="course.lessons">
					<Tooltip :text="__('Lessons')">
						<span class="flex items-center">
							<span class="lucide-book-open size-4 me-1" />
							{{ course.lessons }}
						</span>
					</Tooltip>
				</div>

				<div v-if="enrolledLabel">
					<Tooltip :text="__('Enrolled Students')">
						<span class="flex items-center">
							<span class="lucide-users size-4 me-1" />
							{{ enrolledLabel }}
						</span>
					</Tooltip>
				</div>

				<div v-if="Number(course.rating) > 0">
					<Tooltip :text="__('Average Rating')">
						<span class="flex items-center">
							<LucideStar
								class="size-4 me-1 text-transparent fill-yellow-500"
							/>
							{{ formatRating(course.rating) }}
						</span>
					</Tooltip>
				</div>

				<Tooltip v-if="course.featured" :text="__('Featured')">
					<span class="lucide-award size-4 text-ink-amber-6" />
				</Tooltip>
			</div>

			<div
				v-if="course.image"
				class="font-semibold leading-6"
				:class="course.title.length > 32 ? 'text-xl' : 'text-3xl'"
			>
				{{ course.title }}
			</div>

			<div class="short-introduction text-sm">
				{{ course.short_introduction }}
			</div>

			<ProgressBar
				v-if="user && course.membership"
				:progress="course.membership.progress"
			/>

			<div v-if="user && course.membership" class="text-sm mt-2 mb-4">
				{{ Math.ceil(course.membership.progress) }}% {{ __('completed') }}
			</div>

			<!-- Sin el instructor: en esta escuela los da todos la misma persona,
			     así que repetirlo en cada carta no dice nada. En la ficha sigue. -->
			<div class="flex items-center justify-end mt-auto">
				<div class="flex items-center gap-x-2">
					<div
						v-if="priceLabel"
						class="whitespace-nowrap font-semibold"
						:class="
							ventaIndividual && !soloConPlanAnual
								? 'text-base'
								: 'text-xs text-ink-gray-6'
						"
					>
						{{ priceLabel }}
					</div>

					<Tooltip
						v-if="course.paid_certificate || course.enable_certification"
						:text="__('Get Certified')"
					>
						<span class="lucide-graduation-cap size-5 text-ink-gray-7" />
					</Tooltip>
				</div>
			</div>
		</div>
	</div>
</template>
<script setup>
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/user'
import { Tooltip } from 'frappe-ui'
import { formatEnrollments, formatRating } from '@/utils'
import { theme } from '@/utils/theme'
import { computed, watch } from 'vue'
import ProgressBar from '@/components/ProgressBar.vue'
import colors from '@/utils/frappe-ui-colors.json'

const { user } = sessionStore()
const { userResource } = usersStore()

const props = defineProps({
	course: {
		type: Object,
		default: null,
	},
})

const enrolledLabel = computed(() => formatEnrollments(props.course.enrollments))

const ventaIndividual = computed(
	() =>
		Boolean(props.course.taar_venta_individual) &&
		Boolean(props.course.taar_precio_display)
)

// A quien ya paga el plan mensual, el precio suelto no le dice lo que necesita
// saber: ese curso también entra subiendo al anual, y verlo aquí es lo que le
// hace mirar la membresía en vez de irse.
const soloConPlanAnual = computed(
	() =>
		Boolean(props.course.taar_solo_plan_anual) &&
		userResource.data?.taar_plan === 'Mensual'
)

// Lo que ya es suyo no se vuelve a vender: ni el precio ni el recordatorio de
// que la membresía lo cubre le dicen nada nuevo a quien ya entra al curso.
// `user` llega ya desenvuelto (el store es reactive), como en la plantilla.
const yaEsSuyo = computed(() => Boolean(user && props.course.membership))

// Solo los cursos que se pagan aparte llevan precio; el resto se distingue con
// una nota discreta de que la membresía ya los cubre.
const priceLabel = computed(() => {
	if (yaEsSuyo.value) return ''
	if (soloConPlanAnual.value)
		// Con las dos salidas a la vista se entiende que no está fuera de su
		// alcance, y el precio suelto es lo que hace ver barato el plan anual.
		return ventaIndividual.value
			? __('{0} or annual plan').format(props.course.taar_precio_display)
			: __('With the annual plan')
	if (ventaIndividual.value) return props.course.taar_precio_display
	if (props.course.taar_incluido_en_membresia)
		return __('Included in the membership')
	if (props.course.paid_course) return props.course.price
	return ''
})

const gradientColor = computed(() => {
	let themeMode = theme.value === 'dark' ? 'darkMode' : 'lightMode'
	let color = props.course.card_gradient?.toLowerCase() || 'blue'
	let colorMap = colors[themeMode][color]
	return `linear-gradient(to top right, black, ${colorMap[400]})`
})
</script>
<style>
.course-card-pills {
	background: #ffffff;
	margin-left: 0;
	margin-right: 0.5rem;
	padding: 3.5px 8px;
	font-size: 11px;
	text-align: center;
	letter-spacing: 0.011em;
	text-transform: uppercase;
	font-weight: 600;
	width: fit-content;
}

.avatar-group {
	display: inline-flex;
	align-items: center;
}

.avatar-group .avatar {
	transition: margin 0.1s ease-in-out;
}

.avatar-group.overlap .avatar + .avatar {
	margin-inline-start: calc(-8px);
}

.short-introduction {
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	text-overflow: ellipsis;
	width: 100%;
	overflow: hidden;
	margin: 0.25rem 0 1.25rem;
	line-height: 1.5;
}
</style>
