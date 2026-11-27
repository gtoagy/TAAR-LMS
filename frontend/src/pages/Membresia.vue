<template>
	<div class="h-full">
		<!-- En el móvil sobra: la barra superior ya dice dónde está. -->
		<header
			v-if="!titulo"
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-base px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs class="h-7" :items="breadcrumbs" />
		</header>
		<div
			v-if="membership.loading"
			class="flex flex-1 items-center justify-center p-5"
		>
			<LoadingIndicator class="size-5 text-ink-gray-5" />
		</div>
		<div v-else-if="membership.data" class="p-5">
			<div class="max-w-3xl mx-auto mt-8 text-center">
				<div
					class="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-surface-gray-2"
				>
					<Crown class="size-6 text-ink-gray-7" />
				</div>
				<!-- Con la barra superior del móvil el título ya está arriba. -->
				<h1 v-if="!titulo" class="mb-2 text-title font-semibold text-ink-gray-9">
					{{ __('Membership') }}
				</h1>
				<p class="mb-8 text-body text-ink-gray-7">
					{{ __('Unlimited access to the membership courses.') }}
				</p>

				<!-- Miembro activo o en mora -->
				<div
					v-if="membership.data.is_member"
					class="rounded-lg border p-6 text-start"
					:class="
						membership.data.status === 'En mora'
							? 'border-orange-300 bg-orange-50'
							: 'border-outline-gray-2 bg-surface-base'
					"
				>
					<div class="mb-1 flex flex-wrap items-center gap-2">
						<span class="text-heading font-semibold text-ink-gray-9">
							{{ __('Your membership is active.') }}
						</span>
						<span
							v-if="nombrePlan"
							class="rounded-full bg-surface-gray-3 px-2 py-0.5 text-micro font-semibold uppercase tracking-wide text-ink-gray-7"
						>
							{{ nombrePlan }}
						</span>
					</div>
					<p
						v-if="membership.data.status === 'En mora'"
						class="mb-2 text-body text-orange-700"
					>
						{{
							conPaypal
								? __(
										'We could not process your last payment in PayPal. Check your payment method there to keep your access.'
								  )
								: __(
										'We could not process your last payment. Please update your card to keep your access.'
								  )
						}}
					</p>
					<p
						v-if="membership.data.period_end"
						class="text-body text-ink-gray-7"
					>
						<template v-if="conPaseAnual && membership.data.en_gracia">
							{{
								__(
									'Your annual pass expired on {0}. You can still renew it at the same price.'
								).format(membership.data.period_end)
							}}
						</template>
						<template v-else-if="conMesUnico">
							{{
								__(
									'Your month ends on {0}. Subscribe to keep your access: the first charge comes when your month ends, so you never pay twice.'
								).format(membership.data.period_end)
							}}
						</template>
						<template v-else-if="membership.data.cancel_at_period_end">
							{{
								__(
									'Your membership ends on {0}. You keep full access until then.'
								).format(membership.data.period_end)
							}}
						</template>
						<template v-else>
							{{
								__('Next renewal: {0}').format(membership.data.period_end)
							}}
						</template>
					</p>
					<div class="flex flex-wrap gap-2 mt-5">
						<router-link :to="{ name: 'Courses' }">
							<Button variant="solid">
								{{ __('Go to my courses') }}
							</Button>
						</router-link>
						<!-- El Mes único se pagó una vez y no hay suscripción detrás: el
						     portal de Stripe no tendría nada que enseñar (y falla sin
						     cliente). Lo que sí sirve es suscribirse antes de que acabe. -->
						<!-- El Pase anual tampoco tiene suscripción: se renueva con la
						     liga del precio congelado (pase.DESTINO_RENOVAR). -->
						<Button v-if="conPaseAnual" @click="irARenovar()">
							{{ __('Renew my pass') }}
						</Button>
						<Button v-else-if="conMesUnico" @click="irACheckout('mensual')">
							{{ __('Subscribe to keep my access') }}
						</Button>
						<!-- Quien paga con PayPal no tiene portal de Stripe: cancela
						     aquí mismo (paypal_suscripcion.cancelar_mi_suscripcion) y
						     cambia su cuenta o tarjeta desde su PayPal. -->
						<template v-else-if="conPaypal">
							<Button
								v-if="!membership.data.cancel_at_period_end && !confirmando"
								@click="confirmando = true"
							>
								{{ __('Cancel my subscription') }}
							</Button>
							<a
								href="https://www.paypal.com/myaccount/autopay/"
								target="_blank"
								rel="noopener"
							>
								<Button variant="subtle">{{ __('Open my PayPal') }}</Button>
							</a>
						</template>
						<Button v-else @click="irAPortal()">
							{{ __('Manage my membership') }}
						</Button>
					</div>
					<div
						v-if="conPaypal && confirmando"
						class="mt-4 rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-4"
					>
						<p class="text-body text-ink-gray-8">
							{{
								__(
									'If you cancel, PayPal will not charge you again and you keep your access until {0}.'
								).format(membership.data.period_end)
							}}
						</p>
						<div class="mt-3 flex flex-wrap gap-2">
							<Button
								variant="solid"
								theme="red"
								:loading="cancelar.loading"
								@click="cancelar.submit()"
							>
								{{ __('Yes, cancel it') }}
							</Button>
							<Button @click="confirmando = false">{{ __('Keep it') }}</Button>
						</div>
						<p v-if="cancelar.error" class="mt-3 text-support text-red-600">
							{{ __('We could not cancel it. Try again in a moment or write to us.') }}
						</p>
					</div>
					<p v-if="conPaypal" class="mt-4 text-support text-ink-gray-6">
						{{
							__(
								'Your subscription is paid with PayPal. To change the account or card it is charged to, go to your PayPal.'
							)
						}}
					</p>
					<p v-else-if="!conMesUnico && !conPaseAnual" class="mt-4 text-support text-ink-gray-6">
						{{
							__(
								'From "Manage my membership" you can change your card, download your invoices or cancel your subscription.'
							)
						}}
					</p>
				</div>

				<!-- Con el plan mensual los cursos maestros siguen fuera, y hasta
				     ahora solo se enteraba quien abría una de sus fichas. Aquí es
				     donde se mira la membresía, así que aquí se cuenta. -->
				<div
					v-if="puedeMejorar"
					class="mt-4 rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-6 text-start"
				>
					<div class="mb-1 text-heading font-semibold text-ink-gray-9">
						{{ __('Your plan is the monthly one.') }}
					</div>
					<p class="text-body text-ink-gray-7">
						{{ __('With the annual plan you also get:') }}
					</p>
					<div class="my-4 space-y-2 text-body text-ink-gray-8">
						<div
							v-for="curso in comparativa.cursos_solo_anual"
							:key="curso"
							class="flex items-start gap-2"
						>
							<Check class="mt-1 size-4 shrink-0 text-green-600" />
							{{ curso }}
						</div>
						<div class="flex items-start gap-2">
							<Check class="mt-1 size-4 shrink-0 text-green-600" />
							{{ __('2 months free compared to paying month by month') }}
						</div>
					</div>
					<p
						v-if="comparativa.valor_sueltos"
						class="mb-4 text-support text-ink-gray-6"
					>
						{{
							__('Bought separately they cost {0}.').format(
								comparativa.valor_sueltos
							)
						}}
					</p>
					<Button variant="solid" @click="irAPortal(true)">
						<template #prefix>
							<Crown class="size-4" />
						</template>
						{{ __('Change to the annual plan') }}
					</Button>
					<p class="mt-3 text-support text-ink-gray-6">
						{{
							__(
								'Stripe shows you what you pay today, with the part you already paid this month discounted.'
							)
						}}
					</p>
				</div>

				<!-- Solo para quien no es miembro. A quien ya paga no se le vuelven
				     a ofrecer los dos planes: con el anual ya tiene todo, y al del
				     mensual se le habla arriba, en su caja. Lo que separa a un plan
				     de otro son los cursos maestros, y callarlo acaba en
				     reclamación de quien paga el mensual. -->
				<div
					v-else-if="!membership.data.is_member"
					class="grid gap-4 text-start sm:grid-cols-2"
				>
					<!-- Mensual -->
					<div
						class="flex flex-col rounded-lg border border-outline-gray-2 bg-surface-base p-6"
					>
						<div class="flex items-center gap-2">
							<span
								class="text-label font-medium uppercase tracking-wide text-ink-gray-6"
							>
								{{ __('Monthly') }}
							</span>
							<span
								v-if="membership.data.especial"
								class="rounded-full bg-amber-100 px-2 py-0.5 text-micro font-semibold text-amber-800"
							>
								{{ __('Full access') }}
							</span>
						</div>
						<div
							class="mt-2 text-title font-bold tabular-nums text-ink-gray-9 md:text-display"
						>
							{{ membership.data.price_display }}
							<span class="text-support font-normal text-ink-gray-6">
								{{ __('/ month') }}
							</span>
						</div>
						<!-- Mientras dure la oferta de apertura el mensual abre todo, así
						     que se pinta con lo que de verdad incluye. Callarlo sería el
						     mismo error que teníamos antes, pero al revés. -->
						<div
							v-if="membership.data.especial"
							class="my-5 flex-1 space-y-2 text-body text-ink-gray-8"
						>
							<div class="flex items-start gap-2">
								<Check class="mt-1 size-4 shrink-0 text-green-600" />
								<strong>
									{{
										__('All {0} courses included').format(
											comparativa.cursos_totales
										)
									}}
								</strong>
							</div>
							<div
								v-for="curso in comparativa.cursos_solo_anual"
								:key="curso"
								class="flex items-start gap-2"
							>
								<Check class="mt-1 size-4 shrink-0 text-green-600" />
								{{ curso }}
							</div>
							<div class="flex items-start gap-2">
								<Check class="mt-1 size-4 shrink-0 text-green-600" />
								{{ __('Cancel anytime') }}
							</div>
						</div>

						<div v-else class="my-5 flex-1 space-y-2 text-body text-ink-gray-8">
							<div class="flex items-start gap-2">
								<Check class="mt-1 size-4 shrink-0 text-green-600" />
								{{
									__('{0} courses of the membership').format(
										comparativa.cursos_mensual
									)
								}}
							</div>
							<div class="flex items-start gap-2">
								<Check class="mt-1 size-4 shrink-0 text-green-600" />
								{{ __('New courses at no extra cost') }}
							</div>
							<div class="flex items-start gap-2">
								<Check class="mt-1 size-4 shrink-0 text-green-600" />
								{{ __('Cancel anytime') }}
							</div>
							<div
								v-for="curso in comparativa.cursos_solo_anual"
								:key="curso"
								class="flex items-start gap-2 text-ink-gray-6"
							>
								<X class="mt-1 size-4 shrink-0 text-ink-gray-4" />
								{{ curso }}
							</div>
						</div>
						<p
							v-if="membership.data.especial"
							class="mb-4 text-support font-medium text-amber-800"
						>
							{{
								__(
									'Only until {0}. After that, the monthly plan stops including these courses.'
								).format(membership.data.especial.hasta)
							}}
						</p>
						<Button
							size="md"
							class="w-full"
							@click="irACheckout(membership.data.especial ? 'especial' : 'mensual')"
						>
							{{ __('Choose monthly') }}
						</Button>
					</div>

					<!-- Anual -->
					<div
						class="flex flex-col rounded-lg border-2 border-outline-gray-4 bg-surface-base p-6"
					>
						<div class="flex items-center gap-2">
							<span
								class="text-label font-medium uppercase tracking-wide text-ink-gray-6"
							>
								{{ __('Annual') }}
							</span>
							<span
								class="rounded-full bg-green-100 px-2 py-0.5 text-micro font-semibold text-green-700"
							>
								{{ __('2 months free') }}
							</span>
						</div>
						<div
							class="mt-2 text-title font-bold tabular-nums text-ink-gray-9 md:text-display"
						>
							{{ membership.data.price_display_anual }}
							<span class="text-support font-normal text-ink-gray-6">
								{{ __('/ year') }}
							</span>
						</div>
						<div class="my-5 flex-1 space-y-2 text-body text-ink-gray-8">
							<div class="flex items-start gap-2">
								<Check class="mt-1 size-4 shrink-0 text-green-600" />
								<strong>
									{{
										__('All {0} courses included').format(
											comparativa.cursos_totales
										)
									}}
								</strong>
							</div>
							<div
								v-for="curso in comparativa.cursos_solo_anual"
								:key="curso"
								class="flex items-start gap-2"
							>
								<Check class="mt-1 size-4 shrink-0 text-green-600" />
								{{ curso }}
							</div>
							<div class="flex items-start gap-2">
								<Check class="mt-1 size-4 shrink-0 text-green-600" />
								{{ __('New courses at no extra cost') }}
							</div>
						</div>
						<p
							v-if="comparativa.valor_sueltos"
							class="mb-4 text-support text-ink-gray-6"
						>
							{{
								__('Bought separately they cost {0}.').format(
									comparativa.valor_sueltos
								)
							}}
							<template v-if="comparativa.ahorro_anual">
								<strong class="text-ink-gray-8">
									{{ __('You save {0}.').format(comparativa.ahorro_anual) }}
								</strong>
							</template>
						</p>
						<Button
							variant="solid"
							size="md"
							class="w-full"
							@click="irACheckout('anual')"
						>
							{{ __('Choose annual') }}
						</Button>
					</div>

					<div class="sm:col-span-2 text-center">
						<p class="text-support text-ink-gray-6">
							{{ __('Prices are shown in your local currency at checkout.') }}
						</p>
						<p
							v-if="membership.data.status === 'Cancelada'"
							class="mt-2 text-support text-ink-gray-6"
						>
							{{
								__(
									'Your previous membership is canceled. Reactivate it to regain access immediately.'
								)
							}}
						</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import {
	Breadcrumbs,
	Button,
	createResource,
	LoadingIndicator,
} from 'frappe-ui'
import { computed, ref } from 'vue'
import { Check, Crown, X } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import { useTituloMovil } from '@/utils/navegacionMovil'

const { titulo } = useTituloMovil()

const { user } = sessionStore()

const membership = createResource({
	url: 'taar_lms.api.get_my_membership',
	auto: true,
	cache: ['membership', user],
})

// La diferencia entre planes la calcula el servidor leyendo los cursos, para que
// esta página no pueda quedarse prometiendo lo que ya dejó de ser cierto.
const comparativa = computed(
	() =>
		membership.data?.comparativa || {
			cursos_solo_anual: [],
			cursos_totales: 0,
			cursos_mensual: 0,
			valor_sueltos: null,
			ahorro_anual: null,
		}
)

// Qué plan tiene en vigor. Los miembros que llegaron de Disco todavía no lo
// tienen anotado: a esos no se les inventa uno.
const nombrePlan = computed(() => {
	if (membership.data?.plan === 'Anual') return __('TAN PRO annual')
	if (membership.data?.plan === 'Mensual') return __('TAN PRO monthly')
	return ''
})

const irACheckout = (plan) => {
	// Misma puerta que usan los botones de la landing: sabe explicarse si la
	// compra no puede empezar, y devuelve aquí a quien se arrepienta en Stripe.
	window.location.href = `/comprar/${plan}?volver=/lms/membresia`
}

// El Mes único (pago único de un mes) sin suscripción que tome el relevo: en
// cuanto se suscribe, la ficha deja de estar "sin renovar" y vuelve el portal.
const conMesUnico = computed(
	() =>
		membership.data?.pase &&
		membership.data?.pase_tipo === 'mes' &&
		membership.data?.cancel_at_period_end
)

// El Pase anual (pago único de un año): el servidor manda la liga para
// renovarlo al precio que pagó cuando el pase se vende abierto.
const conPaseAnual = computed(
	() => membership.data?.pase && membership.data?.pase_tipo === 'anual' && membership.data?.renovar
)
const irARenovar = () => {
	window.location.href = `${membership.data.renovar}?volver=/lms/membresia`
}

// Paga con una suscripción de PayPal: sin portal de Stripe ni cambio de plan
// desde ahí (eso es de Stripe); la cancelación va por la escuela.
const conPaypal = computed(() => membership.data?.proveedor === 'paypal')
const confirmando = ref(false)
const cancelar = createResource({
	url: 'taar_lms.paypal_suscripcion.cancelar_mi_suscripcion',
	method: 'POST',
	onSuccess(data) {
		confirmando.value = false
		membership.setData(data)
	},
})

// Solo con el plan mensual identificado: a los miembros migrados que todavía no
// tienen plan anotado no se les ofrece un cambio que quizá ya hicieron.
const puedeMejorar = computed(
	() =>
		membership.data?.is_member &&
		membership.data?.plan === 'Mensual' &&
		!membership.data?.cancel_at_period_end &&
		!conPaypal.value &&
		comparativa.value.cursos_solo_anual.length > 0
)

const irAPortal = (mejorar = false) => {
	window.location.href = mejorar
		? '/api/method/taar_lms.api.ir_a_portal?mejorar=1'
		: '/api/method/taar_lms.api.ir_a_portal'
}

const breadcrumbs = computed(() => [
	{
		label: __('Membership'),
		route: { name: 'Membresia' },
	},
])
</script>
