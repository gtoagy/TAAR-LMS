<!--
	La tienda de materiales: los kits de cada curso y los artículos sueltos.

	El kit abre la misma ventana que en la ficha del curso (quitar lo que ya se
	tiene, envío, pago). Lo suelto se junta en un carrito que se paga igual.
	Nada de esto decide precios: la cuenta final la hace el servidor.
-->
<template>
	<div class="h-full">
		<header
			v-if="!titulo"
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-base px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs class="h-7" :items="[{ label: __('Store'), route: { name: 'Tienda' } }]" />
			<router-link :to="{ name: 'MisPedidos' }">
				<Button size="sm">{{ __('My orders') }}</Button>
			</router-link>
		</header>

		<div v-if="catalogoKits.loading && !catalogoKits.data" class="flex justify-center py-10">
			<LoadingIndicator class="size-5 text-ink-gray-5" />
		</div>

		<div v-else class="mx-auto max-w-4xl p-5 pb-32">
			<p v-if="!catalogoKits.data?.vendible" class="mb-6 rounded-md bg-surface-gray-2 px-4 py-3 text-ink-gray-7">
				{{ __('The store opens very soon.') }}
			</p>
			<p v-else class="mb-6 text-ink-gray-7">
				{{ __('Materials for your courses, shipped to your door anywhere in Mexico.') }}
				<span v-if="catalogoKits.data?.dias_entrega">
					{{ __('Delivery: {0}.').format(catalogoKits.data.dias_entrega) }}
				</span>
			</p>

			<!-- Kits por curso -->
			<section v-if="kits.length" class="mb-10">
				<h2 class="mb-3 text-lg font-semibold text-ink-gray-9">{{ __('Course kits') }}</h2>
				<div class="grid gap-4 sm:grid-cols-2">
					<article v-for="k in kits" :key="k.curso" class="flex flex-col rounded-md border">
						<img v-if="k.foto" :src="k.foto" :alt="k.titulo" class="h-40 w-full rounded-t-md object-cover" />
						<div class="flex flex-1 flex-col gap-2 p-4">
							<h3 class="text-base font-semibold text-ink-gray-9">{{ k.titulo }}</h3>
							<p class="text-sm text-ink-gray-6">
								{{ k.articulos.length }} {{ __('materials') }} · {{ __('from {0}').format(k.desde_texto) }}
							</p>
							<Button class="mt-auto" variant="solid" @click="abrirKit(k.curso)">
								{{ __('Order kit') }}
							</Button>
						</div>
					</article>
				</div>
			</section>

			<!-- Sueltos por categoría -->
			<section v-for="grupo in categorias" :key="grupo.nombre" class="mb-8">
				<h2 class="mb-3 text-lg font-semibold text-ink-gray-9">{{ grupo.nombre }}</h2>
				<ul class="divide-y rounded-md border">
					<li v-for="a in grupo.articulos" :key="a.articulo" class="flex items-center gap-3 px-3 py-3">
						<img v-if="a.foto" :src="a.foto" :alt="a.nombre" class="size-12 shrink-0 rounded object-cover" />
						<div class="min-w-0 flex-1">
							<div class="text-base text-ink-gray-9">{{ a.nombre }}</div>
							<div v-if="a.descripcion" class="text-sm text-ink-gray-5">{{ a.descripcion }}</div>
						</div>
						<div class="whitespace-nowrap text-base">{{ pesos(a.precio) }}</div>
						<Button
							size="sm"
							:disabled="a.agotado || !catalogoKits.data?.vendible"
							@click="agregarAlCarrito(a)"
						>
							{{ a.agotado ? __('Out of stock') : __('Add') }}
						</Button>
					</li>
				</ul>
			</section>
		</div>

		<!-- El carrito, siempre a la vista mientras tenga algo. -->
		<div
			v-if="carrito.length"
			class="fixed inset-x-0 bottom-16 z-20 mx-auto max-w-4xl px-3 sm:bottom-4"
		>
			<div class="flex items-center gap-3 rounded-md border bg-surface-white p-3 shadow-lg">
				<div class="min-w-0 flex-1">
					<div class="text-base font-semibold text-ink-gray-9">
						{{ __('{0} materials').format(piezas) }} · {{ pesos(subtotal) }}
					</div>
					<button class="text-sm text-ink-gray-5 underline" @click="vaciarCarrito()">
						{{ __('Empty cart') }}
					</button>
				</div>
				<Button variant="solid" @click="verCarrito = true">{{ __('Checkout') }}</Button>
			</div>
		</div>

		<KitDialog v-model:open="verKit" :curso="kitAbierto" volver="/lms/tienda" />
		<KitDialog v-model:open="verCarrito" :desde-carrito="carrito" volver="/lms/tienda" />
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Breadcrumbs, Button, LoadingIndicator } from 'frappe-ui'
import KitDialog from '@/components/KitDialog.vue'
import { useTituloMovil } from '@/utils/navegacionMovil'
import {
	agregarAlCarrito,
	carrito,
	catalogoKits,
	pedirCatalogo,
	pesos,
	vaciarCarrito,
} from '@/utils/kits'

const { titulo } = useTituloMovil()
onMounted(() => {
	pedirCatalogo()
	catalogoKits.reload()
})

const kits = computed(() => catalogoKits.data?.kits || [])
const categorias = computed(() => {
	const grupos = {}
	for (const a of catalogoKits.data?.articulos || []) {
		const nombre = a.categoria || __('Other materials')
		;(grupos[nombre] ||= []).push(a)
	}
	return Object.entries(grupos).map(([nombre, articulos]) => ({ nombre, articulos }))
})

const piezas = computed(() => carrito.value.reduce((s, x) => s + x.cantidad, 0))
const subtotal = computed(() => carrito.value.reduce((s, x) => s + x.precio * x.cantidad, 0))

const verKit = ref(false)
const kitAbierto = ref(null)
const verCarrito = ref(false)
function abrirKit(curso) {
	kitAbierto.value = curso
	verKit.value = true
}
</script>
