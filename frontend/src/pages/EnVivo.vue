<template>
	<div class="h-full">
		<!-- En el móvil sobra: la barra de abajo ya dice dónde está. -->
		<header
			class="sticky top-0 z-10 hidden items-center justify-between border-b bg-surface-base px-3 py-2.5 sm:flex sm:px-5"
		>
			<Breadcrumbs class="h-7" :items="breadcrumbs" />
		</header>

		<div
			v-if="sesionesEnVivo.loading && !sesionesEnVivo.data"
			class="flex flex-1 items-center justify-center p-5"
		>
			<LoadingIndicator class="size-5 text-ink-gray-5" />
		</div>

		<div v-else class="p-5">
			<div class="mx-auto mt-8 max-w-3xl">
				<div class="mb-8 text-center">
					<div
						class="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-surface-gray-2"
					>
						<Video class="size-6 text-ink-gray-7" />
					</div>
					<h1 class="mb-2 text-2xl font-semibold text-ink-gray-9">
						{{ __('Live sessions') }}
					</h1>
					<p class="text-base text-ink-gray-7">
						{{
							__(
								'We meet to look at how your piece is going and to answer your questions.'
							)
						}}
					</p>

					<!-- Va aquí y no en la cabecera porque la cabecera se esconde en
					     el móvil, y programar una sesión desde el teléfono tiene que
					     poder hacerse igual. -->
					<Button
						v-if="esModerador"
						class="mt-4"
						@click="mostrarProgramar = true"
					>
						<template #prefix>
							<Plus class="size-4" />
						</template>
						{{ __('Schedule a live session') }}
					</Button>
				</div>

				<ProximaSesion
					v-if="proxima"
					:sesion="proxima"
					:puedeEntrar="datos.puede_entrar"
				/>

				<!-- Sin fecha todavía, la sección no se queda muda: decir que se
				     anuncia aquí es lo que evita que vuelvan a buscarla en WhatsApp. -->
				<div
					v-else
					class="rounded-lg border border-outline-gray-2 bg-surface-base p-6 text-center"
				>
					<p class="text-base text-ink-gray-8">
						{{ __('There is no session scheduled right now.') }}
					</p>
					<p class="mt-1 text-sm text-ink-gray-6">
						{{ __('The next one will show up here, and we will email you.') }}
					</p>
				</div>

				<div v-if="anteriores.length" class="mt-10">
					<h2 class="mb-3 text-lg font-semibold text-ink-gray-9">
						{{ __('Past sessions') }}
					</h2>
					<div class="divide-y divide-outline-gray-1 rounded-lg border">
						<a
							v-for="sesion in anteriores"
							:key="sesion.nombre"
							:href="sesion.grabacion"
							target="_blank"
							rel="noopener"
							class="flex items-center justify-between gap-3 px-4 py-3 hover:bg-surface-gray-1"
						>
							<div class="min-w-0">
								<p class="truncate text-base text-ink-gray-9">
									{{ sesion.titulo }}
								</p>
								<p class="text-sm text-ink-gray-5 first-letter:uppercase">
									{{ fechaCorta(sesion) }}
								</p>
							</div>
							<span
								class="flex shrink-0 items-center gap-1 text-sm text-ink-gray-7"
							>
								<Play class="size-4" />
								{{ __('Watch') }}
							</span>
						</a>
					</div>
				</div>
			</div>
		</div>
	</div>

	<ProgramarSesionModal v-if="mostrarProgramar" v-model="mostrarProgramar" />
</template>

<script setup>
import { Breadcrumbs, Button, LoadingIndicator } from 'frappe-ui'
import { Play, Plus, Video } from 'lucide-vue-next'
import { computed, inject, onMounted, ref } from 'vue'
import ProgramarSesionModal from '@/components/ProgramarSesionModal.vue'
import ProximaSesion from '@/components/ProximaSesion.vue'
import { fechaCorta, pedirSesiones, sesionesEnVivo } from '@/utils/envivo'

const user = inject('$user')
const mostrarProgramar = ref(false)

// Esconder el botón no es la protección: `crear_sesion()` vuelve a comprobarlo
// en el servidor. Aquí solo se evita enseñar algo que no lleva a ninguna parte.
const esModerador = computed(() => !!user.data?.is_moderator)

onMounted(() => pedirSesiones())

const datos = computed(() => sesionesEnVivo.data || {})
const proxima = computed(() => datos.value.proxima)
const anteriores = computed(() => datos.value.anteriores || [])

const breadcrumbs = computed(() => [
	{
		label: __('Live sessions'),
		route: { name: 'EnVivo' },
	},
])
</script>
