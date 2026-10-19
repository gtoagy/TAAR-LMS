<template>
	<div class="h-full">
		<!-- En el móvil sobra: la barra superior ya dice dónde está. -->
		<header
			v-if="!titulo"
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-base px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs class="h-7" :items="breadcrumbs" />
		</header>

		<!-- Hasta saber quién mira no se enseña nada: aquí hay nombres, celulares
		     y lo que pagó cada una. -->
		<div
			v-if="isLoggedIn && !user.data"
			class="flex flex-1 items-center justify-center p-5"
		>
			<LoadingIndicator class="size-5 text-ink-gray-5" />
		</div>

		<div v-else-if="!puedeAtender" class="p-5">
			<div class="mx-auto mt-16 max-w-sm text-center">
				<component
					:is="etiquetaTitulo"
					class="mb-2 text-heading font-semibold text-ink-gray-9"
				>
					{{ __('This page is for the school team.') }}
				</component>
				<router-link :to="{ name: 'Courses' }" class="mt-6 inline-block">
					<Button variant="solid" size="md">
						{{ __('Go to my courses') }}
					</Button>
				</router-link>
			</div>
		</div>

		<div v-else class="p-4 sm:p-5">
			<div class="mx-auto max-w-3xl">
				<div class="flex items-start justify-between gap-3">
					<div class="min-w-0">
						<h1
							v-if="!titulo"
							class="text-title font-semibold text-ink-gray-9"
						>
							{{ __('Follow-up') }}
						</h1>
						<p class="mt-1 text-body text-ink-gray-7">
							{{
								__(
									'Who just bought and who needs a message, with WhatsApp one tap away.'
								)
							}}
						</p>
					</div>
					<Button
						size="sm"
						:loading="datos.loading"
						:aria-label="__('Refresh')"
						@click="datos.reload()"
					>
						<template #icon>
							<RefreshCw class="size-4" />
						</template>
					</Button>
				</div>

				<!-- Las tres listas. Botones y no pestañas de frappe-ui: en un
				     teléfono tienen que caber los tres con su número sin scroll. -->
				<div
					class="mt-5 grid grid-cols-3 gap-1 rounded-lg bg-surface-gray-2 p-1"
					role="tablist"
				>
					<button
						v-for="p in pestanas"
						:key="p.clave"
						role="tab"
						:aria-selected="pestana === p.clave"
						class="rounded-md px-2 py-2 text-base font-medium transition"
						:class="
							pestana === p.clave
								? 'bg-surface-elevation-1 text-ink-gray-9 shadow-sm'
								: 'text-ink-gray-6'
						"
						@click="pestana = p.clave"
					>
						{{ p.etiqueta }}
						<span
							v-if="p.cuantas !== null"
							class="ml-0.5 tabular-nums"
							:class="p.alerta ? 'text-ink-red-4' : 'text-ink-gray-5'"
						>
							{{ p.cuantas }}
						</span>
					</button>
				</div>

				<div v-if="datos.loading && !datos.data" class="mt-10 flex justify-center">
					<LoadingIndicator class="size-5 text-ink-gray-5" />
				</div>

				<ErrorMessage
					v-else-if="datos.error"
					class="mt-6"
					:message="mensajeDelServidor(datos.error) || __('We could not load the list.')"
				/>

				<p v-else-if="!lista.length" class="mt-8 text-center text-body text-ink-gray-6">
					{{ textoVacio }}
				</p>

				<div v-else class="mt-4 space-y-3">
					<div
						v-for="alumna in lista"
						:id="`alumna-${alumna.alumna}`"
						:key="`${pestana}-${alumna.alumna}`"
						class="rounded-lg border bg-surface-base p-4 transition"
						:class="
							alumna.alumna === destacada
								? 'border-outline-amber-1 bg-surface-amber-1'
								: 'border-outline-gray-2'
						"
					>
						<div class="flex items-start justify-between gap-2">
							<div class="min-w-0">
								<div class="text-body font-medium text-ink-gray-9">
									{{ alumna.nombre }}
								</div>
								<div class="text-support text-ink-gray-6">
									{{ alumna.producto }}
								</div>
							</div>
							<Badge
								v-if="alumna.etapa"
								size="md"
								variant="subtle"
								:theme="colorDeEtapa(alumna.etapa)"
								class="shrink-0"
							>
								{{ alumna.etapa }}
							</Badge>
						</div>

						<!-- Lo que conviene hacer, que es por lo que se abre esta
						     página. En rojo lo que no puede esperar. -->
						<p
							v-if="alumna.que_hacer"
							class="mt-3 text-base"
							:class="
								alumna.urgente
									? 'font-semibold text-ink-red-4'
									: alumna.pendiente
									? 'font-medium text-ink-gray-9'
									: 'text-ink-gray-6'
							"
						>
							{{ alumna.que_hacer }}
						</p>

						<p class="mt-2 text-support text-ink-gray-6">
							{{ detalle(alumna) }}
						</p>

						<div class="mt-4 flex flex-wrap items-center gap-2">
							<!-- Un enlace y no un botón: en el teléfono es lo que deja
							     al sistema abrir la app de WhatsApp (Business, si es
							     la que está) en vez de una pestaña nueva. -->
							<a
								v-if="alumna.whatsapp"
								:href="alumna.whatsapp"
								target="_blank"
								rel="noopener"
								class="inline-flex h-9 flex-1 items-center justify-center gap-1.5 rounded-md bg-[#25d366] px-4 text-base font-medium text-white sm:flex-none"
							>
								<WhatsAppIcon class="size-4" />
								{{ __('WhatsApp') }}
							</a>
							<span
								v-else
								class="inline-flex h-9 items-center text-support text-ink-gray-5"
							>
								{{ __('No phone number yet') }}
							</span>

							<Button
								v-if="alumna.pendiente"
								size="md"
								:loading="marcando === alumna.alumna"
								@click="marcarContactada(alumna)"
							>
								<template #prefix>
									<Check class="size-4" />
								</template>
								{{ __('I wrote to her') }}
							</Button>
							<span
								v-else-if="alumna.contactada_en"
								class="text-support text-ink-gray-5"
							>
								{{ __('You wrote to her on {0}').format(fecha(alumna.contactada_en)) }}
							</span>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import {
	Badge,
	Breadcrumbs,
	Button,
	call,
	createResource,
	ErrorMessage,
	LoadingIndicator,
	toast,
	usePageMeta,
} from 'frappe-ui'
import { computed, inject, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Check, RefreshCw } from 'lucide-vue-next'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { sessionStore } from '@/stores/session'
import { useTituloMovil } from '@/utils/navegacionMovil'

const { brand, isLoggedIn } = sessionStore()
const { titulo, etiquetaTitulo } = useTituloMovil()
const user = inject('$user')
const route = useRoute()

// Los mismos días que espera el servidor entre un mensaje y el siguiente
// (seguimiento.DIAS_DE_DESCANSO). Aquí solo decide si una venta sigue pidiendo
// que le escriban.
const DIAS_DE_DESCANSO = 7

const puedeAtender = computed(
	() => Boolean(user.data?.is_moderator) || Boolean(user.data?.is_system_manager)
)

// Si se llega desde el aviso de una venta (?alumna=correo), se abre en
// «Ventas» con ella marcada.
const destacada = ref((route.query.alumna || '').toString().toLowerCase())
const pestana = ref(destacada.value ? 'ventas' : 'pendientes')
const marcando = ref(null)

const datos = createResource({
	url: 'taar_lms.seguimiento.para_la_app',
	auto: false,
})

watch(
	puedeAtender,
	(puede) => {
		if (puede && !datos.data && !datos.loading) datos.reload()
	},
	{ immediate: true }
)

const compradoras = computed(() =>
	(datos.data?.compradoras || []).map((c) => ({ ...c, producto: c.curso_titulo }))
)

const ventas = computed(() =>
	(datos.data?.ventas || []).map((v) => ({
		...v,
		etapa: v.bienvenida === 'Completa' ? null : __('Welcome unfinished'),
		urgente: false,
		pendiente: v.bienvenida !== 'Completa' && !contactadaHacePoco(v.contactada_en),
		que_hacer: '',
	}))
)

// «Por escribir» junta lo que el informe ya marca como pendiente (compradoras
// de curso) con las membresías que no terminaron la bienvenida, que el informe
// no mira porque no tienen un curso cuyo avance medir.
const pendientes = computed(() => {
	const deCursos = compradoras.value.filter((c) => c.pendiente)
	const yaEstan = new Set(deCursos.map((c) => c.alumna))
	const deMembresia = ventas.value
		.filter((v) => v.membresia && v.pendiente && !yaEstan.has(v.alumna))
		.map((v) => ({
			...v,
			que_hacer: __('Bought the membership and did not finish the welcome'),
		}))
	return [...deCursos, ...deMembresia]
})

const lista = computed(() => {
	if (pestana.value === 'ventas') return ventas.value
	if (pestana.value === 'todas') return compradoras.value
	return pendientes.value
})

const pestanas = computed(() => [
	{
		clave: 'pendientes',
		etiqueta: __('To write'),
		cuantas: datos.data ? pendientes.value.length : null,
		alerta: pendientes.value.some((p) => p.urgente),
	},
	{
		clave: 'ventas',
		etiqueta: __('Sales'),
		cuantas: datos.data ? ventas.value.length : null,
	},
	{
		clave: 'todas',
		etiqueta: __('Course buyers'),
		cuantas: datos.data ? compradoras.value.length : null,
	},
])

const textoVacio = computed(() => {
	if (pestana.value === 'pendientes') return __('Nobody is waiting for a message. All good.')
	if (pestana.value === 'ventas') return __('No sales in the last 30 days.')
	return __('No course buyers in the last 60 days.')
})

// Al llegar desde el aviso de una venta, se baja hasta ella.
watch(
	() => datos.data,
	async (d) => {
		if (!d || !destacada.value) return
		await nextTick()
		const tarjeta = document.getElementById(`alumna-${destacada.value}`)
		tarjeta?.scrollIntoView({ behavior: 'smooth', block: 'center' })
	}
)

const marcarContactada = async (alumna) => {
	marcando.value = alumna.alumna
	try {
		await call('taar_lms.seguimiento.marcar_contactada', { alumna: alumna.alumna })
		toast.success(__('Noted. She leaves the list for a week.'))
		await datos.reload()
	} catch (error) {
		toast.error(mensajeDelServidor(error) || __('We could not save that.'))
	} finally {
		marcando.value = null
	}
}

/* Las fechas llegan como "2026-10-12 14:33:00": Safari no entiende el espacio. */
const aFecha = (texto) => (texto ? new Date(String(texto).replace(' ', 'T')) : null)

const fecha = (texto) => {
	const d = aFecha(texto)
	return d ? d.toLocaleDateString('es-MX', { day: 'numeric', month: 'short' }) : ''
}

const contactadaHacePoco = (texto) => {
	const d = aFecha(texto)
	return Boolean(d) && Date.now() - d.getTime() < DIAS_DE_DESCANSO * 24 * 3600 * 1000
}

const detalle = (alumna) => {
	const partes = [__('Bought on {0}').format(fecha(alumna.compro))]
	if (alumna.total) {
		partes.push(__('{0} of {1} lessons').format(alumna.vistas, alumna.total))
	} else if (alumna.bienvenida && alumna.bienvenida !== 'Completa') {
		partes.push(alumna.bienvenida)
	} else if (alumna.empezo) {
		partes.push(__('Already started'))
	}
	if (alumna.miembro) partes.push(__('Has the membership'))
	return partes.join(' · ')
}

// Casi los del informe del escritorio. El Badge de frappe-ui solo trae gris,
// azul, verde, naranja y rojo, así que amarillo y morado se quedan en los vecinos.
const COLORES = {
	'Bienvenida a medias': 'red',
	'Sin empezar': 'orange',
	Empezando: 'blue',
	Avanzando: 'blue',
	'Pasó la mitad': 'green',
	Terminó: 'green',
}
const colorDeEtapa = (etapa) => COLORES[etapa] || 'red'

const mensajeDelServidor = (error) => {
	if (!error) return ''
	return typeof error === 'string' ? error : error?.messages?.[0] || ''
}

const breadcrumbs = computed(() => [
	{
		label: __('Follow-up'),
		route: { name: 'Seguimiento' },
	},
])

usePageMeta(() => {
	return {
		title: __('Follow-up'),
		icon: brand.favicon,
	}
})
</script>
