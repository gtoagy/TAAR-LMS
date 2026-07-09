<template>
	<div class="h-full">
		<header
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
			<div class="max-w-xl mx-auto mt-8 text-center">
				<div
					class="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-surface-gray-2"
				>
					<Crown class="size-6 text-ink-gray-7" />
				</div>
				<h1 class="text-2xl font-semibold text-ink-gray-9 mb-2">
					{{ __('Membership') }}
				</h1>
				<p class="text-base text-ink-gray-7 mb-8">
					{{ __('Unlimited access to all courses on the platform.') }}
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
					<div class="text-lg font-medium text-ink-gray-9 mb-1">
						{{ __('Your membership is active.') }}
					</div>
					<p
						v-if="membership.data.status === 'En mora'"
						class="text-base text-orange-700 mb-2"
					>
						{{
							__(
								'We could not process your last payment. Please update your card to keep your access.'
							)
						}}
					</p>
					<p
						v-if="membership.data.period_end"
						class="text-base text-ink-gray-7"
					>
						<template v-if="membership.data.cancel_at_period_end">
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
						<Button @click="irAPortal()">
							{{ __('Manage my membership') }}
						</Button>
					</div>
					<p class="text-sm text-ink-gray-5 mt-4">
						{{
							__(
								'From "Manage my membership" you can change your card, download your invoices or cancel your subscription.'
							)
						}}
					</p>
				</div>

				<!-- Sin membresía / cancelada -->
				<div
					v-else
					class="rounded-lg border border-outline-gray-2 bg-surface-base p-8"
				>
					<div class="text-4xl font-bold text-ink-gray-9">
						{{ membership.data.price_display }}
						<span class="text-base font-normal text-ink-gray-5">
							{{ __('/ month') }}
						</span>
					</div>
					<div class="my-6 space-y-2 text-start text-base text-ink-gray-8">
						<div class="flex items-center gap-2">
							<Check class="size-4 text-green-600" />
							{{ __('All courses included') }}
						</div>
						<div class="flex items-center gap-2">
							<Check class="size-4 text-green-600" />
							{{ __('New courses at no extra cost') }}
						</div>
						<div class="flex items-center gap-2">
							<Check class="size-4 text-green-600" />
							{{ __('Cancel anytime') }}
						</div>
					</div>
					<Button variant="solid" size="md" class="w-full" @click="irACheckout()">
						{{ __('Become a member') }}
					</Button>
					<p
						v-if="membership.data.status === 'Cancelada'"
						class="text-sm text-ink-gray-5 mt-4"
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
</template>

<script setup>
import {
	Breadcrumbs,
	Button,
	createResource,
	LoadingIndicator,
} from 'frappe-ui'
import { computed } from 'vue'
import { Check, Crown } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'

const { user } = sessionStore()

const membership = createResource({
	url: 'taar_lms.api.get_my_membership',
	auto: true,
	cache: ['membership', user],
})

const irACheckout = () => {
	window.location.href = '/api/method/taar_lms.api.ir_a_checkout'
}

const irAPortal = () => {
	window.location.href = '/api/method/taar_lms.api.ir_a_portal'
}

const breadcrumbs = computed(() => [
	{
		label: __('Membership'),
		route: { name: 'Membresia' },
	},
])
</script>
