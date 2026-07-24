<template>
	<Dialog
		v-model="show"
		:options="{ title: __('Welcome to TanArtistic!'), size: 'md' }"
	>
		<template #body-content>
			<div class="space-y-3 text-base text-ink-gray-8">
				<p>
					{{
						tipo === 'membresia'
							? __(
									'Your payment was successful. Your access to all courses will be ready in a few seconds.'
							  )
							: __(
									'Purchase successful! Your access will be ready in a few seconds.'
							  )
					}}
				</p>

				<!-- Cargando info del pago -->
				<div
					v-if="sessionId && info.loading"
					class="flex justify-center py-2"
				>
					<LoadingIndicator class="size-5 text-ink-gray-5" />
				</div>

				<!-- Cuenta nueva: crear contraseña aquí mismo -->
				<template v-else-if="info.data?.necesita_password">
					<p v-if="info.data.email">
						{{ __('Your purchase is linked to {0}.').format(info.data.email) }}
					</p>
					<p class="font-medium text-ink-gray-9">
						{{ __('Create your password to access your courses.') }}
					</p>
					<FormControl
						v-model="password"
						type="password"
						:label="__('Password')"
						:placeholder="__('At least 8 characters')"
					/>
					<FormControl
						v-model="password2"
						type="password"
						:label="__('Confirm password')"
					/>
					<Button
						variant="solid"
						size="md"
						class="w-full"
						:loading="creando"
						@click="crearPassword()"
					>
						{{ __('Create my password and start') }}
					</Button>
				</template>

				<!-- Cuenta existente sin sesión: a iniciar sesión -->
				<template v-else-if="info.data && !info.data.sesion_activa">
					<p>
						{{ __('This account already has access. Log in to continue.') }}
					</p>
					<Button
						variant="solid"
						size="md"
						class="w-full"
						@click="irALogin()"
					>
						{{ __('Log in') }}
					</Button>
				</template>

				<!-- Ya con sesión: solo la bienvenida -->
				<Button
					v-else
					variant="solid"
					size="md"
					class="w-full"
					@click="show = false"
				>
					{{ __('Explore the courses') }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import {
	Button,
	call,
	createResource,
	Dialog,
	FormControl,
	LoadingIndicator,
	toast,
} from 'frappe-ui'
import { ref, watch } from 'vue'

const show = defineModel()

const props = defineProps({
	sessionId: { type: String, default: null },
	tipo: { type: String, default: 'membresia' },
})

const password = ref('')
const password2 = ref('')
const creando = ref(false)

const info = createResource({
	url: 'taar_lms.api.info_post_pago',
	makeParams() {
		return { session_id: props.sessionId }
	},
})

watch(
	() => [show.value, props.sessionId],
	() => {
		if (show.value && props.sessionId) info.reload()
	},
	{ immediate: true }
)

const crearPassword = async () => {
	if (password.value.length < 8) {
		toast.warning(__('The password must have at least 8 characters.'))
		return
	}
	if (password.value !== password2.value) {
		toast.warning(__('Passwords do not match.'))
		return
	}
	creando.value = true
	try {
		await call('taar_lms.api.completar_registro', {
			session_id: props.sessionId,
			password: password.value,
		})
		toast.success(__('Your account is ready!'))
		// La sesión ya quedó iniciada en el servidor: recargar para entrar.
		setTimeout(() => window.location.reload(), 800)
	} catch (err) {
		const msg = typeof err === 'string' ? err : err.messages?.[0] ?? 'Error'
		toast.error(__(msg))
		creando.value = false
	}
}

const irALogin = () => {
	window.location.href = `/login?redirect-to=${encodeURIComponent(
		window.location.pathname
	)}`
}
</script>
