<!--
	Armar y pagar un pedido de materiales.

	Sirve a los dos caminos: el kit de un curso (`curso`), donde la alumna quita
	lo que ya tiene, y el carrito de la tienda (`desdeCarrito`), donde ya viene
	elegido. Después pide el código postal, enseña las opciones de envío, toma la
	dirección y abre el pago.

	Ninguna cifra se calcula aquí: el total que se enseña es el que devuelve
	`taar_lms.kits.cotizar`, y el pedido lo crea `taar_lms.kits.preparar` con sus
	propios precios. El pago es el modal de la escuela (`pagarPedido`).
-->
<template>
	<Dialog v-model:open="abierto" :title="titulo" size="xl">
		<template #default>
			<div class="taar-kit flex flex-col gap-5 text-ink-gray-8">
				<div v-if="cargando" class="flex justify-center py-8">
					<LoadingIndicator class="size-5 text-ink-gray-5" />
				</div>

				<template v-else-if="lista.length">
					<img
						v-if="kit?.foto"
						:src="kit.foto"
						:alt="kit.titulo"
						class="w-full max-h-56 object-cover rounded-md"
					/>
					<p v-if="kit?.descripcion" class="text-p-base text-ink-gray-7">
						{{ kit.descripcion }}
					</p>

					<!-- 1. Qué lleva -->
					<section>
						<h3 class="text-base font-semibold text-ink-gray-9 mb-2">
							{{
								modoKit && puedePedir
									? __('Uncheck what you already have')
									: __('What it includes')
							}}
						</h3>
						<ul class="divide-y rounded-md border">
							<li
								v-for="item in lista"
								:key="item.articulo"
								class="flex items-center gap-3 px-3 py-2.5"
								:class="{ 'opacity-50': item.agotado }"
							>
								<input
									v-if="modoKit && puedePedir"
									type="checkbox"
									class="taar-kit-check"
									:checked="marcados[item.articulo]"
									:disabled="item.obligatorio || item.agotado"
									@change="alternar(item.articulo)"
								/>
								<div class="min-w-0 flex-1">
									<div class="text-base text-ink-gray-9">
										<span v-if="item.cantidad > 1">{{ item.cantidad }} × </span>
										{{ item.nombre }}
									</div>
									<div class="text-sm text-ink-gray-5">
										<span v-if="item.agotado">{{ __('Out of stock') }}</span>
										<span v-else-if="item.obligatorio">{{ __('Always included') }}</span>
										<span v-else-if="item.nota">{{ item.nota }}</span>
									</div>
								</div>
								<div class="text-base text-ink-gray-8 whitespace-nowrap">
									{{ pesos(item.precio * item.cantidad) }}
								</div>
							</li>
						</ul>
						<div class="mt-2 flex justify-between text-base">
							<span class="text-ink-gray-7">{{ __('Materials') }}</span>
							<span class="font-semibold text-ink-gray-9">{{ pesos(subtotalVista) }}</span>
						</div>
					</section>

					<p
						v-if="!puedePedir"
						class="rounded-md bg-surface-gray-2 px-3 py-2 text-sm text-ink-gray-7"
					>
						{{ motivoSinCompra }}
					</p>

					<template v-else>
						<!-- 2. A dónde -->
						<section class="flex flex-col gap-3">
							<h3 class="text-base font-semibold text-ink-gray-9">
								{{ __('Shipping (Mexico only)') }}
							</h3>
							<label class="taar-kit-campo">
								<span>{{ __('Postal code') }}</span>
								<input
									v-model="direccion.cp"
									inputmode="numeric"
									maxlength="5"
									autocomplete="postal-code"
									placeholder="97000"
									@input="alCambiarCp"
								/>
							</label>

							<div v-if="cotizacion.loading" class="text-sm text-ink-gray-5">
								{{ __('Calculating shipping…') }}
							</div>
							<div v-else-if="opcionesEnvio.length" class="flex flex-col gap-2">
								<label
									v-for="op in opcionesEnvio"
									:key="op.id"
									class="flex items-center gap-3 rounded-md border px-3 py-2.5 cursor-pointer"
									:class="{ 'border-ink-gray-7': envio === op.id }"
								>
									<input v-model="envio" type="radio" :value="op.id" />
									<div class="flex-1">
										<div class="text-base text-ink-gray-9">
											{{ op.paqueteria }} · {{ op.servicio }}
										</div>
										<div class="text-sm text-ink-gray-5">{{ op.dias }}</div>
									</div>
									<div class="text-base font-semibold">{{ op.precio_texto }}</div>
								</label>
							</div>

							<template v-if="opcionesEnvio.length">
								<label class="taar-kit-campo">
									<span>{{ __('Who receives it') }}</span>
									<input v-model="direccion.receptor" autocomplete="name" />
								</label>
								<label class="taar-kit-campo">
									<span>{{ __('Phone (10 digits)') }}</span>
									<input
										v-model="direccion.telefono"
										inputmode="tel"
										autocomplete="tel-national"
									/>
								</label>
								<label class="taar-kit-campo">
									<span>{{ __('Street and number') }}</span>
									<input v-model="direccion.calle" autocomplete="address-line1" />
								</label>
								<label class="taar-kit-campo">
									<span>{{ __('Neighborhood (colonia)') }}</span>
									<input v-model="direccion.colonia" autocomplete="address-line2" />
								</label>
								<div class="grid gap-3 sm:grid-cols-2">
									<label class="taar-kit-campo">
										<span>{{ __('City or municipality') }}</span>
										<input v-model="direccion.ciudad" autocomplete="address-level2" />
									</label>
									<label class="taar-kit-campo">
										<span>{{ __('State') }}</span>
										<select v-model="direccion.estado_mx" autocomplete="address-level1">
											<option value="" disabled>{{ __('Choose…') }}</option>
											<option v-for="e in estados" :key="e" :value="e">{{ e }}</option>
										</select>
									</label>
								</div>
								<label class="taar-kit-campo">
									<span>{{ __('References (optional)') }}</span>
									<input
										v-model="direccion.referencias"
										:placeholder="__('Green gate, between 12 and 14…')"
									/>
								</label>
							</template>
						</section>

						<!-- 3. Total y pago -->
						<section v-if="opcionElegida" class="rounded-md bg-surface-gray-2 px-4 py-3">
							<div class="flex justify-between text-base">
								<span>{{ __('Materials') }}</span>
								<span>{{ cotizacion.data?.subtotal_texto }}</span>
							</div>
							<div class="flex justify-between text-base">
								<span>{{ __('Shipping') }}</span>
								<span>{{ opcionElegida.precio_texto }}</span>
							</div>
							<div class="mt-1 flex justify-between text-lg font-semibold text-ink-gray-9">
								<span>{{ __('Total') }}</span>
								<span>{{ opcionElegida.total_texto }}</span>
							</div>
						</section>

						<p v-if="error" class="text-sm text-ink-red-4">{{ error }}</p>

						<Button
							variant="solid"
							size="lg"
							class="w-full"
							:disabled="!opcionElegida"
							:loading="preparando"
							@click="continuar"
						>
							{{ __('Continue to payment') }}
						</Button>
						<p class="text-center text-sm text-ink-gray-5">
							{{ __('Card, PayPal or Mercado Pago. We email you the tracking number when it ships.') }}
						</p>
					</template>
				</template>

				<p v-else class="py-6 text-center text-ink-gray-5">
					{{ __('There is nothing to order yet.') }}
				</p>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, inject, reactive, ref, watch } from 'vue'
import { Button, Dialog, LoadingIndicator, call, createResource } from 'frappe-ui'
import { useTelemetry } from 'frappe-ui/frappe'
import { pagarPedido, pesos } from '@/utils/kits'

const props = defineProps({
	curso: { type: String, default: null },
	// Para la tienda: [{articulo, nombre, precio, cantidad}] ya elegidos.
	desdeCarrito: { type: Array, default: null },
	volver: { type: String, default: null },
})
const abierto = defineModel('open', { type: Boolean, default: false })

const user = inject('$user')
const { capture } = useTelemetry()

const modoKit = computed(() => !props.desdeCarrito)

const catalogo = createResource({
	url: 'taar_lms.kits.catalogo',
	makeParams: () => ({ curso: props.curso }),
})

watch(
	abierto,
	(si) => {
		if (!si) return
		error.value = ''
		if (modoKit.value && props.curso) catalogo.reload()
		else if (!catalogo.data) catalogo.fetch()
		capture('kit_visto', { curso: props.curso || 'tienda' })
	},
	{ immediate: true }
)

const kit = computed(() => (modoKit.value ? catalogo.data?.kit : null))
const cargando = computed(() => catalogo.loading && !catalogo.data)
const estados = computed(() => catalogo.data?.estados || [])

const lista = computed(() => {
	if (!modoKit.value) return props.desdeCarrito || []
	return kit.value?.articulos || []
})

const titulo = computed(() =>
	modoKit.value ? kit.value?.titulo || __('Materials kit') : __('Your order')
)

// Lo marcado de entrada: lo preseleccionado y lo obligatorio.
const marcados = reactive({})
watch(
	lista,
	(items) => {
		for (const item of items) {
			if (!(item.articulo in marcados)) {
				marcados[item.articulo] =
					!modoKit.value || ((item.preseleccionado || item.obligatorio) && !item.agotado)
			}
		}
	},
	{ immediate: true }
)

function alternar(articulo) {
	marcados[articulo] = !marcados[articulo]
	recotizar()
}

const seleccion = computed(() =>
	lista.value
		.filter((x) => marcados[x.articulo] && !x.agotado)
		.map((x) => ({ articulo: x.articulo, cantidad: x.cantidad }))
)

// Solo para enseñar mientras no hay cotización; lo que se cobra lo dice el servidor.
const subtotalVista = computed(() =>
	lista.value
		.filter((x) => marcados[x.articulo] && !x.agotado)
		.reduce((s, x) => s + x.precio * x.cantidad, 0)
)

const puedePedir = computed(
	() => !!user?.data && !!catalogo.data?.vendible && seleccion.value.length > 0
)
const motivoSinCompra = computed(() => {
	if (!catalogo.data?.vendible) return __('Kits will be available to order very soon.')
	if (!user?.data) return __('Log in to order your kit.')
	return __('Choose at least one material.')
})

// ── Envío ────────────────────────────────────────────────────────────────
const direccion = reactive({
	cp: '',
	receptor: user?.data?.full_name || '',
	telefono: '',
	calle: '',
	colonia: '',
	ciudad: '',
	estado_mx: '',
	referencias: '',
})
const envio = ref(null)
const error = ref('')

const cotizacion = createResource({
	url: 'taar_lms.kits.cotizar',
	method: 'POST',
	makeParams: () => ({
		articulos: seleccion.value,
		cp: direccion.cp,
		curso: modoKit.value ? props.curso : null,
	}),
	onSuccess(datos) {
		error.value = ''
		const ids = (datos.envio || []).map((o) => o.id)
		if (!ids.includes(envio.value)) envio.value = ids[0] || null
		capture('kit_cotizado', { curso: props.curso || 'tienda', cp: direccion.cp })
	},
	onError(err) {
		error.value = mensajeDe(err)
	},
})

const opcionesEnvio = computed(() =>
	direccion.cp.length === 5 ? cotizacion.data?.envio || [] : []
)
const opcionElegida = computed(() => opcionesEnvio.value.find((o) => o.id === envio.value))

function alCambiarCp() {
	direccion.cp = direccion.cp.replace(/\D/g, '').slice(0, 5)
	if (direccion.cp.length === 5) recotizar()
}

function recotizar() {
	if (direccion.cp.length === 5 && seleccion.value.length) cotizacion.reload()
}

// ── Pagar ────────────────────────────────────────────────────────────────
const preparando = ref(false)

async function continuar() {
	if (!opcionElegida.value) return
	error.value = ''
	preparando.value = true
	try {
		const r = await call('taar_lms.kits.preparar', {
			articulos: seleccion.value,
			direccion: { ...direccion },
			envio: envio.value,
			curso: modoKit.value ? props.curso : null,
		})
		capture('kit_pagar_clic', { curso: props.curso || 'tienda', total: r.total })
		pagarPedido(r.destino, props.volver || window.location.pathname)
	} catch (err) {
		error.value = mensajeDe(err)
		// Si el envío cambió, se vuelve a cotizar para que elija con la cifra nueva.
		recotizar()
	} finally {
		preparando.value = false
	}
}

function mensajeDe(err) {
	const msg = err?.messages?.[0] || err?.message || ''
	return msg.replace(/<[^>]+>/g, '') || __('Something went wrong. Please try again.')
}
</script>

<style>
/* Sin scoped: el diálogo de frappe-ui pinta fuera del componente. */
.taar-kit .taar-kit-campo {
	display: flex;
	flex-direction: column;
	gap: 4px;
}
.taar-kit .taar-kit-campo > span {
	font-size: 14px;
	color: var(--ink-gray-6);
}
/* 16px de verdad: Safari hace zoom al enfocar un campo más chico. */
.taar-kit .taar-kit-campo input,
.taar-kit .taar-kit-campo select {
	font-size: 16px;
	padding: 9px 11px;
	border: 1px solid var(--outline-gray-2);
	border-radius: 8px;
	background: var(--surface-elevation-1);
	color: var(--ink-gray-9);
	width: 100%;
}
.taar-kit .taar-kit-check {
	width: 20px;
	height: 20px;
	flex-shrink: 0;
}
</style>
