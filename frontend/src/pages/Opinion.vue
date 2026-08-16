<template>
	<div class="h-full">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-base px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs class="h-7" :items="breadcrumbs" />
		</header>

		<!-- Cargando: hasta que el servidor no dice quién es, no se enseña ni el
		     formulario ni el "no estás invitada". Enseñar cualquiera de los dos
		     antes de tiempo es prometer o negar un descuento a ciegas. -->
		<div
			v-if="invitacion.loading && !invitacion.data"
			class="flex flex-1 items-center justify-center p-5"
		>
			<LoadingIndicator class="size-5 text-ink-gray-5" />
		</div>

		<div v-else class="p-5">
			<div class="mx-auto mt-8 max-w-2xl">
				<!-- Enviada: agradecimiento -->
				<div v-if="resultado" class="text-center">
					<div
						class="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-surface-gray-2"
					>
						<Heart class="size-6 text-ink-gray-7" />
					</div>
					<h1 class="mb-2 text-2xl font-semibold text-ink-gray-9">
						{{ __('Thank you for writing to us!') }}
					</h1>
					<!-- El descuento puede tardar en cuadrar con la suscripción, y eso
					     no es un problema de ella: se le cuenta igual de bien en los dos
					     casos, nunca como un fallo. -->
					<p class="text-base text-ink-gray-7">
						<template v-if="resultado.descuento_aplicado">
							{{
								__(
									'Your {0}% discount is already applied. You will see it in your next {1} payments.'
								).format(porcentaje, meses)
							}}
						</template>
						<template v-else>
							{{
								__(
									'Your {0}% discount for {1} months is on its way. You will see it very soon.'
								).format(porcentaje, meses)
							}}
						</template>
					</p>
					<!-- El servidor manda además su propio `mensaje`, pero dice lo mismo
					     que acabamos de decir aquí arriba: enseñar los dos hace que
					     parezca que algo falló y que hay que leerlo dos veces. -->
					<router-link :to="{ name: 'Courses' }" class="mt-8 inline-block">
						<Button variant="solid" size="md">
							{{ __('Go to my courses') }}
						</Button>
					</router-link>
				</div>

				<!-- Sin invitación, o ya la envió: ni formulario ni explicaciones -->
				<div v-else-if="!puedeEscribir" class="text-center">
					<div
						class="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-surface-gray-2"
					>
						<Heart class="size-6 text-ink-gray-7" />
					</div>
					<h1 class="mb-2 text-2xl font-semibold text-ink-gray-9">
						<template v-if="invitacion.data?.ya_enviada">
							{{ __('You already sent us your review. Thank you!') }}
						</template>
						<template v-else>
							{{ __('You do not have this invitation right now.') }}
						</template>
					</h1>
					<router-link :to="{ name: 'Courses' }" class="mt-6 inline-block">
						<Button variant="solid" size="md">
							{{ __('Go to my courses') }}
						</Button>
					</router-link>
				</div>

				<!-- Formulario -->
				<template v-else>
					<div class="text-center">
						<h1 class="mb-2 text-2xl font-semibold text-ink-gray-9">
							{{ __('Tell us your experience') }}
						</h1>
						<p class="text-base text-ink-gray-7">
							{{
								__(
									'Tell us how the school has been for you and we apply {0}% off your subscription for {1} months.'
								).format(porcentaje, meses)
							}}
						</p>
					</div>

					<div class="mt-8 space-y-6">
						<!-- Estrellas: el mismo control que ya usa la escuela para las
						     reseñas de los cursos, aquí en grande porque es lo primero
						     que se toca. -->
						<div class="space-y-1.5">
							<FormLabel :label="__('How would you rate the school?')" />
							<Rating v-model="valoracion" size="xl" />
						</div>

						<FormControl
							type="textarea"
							:rows="8"
							v-model="texto"
							:label="__('Your review')"
							:placeholder="
								__(
									'What have you learned? What do you like the most about the classes?'
								)
							"
						/>

						<!-- Fotos: opcionales. Se suben al elegirlas para que el envío
						     de la reseña sea inmediato y no se quede colgado esperando
						     a una conexión de móvil. -->
						<div class="space-y-2">
							<FormLabel
								:label="
									__('Photos of your work ({0} max, optional)').format(
										MAXIMO_FOTOS
									)
								"
							/>
							<!-- Ancho acotado: a lo ancho de la página, tres huecos
							     cuadrados salen enormes y el formulario parece pedir
							     fotos a gritos cuando son opcionales. -->
							<div class="grid max-w-xs grid-cols-3 gap-3">
								<div
									v-for="(url, indice) in imagenes"
									:key="url"
									class="relative aspect-square overflow-hidden rounded-md border bg-surface-gray-2"
								>
									<img :src="url" class="size-full object-cover" />
									<button
										type="button"
										class="absolute end-1 top-1 grid size-6 place-items-center rounded-full bg-black/60 text-white"
										:aria-label="__('Remove photo')"
										@click="quitarFoto(indice)"
									>
										<X class="size-3.5" />
									</button>
								</div>

								<div
									v-if="subiendo"
									class="grid aspect-square place-items-center rounded-md border border-dashed border-outline-gray-2 text-xs text-ink-gray-6"
								>
									{{ `${__('Uploading')} ${progreso}%` }}
								</div>

								<button
									v-else-if="imagenes.length < MAXIMO_FOTOS"
									type="button"
									class="grid aspect-square place-items-center rounded-md border border-dashed border-outline-gray-2 text-ink-gray-5 hover:bg-surface-gray-1"
									@click="elegirFotos()"
								>
									<span class="flex flex-col items-center gap-1">
										<ImagePlus class="size-5 stroke-1" />
										<span class="text-xs">{{ __('Add photos') }}</span>
									</span>
								</button>
							</div>
							<input
								ref="entrada"
								type="file"
								accept="image/*"
								multiple
								class="hidden"
								@change="alElegir"
							/>
						</div>

						<div class="flex flex-wrap items-center gap-x-4 gap-y-2">
							<Button
								variant="solid"
								size="md"
								:disabled="!puedeEnviar"
								:loading="enviando"
								@click="enviar()"
							>
								{{ __('Send my review') }}
							</Button>
							<!-- Contador amable: dice lo que falta, no lo que sobra -->
							<p
								class="text-sm"
								:class="puedeEnviar ? 'text-green-700' : 'text-ink-gray-6'"
							>
								{{ aviso }}
							</p>
						</div>
					</div>
				</template>
			</div>
		</div>
	</div>
</template>

<script setup>
import {
	Breadcrumbs,
	Button,
	call,
	createResource,
	FileUploadHandler,
	FormControl,
	FormLabel,
	LoadingIndicator,
	Rating,
	toast,
	usePageMeta,
} from 'frappe-ui'
import { computed, ref } from 'vue'
import { Heart, ImagePlus, X } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import { validateFile } from '@/utils'

const { brand, isLoggedIn, user } = sessionStore()

const MAXIMO_FOTOS = 3

// Quién está invitada lo decide el servidor. Misma clave de caché que usa la
// barra de invitación: frappe-ui devuelve el mismo recurso, así que las dos
// pantallas comparten la respuesta y, al enviar, la barra se entera sola.
const invitacion = createResource({
	url: 'taar_lms.api.mi_invitacion_resena',
	auto: isLoggedIn,
	cache: ['invitacion-resena', user],
})

const valoracion = ref(0)
const texto = ref('')
const imagenes = ref([])
const entrada = ref(null)
const subiendo = ref(false)
const progreso = ref(0)
const enviando = ref(false)
const resultado = ref(null)

const porcentaje = computed(() => invitacion.data?.porcentaje)
const meses = computed(() => invitacion.data?.meses)

// Si el servidor no manda mínimo, no se inventa uno: se pide solo que haya
// escrito algo.
const minimo = computed(() => invitacion.data?.palabras_minimas ?? 0)

const puedeEscribir = computed(
	() => invitacion.data?.invitada && !invitacion.data?.ya_enviada
)

const palabras = computed(
	() => texto.value.trim().split(/\s+/).filter(Boolean).length
)

const puedeEnviar = computed(
	() =>
		valoracion.value > 0 &&
		palabras.value >= minimo.value &&
		palabras.value > 0 &&
		!subiendo.value
)

const aviso = computed(() => {
	const faltan = minimo.value - palabras.value
	if (faltan === 1) return __('One more word and you can send it.')
	if (faltan > 1) return __('{0} more words and you can send it.').format(faltan)
	if (!palabras.value) return __('Write us a few words.')
	if (!valoracion.value) return __('Only the stars are missing.')
	return __('Perfect, you can send it now.')
})

const elegirFotos = () => {
	if (entrada.value) entrada.value.value = ''
	entrada.value?.click()
}

const alElegir = async (evento) => {
	const elegidas = Array.from(evento.target.files || [])
	if (!elegidas.length) return

	// De tres en adelante se avisa una sola vez, en vez de callarse y descartar
	// fotos sin decir nada.
	const hueco = MAXIMO_FOTOS - imagenes.value.length
	if (elegidas.length > hueco) {
		toast.warning(__('You can attach up to {0} photos.').format(MAXIMO_FOTOS))
	}

	for (const archivo of elegidas.slice(0, hueco)) {
		if (await validateFile(archivo, true, 'image')) continue
		await subirFoto(archivo)
	}
}

const subirFoto = async (archivo) => {
	subiendo.value = true
	progreso.value = 0

	const subida = new FileUploadHandler()
	subida.on('progress', ({ uploaded, total }) => {
		progreso.value = Math.round((uploaded / total) * 100)
	})

	try {
		const guardado = await subida.upload(archivo, {
			private: false,
			folder: 'Home/Attachments',
			optimize: true,
		})
		imagenes.value.push(guardado.file_url)
	} catch (error) {
		toast.error(error?.message || __('Error Uploading File'))
	} finally {
		subiendo.value = false
	}
}

const quitarFoto = (indice) => {
	imagenes.value.splice(indice, 1)
}

const enviar = async () => {
	enviando.value = true
	try {
		const respuesta = await call('taar_lms.api.enviar_resena', {
			valoracion: valoracion.value,
			texto: texto.value.trim(),
			imagenes: imagenes.value,
		})
		if (!respuesta?.ok) {
			toast.error(respuesta?.mensaje || __('Your review could not be sent.'))
			return
		}
		resultado.value = respuesta
		// La invitación ya está gastada: se apaga aquí mismo para que la barra
		// desaparezca de toda la escuela, y se vuelve a preguntar para que el
		// dato quede guardado también para la próxima visita.
		if (invitacion.data) invitacion.data.ya_enviada = true
		invitacion.reload()
	} catch (error) {
		// Solo lo que el servidor haya escrito para ella. El texto de la
		// excepción es una ruta con un traceback detrás: eso no se le enseña.
		const mensaje = typeof error === 'string' ? error : error?.messages?.[0]
		toast.error(mensaje || __('Your review could not be sent.'))
	} finally {
		enviando.value = false
	}
}

const breadcrumbs = computed(() => [
	{
		label: __('Your experience'),
		route: { name: 'Opinion' },
	},
])

usePageMeta(() => {
	return {
		title: __('Tell us your experience'),
		icon: brand.favicon,
	}
})
</script>
