<template>
	<div class="h-full">
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-base px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs class="h-7" :items="breadcrumbs" />
		</header>

		<!-- Hasta que el servidor no dice quién está mirando, no se enseña nada.
		     Pintar el buscador antes de tiempo sería abrir la libreta de la
		     escuela —correos, pagos, cursos— a quien todavía no sabemos si puede
		     verla. -->
		<div
			v-if="isLoggedIn && !user.data"
			class="flex flex-1 items-center justify-center p-5"
		>
			<LoadingIndicator class="size-5 text-ink-gray-5" />
		</div>

		<div v-else-if="!puedeAtender" class="p-5">
			<div class="mx-auto mt-16 max-w-sm text-center">
				<h1 class="mb-2 text-xl font-semibold text-ink-gray-9">
					{{ __('This page is for the school team.') }}
				</h1>
				<router-link :to="{ name: 'Courses' }" class="mt-6 inline-block">
					<Button variant="solid" size="md">
						{{ __('Go to my courses') }}
					</Button>
				</router-link>
			</div>
		</div>

		<div v-else class="p-5">
			<div class="mx-auto max-w-3xl">
				<h1 class="text-2xl font-semibold text-ink-gray-9">
					{{ __('Student support') }}
				</h1>
				<p class="mt-1 text-base text-ink-gray-7">
					{{
						__(
							'Look up a student to resend her access or move her account to another email.'
						)
					}}
				</p>

				<FormControl
					v-model="texto"
					type="text"
					class="mt-6"
					:placeholder="__('Name or email')"
					autocapitalize="off"
					autocomplete="off"
					spellcheck="false"
				/>

				<!-- Buscando. El indicador va aquí y no encima de los resultados
				     para que la lista no salte con cada tecla. -->
				<div v-if="buscando" class="mt-8 flex items-center justify-center">
					<LoadingIndicator class="size-5 text-ink-gray-5" />
				</div>

				<ErrorMessage v-else-if="errorBusqueda" class="mt-6" :message="errorBusqueda" />

				<p v-else-if="!suficiente" class="mt-6 text-sm text-ink-gray-5">
					{{ __('Write at least {0} letters to search.').format(MINIMO_LETRAS) }}
				</p>

				<p v-else-if="!resultados.length" class="mt-6 text-base text-ink-gray-7">
					{{ __('Nobody matches that. Try her name, or part of her email.') }}
				</p>

				<div v-else class="mt-6 space-y-3">
					<div
						v-for="alumna in resultados"
						:key="alumna.correo"
						class="rounded-lg border border-outline-gray-2 bg-surface-base p-4"
					>
						<div class="flex flex-wrap items-start justify-between gap-2">
							<div class="min-w-0">
								<div class="font-medium text-ink-gray-9">
									{{ alumna.nombre || alumna.correo }}
								</div>
								<!-- break-all: hay correos largos y la tarjeta tiene que
								     caber en un móvil sin desbordarse a lo ancho. -->
								<div class="break-all text-sm text-ink-gray-6">
									{{ alumna.correo }}
								</div>
							</div>
							<!-- Lo primero que hay que saber estos días: si nunca entró,
							     lo que le falta es su enlace, no su contraseña. -->
							<Badge
								size="md"
								variant="subtle"
								:theme="alumna.ha_entrado ? 'green' : 'amber'"
							>
								{{
									alumna.ha_entrado
										? __('Already signed in')
										: __('Never signed in')
								}}
							</Badge>
						</div>

						<p class="mt-3 text-sm text-ink-gray-7">
							{{ textoMembresia(alumna.membresia) }}
						</p>

						<div v-if="alumna.cursos.length" class="mt-3 flex flex-wrap gap-1.5">
							<span
								v-for="curso in alumna.cursos"
								:key="curso.nombre"
								class="rounded-full px-2 py-0.5 text-xs"
								:class="
									curso.comprado
										? 'bg-surface-amber-2 text-ink-amber-8'
										: 'bg-surface-gray-2 text-ink-gray-7'
								"
							>
								{{ curso.nombre }}
								<!-- Los comprados sueltos son suyos para siempre; los demás
								     se van con ella el día que cancele. Quien atiende
								     necesita saber cuál es cuál antes de responder. -->
								<template v-if="curso.comprado">
									· {{ __('bought separately') }}
								</template>
							</span>
						</div>
						<p v-else class="mt-3 text-sm text-ink-gray-5">
							{{ __('No courses yet.') }}
						</p>

						<div class="mt-4 flex flex-wrap gap-2">
							<Button size="sm" @click="abrirReenvio(alumna)">
								<template #prefix>
									<Send class="size-3.5" />
								</template>
								{{ __('Resend her access') }}
							</Button>
							<Button size="sm" @click="abrirMudanza(alumna)">
								<template #prefix>
									<AtSign class="size-3.5" />
								</template>
								{{ __('Change her email') }}
							</Button>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Reenviar el acceso -->
		<Dialog
			v-model:open="dialogoReenvio"
			:title="__('Resend her access')"
			:actions="[
				{
					label: __('Yes, send it'),
					variant: 'solid',
					loading: enviando,
					onClick: () => reenviar(),
				},
			]"
		>
			<template #body-content>
				<p class="text-base text-ink-gray-7">
					{{
						__(
							'We will email {0} with her link to create her password. Her previous link stops working.'
						).format(elegida?.correo)
					}}
				</p>
				<ErrorMessage class="mt-2" :message="errorReenvio" />
			</template>
		</Dialog>

		<!-- Cambiar el correo -->
		<Dialog
			v-model:open="dialogoMudanza"
			:title="__('Change her email')"
			:actions="[
				{
					label: __('Move her account'),
					variant: 'solid',
					loading: mudando,
					onClick: () => mudar(),
				},
			]"
		>
			<template #body-content>
				<div class="space-y-4">
					<p class="text-base text-ink-gray-7">
						{{ __('Her account today: {0}').format(elegida?.correo) }}
					</p>

					<FormControl
						v-model="correoNuevo"
						type="email"
						:label="__('New email')"
						placeholder="nombre@correo.com"
						autocapitalize="off"
						autocomplete="off"
						spellcheck="false"
						@keyup.enter="mudar()"
					/>

					<!-- Lo que se lleva consigo. Se dice antes de confirmar, no
					     después: quien atiende tiene que saber que esto no es
					     "editar un campo", es mover la cuenta entera. -->
					<div
						class="rounded-md bg-surface-gray-1 p-3 text-sm leading-relaxed text-ink-gray-7"
					>
						<p>
							{{
								__(
									'The whole account moves: her membership, her courses and her progress.'
								)
							}}
						</p>
						<p v-if="elegida?.stripe_customer_id" class="mt-1.5">
							{{
								__(
									'It also gets fixed in Stripe, so her next receipt goes to the right inbox.'
								)
							}}
						</p>
						<p class="mt-1.5">
							{{
								__(
									'She does not get any email from this. Send her access afterwards if she needs it.'
								)
							}}
						</p>
					</div>

					<ErrorMessage :message="errorMudanza" />
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import {
	Badge,
	Breadcrumbs,
	Button,
	call,
	createResource,
	debounce,
	Dialog,
	ErrorMessage,
	FormControl,
	LoadingIndicator,
	toast,
	usePageMeta,
} from 'frappe-ui'
import { computed, inject, ref, watch } from 'vue'
import { AtSign, Send } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'

const { brand, isLoggedIn } = sessionStore()
const user = inject('$user')

// El mismo mínimo que aplica el servidor. Por debajo no se pregunta: encajarían
// casi todas las alumnas y la respuesta no ayuda a nadie.
const MINIMO_LETRAS = 3

const texto = ref('')
const elegida = ref(null)
const dialogoReenvio = ref(false)
const dialogoMudanza = ref(false)
const correoNuevo = ref('')
const enviando = ref(false)
const mudando = ref(false)
const errorReenvio = ref('')
const errorMudanza = ref('')

// Las dos maneras de administrar la escuela, las mismas que comprueba el
// servidor. La dueña entra por Moderator; quien lleva el sistema, por la otra.
const puedeAtender = computed(
	() => Boolean(user.data?.is_moderator) || Boolean(user.data?.is_system_manager)
)

const busqueda = createResource({
	url: 'taar_lms.api.buscar_alumnas',
	makeParams: () => ({ texto: texto.value.trim() }),
})

const suficiente = computed(() => texto.value.trim().length >= MINIMO_LETRAS)

// Si borra letras hasta quedarse corta, los resultados de antes desaparecen solos
// en vez de quedarse en pantalla contradiciendo lo que hay escrito arriba.
const resultados = computed(() =>
	suficiente.value ? busqueda.data || [] : []
)

const buscando = computed(() => suficiente.value && busqueda.loading)

const errorBusqueda = computed(() =>
	suficiente.value ? mensajeDelServidor(busqueda.error) : ''
)

// Medio segundo: se escribe un nombre entero sin que salga una consulta por
// letra, y sigue sintiéndose inmediato. La consulta se retrasa, pero el aviso de
// "escribe al menos tres letras" no: eso se ve al momento.
const buscarConCalma = debounce(() => {
	if (suficiente.value) busqueda.reload()
}, 500)

watch(texto, buscarConCalma)

/* Solo lo que el servidor haya escrito para quien lee. El texto de la excepción
   trae la ruta y el traceback detrás, y eso no se enseña en pantalla. */
const mensajeDelServidor = (error) => {
	if (!error) return ''
	return typeof error === 'string' ? error : error?.messages?.[0] || ''
}

const textoMembresia = (membresia) => {
	if (!membresia) return __('No membership.')
	// El vitalicio pagó una vez y para siempre: hablarle de estado o de fecha de
	// renovación es contarle algo que no existe.
	if (membresia.vitalicio) return __('Lifetime access.')

	// Estado y plan llegan ya en español desde el servidor ("Activa", "En mora",
	// "Anual"): son los mismos nombres que se ven en la ficha, y traducirlos aquí
	// haría que la pantalla y la ficha se llamaran distinto.
	const partes = [membresia.estado, membresia.plan].filter(Boolean)
	let resumen = __('Membership: {0}').format(partes.join(' · '))
	if (membresia.hasta) {
		resumen += ' · ' + __('until {0}').format(membresia.hasta)
	}
	return resumen
}

const abrirReenvio = (alumna) => {
	elegida.value = alumna
	errorReenvio.value = ''
	dialogoReenvio.value = true
}

const reenviar = async () => {
	enviando.value = true
	errorReenvio.value = ''
	try {
		await call('taar_lms.api.reenviar_acceso', { correo: elegida.value.correo })
		toast.success(__('Access sent to {0}').format(elegida.value.correo))
		dialogoReenvio.value = false
	} catch (error) {
		errorReenvio.value =
			mensajeDelServidor(error) || __('We could not send that email.')
	} finally {
		enviando.value = false
	}
}

const abrirMudanza = (alumna) => {
	elegida.value = alumna
	correoNuevo.value = ''
	errorMudanza.value = ''
	dialogoMudanza.value = true
}

const mudar = async () => {
	if (mudando.value) return
	mudando.value = true
	errorMudanza.value = ''
	const nuevo = correoNuevo.value.trim()
	try {
		const respuesta = await call('taar_lms.api.cambiar_correo', {
			actual: elegida.value.correo,
			nuevo,
		})
		// Que Stripe no se dejara corregir no deshace la mudanza, pero hay que
		// decirlo en voz alta: si no, el próximo recibo se va al buzón viejo y
		// nadie se entera hasta que la alumna escribe otra vez.
		if (respuesta?.stripe === false && elegida.value.stripe_customer_id) {
			toast.warning(
				__('Account moved, but Stripe kept the old address. Fix it there by hand.')
			)
		} else {
			toast.success(__('Account moved to {0}').format(nuevo))
		}
		dialogoMudanza.value = false

		// El correo viejo ya no existe, así que la tarjeta que sigue en pantalla
		// enseña una cuenta que acaba de dejar de estar ahí: se vuelve a buscar.
		const consulta = texto.value.trim().toLowerCase()
		if (
			nuevo.toLowerCase().includes(consulta) ||
			(elegida.value.nombre || '').toLowerCase().includes(consulta)
		) {
			busqueda.reload()
		} else {
			// Lo que escribió solo encajaba con el correo de antes: repetir esa
			// búsqueda dejaría la lista vacía justo después de decirle que salió
			// bien. Se pasa al nuevo, que sí la trae; el watch busca solo.
			texto.value = nuevo
		}
	} catch (error) {
		errorMudanza.value =
			mensajeDelServidor(error) || __('We could not change that email.')
	} finally {
		mudando.value = false
	}
}

const breadcrumbs = computed(() => [
	{
		label: __('Student support'),
		route: { name: 'Soporte' },
	},
])

usePageMeta(() => {
	return {
		title: __('Student support'),
		icon: brand.favicon,
	}
})
</script>
