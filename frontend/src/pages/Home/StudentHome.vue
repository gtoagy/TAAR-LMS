<template>
	<div>
		<!-- Lo primero de la pantalla cuando hay sesión a la vista: es lo único
		     que tiene hora y se pasa si no se ve a tiempo. Los cursos siguen ahí
		     mañana; la sesión de las seis, no. -->
		<div v-if="proximaSesion" class="mt-8">
			<ProximaSesion
				:sesion="proximaSesion"
				:puedeEntrar="sesionesEnVivo.data?.puede_entrar"
			/>
		</div>

		<div v-if="myCourses.data?.length" class="mt-10">
			<div class="flex items-center justify-between mb-3">
				<span class="font-semibold text-lg text-ink-gray-9">
					{{
						myCourses.data[0].membership
							? __('My Courses')
							: __('Our Popular Courses')
					}}
				</span>
				<router-link
					:to="{
						name: 'Courses',
					}"
				>
					<span class="flex items-center gap-x-1 text-ink-gray-5 text-xs">
						<span>
							{{ __('See all') }}
						</span>
						<span class="lucide-move-right size-3 rtl:rotate-180" />
					</span>
				</router-link>
			</div>
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
				<router-link
					v-for="course in myCourses.data"
					:to="courseCardRoute(course)"
				>
					<CourseCard :course="course" />
				</router-link>
			</div>
		</div>

		<div v-if="myBatches.data?.length" class="mt-10">
			<div class="flex items-center justify-between mb-3">
				<span class="font-semibold text-lg text-ink-gray-9">
					{{
						myBatches.data?.[0].students?.includes(user.data?.name)
							? __('My Batches')
							: __('Our Upcoming Batches')
					}}
				</span>
				<router-link
					:to="{
						name: 'Batches',
					}"
				>
					<span class="flex items-center gap-x-1 text-ink-gray-5 text-xs">
						<span>
							{{ __('See all') }}
						</span>
						<span class="lucide-move-right size-3 rtl:rotate-180" />
					</span>
				</router-link>
			</div>
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
				<router-link
					v-for="batch in myBatches.data"
					:to="{ name: 'BatchDetail', params: { batchName: batch.name } }"
				>
					<BatchCard :batch="batch" />
				</router-link>
			</div>
		</div>
	</div>
</template>
<script setup lang="ts">
import { computed, inject, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import CourseCard from '@/components/CourseCard.vue'
import BatchCard from '@/pages/Batches/components/BatchCard.vue'
import ProximaSesion from '@/components/ProximaSesion.vue'
import { courseCardRoute } from '@/utils'
import { pedirSesiones, sesionesEnVivo } from '@/utils/envivo'

const user = inject<any>('$user')

onMounted(() => pedirSesiones())

const proximaSesion = computed(() => sesionesEnVivo.data?.proxima)

const myCourses = createResource({
	url: 'lms.lms.api.get_my_courses',
	auto: true,
})

const myBatches = createResource({
	url: 'lms.lms.api.get_my_batches',
	auto: true,
})
</script>
