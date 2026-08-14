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
									'Your payment went through. Your access to the membership courses will be ready in a few seconds.'
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
					<!-- El nombre se pide aquí porque es la única vez que la escuela
					     puede preguntarlo. Stripe solo entrega el de la tarjeta: llega
					     en mayúsculas, o es el de quien prestó la tarjeta, y a veces no
					     llega. Se propone partido para que casi siempre solo haya que
					     mirarlo. -->
					<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
						<FormControl v-model="nombre" :label="__('First Name')" />
						<FormControl v-model="apellido" :label="__('Last Name')" />
					</div>

					<!-- El correo se enseña como un dato, no como un campo: es el que
					     usó para pagar y el que va a recibir sus accesos. Pero se
					     puede corregir, porque escribirlo mal en el checkout es de lo
					     más común y con la cuenta atada a un correo equivocado se
					     queda fuera de algo que ya pagó. -->
					<div
						v-if="info.data.email"
						class="rounded-md bg-surface-gray-2 px-3 py-2"
					>
						<div class="text-sm text-ink-gray-6">
							{{ __('Your account') }}
						</div>
						<div v-if="!editandoCorreo" class="flex items-center gap-2">
							<span class="font-medium text-ink-gray-9 break-all">
								{{ correo }}
							</span>
							<button
								class="shrink-0 text-sm text-ink-gray-6 underline"
								@click="editandoCorreo = true"
							>
								{{ __('Not your email?') }}
							</button>
						</div>
						<template v-else>
							<FormControl v-model="correo" type="email" class="mt-1" />
							<p class="mt-1 text-sm text-ink-gray-6">
								{{ __('Here is where your access and your invoices arrive.') }}
							</p>
						</template>
					</div>
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

				<!-- Ya era alumna: no puede poner contraseña nueva sin identificarse
				     (si no, quien pagara con el correo de otra se quedaría con su
				     cuenta), pero sí resolverlo aquí mismo si no la recuerda. -->
				<template v-else-if="info.data && !info.data.sesion_activa">
					<p>
						{{
							__('You already have an account with {0}.').format(
								info.data.email
							)
						}}
					</p>
					<Button
						variant="solid"
						size="md"
						class="w-full"
						@click="irALogin()"
					>
						{{ __('Log in with my password') }}
					</Button>
					<p v-if="enlaceEnviado" class="text-sm text-ink-gray-6">
						{{
							__('We sent you a link to {0}. Check your inbox.').format(
								info.data.email
							)
						}}
					</p>
					<Button
						v-else
						size="md"
						class="w-full"
						:loading="enviandoEnlace"
						@click="enviarEnlace()"
					>
						{{ __('I do not remember it, send me a link') }}
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
const correo = ref('')
const nombre = ref('')
const apellido = ref('')
const editandoCorreo = ref(false)
const enviandoEnlace = ref(false)
const enlaceEnviado = ref(false)

const info = createResource({
	url: 'taar_lms.api.info_post_pago',
	makeParams() {
		return { session_id: props.sessionId }
	},
	onSuccess(data) {
		correo.value = data?.email || ''
		nombre.value = data?.nombre || ''
		apellido.value = data?.apellido || ''
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
	if (!nombre.value.trim()) {
		toast.warning(__('Tell us your name.'))
		return
	}
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
			correo: correo.value || undefined,
			nombre: nombre.value,
			apellido: apellido.value,
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

const enviarEnlace = async () => {
	enviandoEnlace.value = true
	try {
		await call('taar_lms.api.enviar_enlace_acceso', {
			session_id: props.sessionId,
		})
		enlaceEnviado.value = true
	} catch (err) {
		const msg = typeof err === 'string' ? err : err.messages?.[0] ?? 'Error'
		toast.error(__(msg))
	}
	enviandoEnlace.value = false
}

const irALogin = () => {
	window.location.href = `/login?redirect-to=${encodeURIComponent(
		window.location.pathname
	)}`
}
</script>
