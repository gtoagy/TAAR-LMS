<!--
	Los pedidos de materiales de la alumna: en qué van y su guía para rastrearlos.

	Es a donde vuelve el pago de un kit (`/lms/pedidos?pedido=<referencia>`).
	Quien vuelve de Mercado Pago llega antes que su aviso: por eso, si el pedido
	que trae en la dirección todavía no sale como pagado, se vuelve a preguntar
	unas cuantas veces antes de rendirse.
-->
<template>
	<div class="h-full">
		<header
			v-if="!titulo"
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-base px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs class="h-7" :items="[{ label: __('My orders'), route: { name: 'MisPedidos' } }]" />
		</header>

		<div class="mx-auto max-w-2xl p-5">
			<div
				v-if="recienPagado"
				class="mb-5 rounded-md bg-surface-green-2 px-4 py-3 text-base text-ink-green-3"
			>
				{{ __('Thank you! Your order is paid. We will email you when it ships.') }}
			</div>
			<div
				v-else-if="esperandoPago"
				class="mb-5 rounded-md bg-surface-gray-2 px-4 py-3 text-base text-ink-gray-7"
			>
				{{ __('We are confirming your payment. This can take a minute.') }}
			</div>

			<div v-if="pedidos.loading && !pedidos.data" class="flex justify-center py-10">
				<LoadingIndicator class="size-5 text-ink-gray-5" />
			</div>

			<div v-else-if="!lista.length" class="py-10 text-center text-ink-gray-6">
				<p class="mb-4">{{ __('You have no material orders yet.') }}</p>
				<router-link v-if="tiendaAbierta" :to="{ name: 'Tienda' }">
					<Button variant="solid">{{ __('Go to the store') }}</Button>
				</router-link>
			</div>

			<div v-else class="flex flex-col gap-4">
				<article
					v-for="p in lista"
					:key="p.referencia"
					class="rounded-md border p-4"
					:class="{ 'border-ink-gray-7': p.referencia === pedidoDeLaUrl }"
				>
					<div class="flex items-start justify-between gap-3">
						<div>
							<h2 class="text-base font-semibold text-ink-gray-9">{{ p.titulo }}</h2>
							<div class="text-sm text-ink-gray-5">{{ fecha(p.pagado_en || p.creado) }}</div>
						</div>
						<Badge :theme="tema(p.estado)" size="md">{{ etiqueta(p.estado) }}</Badge>
					</div>

					<ul class="mt-3 text-base text-ink-gray-7">
						<li v-for="a in p.articulos" :key="a.nombre">
							{{ a.cantidad }} × {{ a.nombre }}
						</li>
					</ul>

					<div class="mt-3 text-sm text-ink-gray-6">{{ __('Ships to') }}: {{ p.direccion }}</div>
					<div class="mt-1 flex justify-between text-base">
						<span class="text-ink-gray-7">{{ __('Total') }} ({{ __('shipping') }} {{ p.envio_texto }})</span>
						<span class="font-semibold text-ink-gray-9">{{ p.total_texto }}</span>
					</div>

					<div v-if="p.guia" class="mt-3 flex flex-wrap items-center gap-2">
						<span class="text-sm text-ink-gray-7">
							{{ p.paqueteria }} · {{ __('Tracking') }} <b>{{ p.guia }}</b>
						</span>
						<a v-if="p.rastreo_url" :href="p.rastreo_url" target="_blank" rel="noopener">
							<Button size="sm">{{ __('Track my package') }}</Button>
						</a>
					</div>
				</article>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Badge, Breadcrumbs, Button, LoadingIndicator, createResource } from 'frappe-ui'
import { useTituloMovil } from '@/utils/navegacionMovil'
import { pedirCatalogo, tiendaAbierta, vaciarCarrito } from '@/utils/kits'

const { titulo } = useTituloMovil()
const route = useRoute()
const pedidoDeLaUrl = computed(() => route.query.pedido || null)

// Al volver de Stripe trae el id de su sesión: el servidor confirma el pago con
// él si el aviso de Stripe todavía no llega.
const pedidos = createResource({
	url: 'taar_lms.kits.mis_pedidos',
	makeParams: () => (route.query.session_id ? { session_id: route.query.session_id } : {}),
})
const lista = computed(() => pedidos.data || [])

const encontrado = computed(() => lista.value.find((p) => p.referencia === pedidoDeLaUrl.value))
const recienPagado = computed(() => !!encontrado.value && encontrado.value.estado === 'Pagado')
const esperandoPago = computed(() => !!pedidoDeLaUrl.value && !encontrado.value && intentos.value < 6)

const intentos = ref(0)
function cargar() {
	pedidos.fetch().then(() => {
		if (pedidoDeLaUrl.value && !encontrado.value && intentos.value < 6) {
			intentos.value += 1
			setTimeout(cargar, 3000)
		}
		// Pagado desde el carrito: el carrito ya se convirtió en pedido.
		if (encontrado.value) vaciarCarrito()
	})
}

onMounted(() => {
	pedirCatalogo()
	cargar()
})

const ETIQUETAS = {
	Pagado: __('Paid'),
	'Guía generada': __('Preparing'),
	'Con el proveedor': __('Preparing'),
	'En camino': __('On its way'),
	Entregado: __('Delivered'),
	Problema: __('We will contact you'),
	Reembolsado: __('Refunded'),
}
function etiqueta(estado) {
	return ETIQUETAS[estado] || estado
}
function tema(estado) {
	if (estado === 'Entregado') return 'green'
	if (estado === 'En camino') return 'blue'
	if (estado === 'Problema' || estado === 'Reembolsado') return 'orange'
	return 'gray'
}
function fecha(texto) {
	if (!texto) return ''
	const d = new Date(texto.replace(' ', 'T'))
	return isNaN(d) ? '' : d.toLocaleDateString('es-MX', { day: 'numeric', month: 'long', year: 'numeric' })
}
</script>
