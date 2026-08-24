<template>
	<!-- El asistente de bienvenida.

	     No se puede cerrar: quien acaba de pagar tiene que salir de aquí con su
	     contraseña puesta, y a quien lleva tiempo con nosotras le preguntamos una
	     sola vez en su vida. Si aun así cierra la pestaña, vuelve a salirle al
	     entrar, porque lo que decide si aparece vive en el servidor y no en la
	     dirección de la página. -->
	<Dialog
		v-model="show"
		:options="{ size: 'lg' }"
		:disable-outside-click-to-close="true"
	>
		<template #body>
			<div class="taar-asistente">
				<!-- Cargando -->
				<div v-if="cargando" class="flex justify-center py-16">
					<LoadingIndicator class="size-6 text-ink-gray-5" />
				</div>

				<!-- El pago todavía no se ha confirmado.

				     Antes esto caía en el mismo sitio que un error de red: un botón
				     suelto, sin sesión y sin explicación. Con OXXO y con
				     transferencia, que es como paga mucha gente en México, el
				     dinero tarda horas en llegar. -->
				<template v-else-if="estado === 'pago_pendiente'">
					<h2 class="taar-titulo">{{ __('Your payment is on its way') }} ⏳</h2>
					<p class="taar-apoyo">
						{{
							__(
								'Payments with OXXO or bank transfer take a few hours to be confirmed.'
							)
						}}
					</p>
					<div class="taar-aviso">
						{{ __('As soon as it arrives we will write to {0} with your access.').format(datos?.email || '') }}
						{{ __('You do not need to do anything else.') }}
					</div>
					<div class="taar-acciones">
						<a
							v-if="datos?.soporte"
							:href="datos.soporte"
							target="_blank"
							rel="noopener"
							class="taar-boton taar-boton-wa"
						>
							{{ __('Write to us if you have questions') }}
						</a>
					</div>
				</template>

				<!-- Ya tenía cuenta antes de este pago.

				     Aquí no se le deja poner contraseña: si bastara con que la
				     cuenta no hubiera entrado nunca, cualquiera podría pagar
				     escribiendo el correo de otra alumna y quedarse con su cuenta.
				     Se identifica abriendo su correo, que es lo correcto. -->
				<template v-else-if="estado === 'existente'">
					<h2 class="taar-titulo">{{ __('You already have an account with us') }} 👋</h2>
					<p class="taar-apoyo">
						{{ __('Your purchase is linked to {0}.').format(datos?.email || '') }}
					</p>
					<div v-if="enlaceEnviado" class="taar-aviso">
						{{ __('We sent you a link to {0}. Check your inbox.').format(datos?.email || '') }}
					</div>
					<div class="taar-acciones">
						<button class="taar-boton" @click="irALogin()">
							{{ __('Log in with my password') }}
						</button>
						<button
							v-if="!enlaceEnviado"
							class="taar-boton taar-boton-fantasma"
							:disabled="enviandoEnlace"
							@click="enviarEnlace()"
						>
							{{ __('I do not remember it, send me a link') }}
						</button>
					</div>
				</template>

				<!-- ── El asistente propiamente dicho ── -->
				<template v-else>
					<div v-if="totalPasos > 1" class="taar-progreso">
						<span class="taar-progreso-rotulo">
							{{ __('Step {0} of {1}').format(pasoVisible, totalPasos) }}
						</span>
						<div class="taar-segmentos">
							<i
								v-for="n in totalPasos"
								:key="n"
								:class="{ hecho: n <= pasoVisible }"
							></i>
						</div>
					</div>

					<!-- Paso: la cuenta. Solo dos cosas, que es lo justo para alguien
					     que acaba de pagar: cuál es su cuenta y con qué entra. -->
					<template v-if="paso === 'cuenta'">
						<h2 class="taar-titulo">{{ __('You are part of TanArtistic now') }} 🎨</h2>
						<p class="taar-apoyo">
							{{ __('We received your payment. Create your password and we are in.') }}
						</p>

						<div class="taar-campos">
							<!-- El correo se enseña como un dato y no como un campo: es
							     el que usó para pagar. Pero se puede corregir, porque
							     escribirlo mal en el checkout es de lo más común y con
							     la cuenta atada a un correo equivocado se queda fuera de
							     algo que ya pagó. Va aquí y no en el paso siguiente
							     porque decide QUÉ cuenta recibe esta contraseña. -->
							<div v-if="datos?.email" class="taar-caja-dato">
								<div class="taar-caja-et">{{ __('Your account') }}</div>
								<div v-if="!editandoCorreo" class="taar-caja-val">
									<span>{{ correo }}</span>
									<button class="taar-enlace" @click="editandoCorreo = true">
										{{ __('Not your email?') }}
									</button>
								</div>
								<template v-else>
									<FormControl v-model="correo" type="email" class="mt-1" />
									<p class="taar-pista">
										{{ __('Here is where your access and your invoices arrive.') }}
									</p>
								</template>
							</div>

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
						</div>

						<div class="taar-acciones">
							<button class="taar-boton" :disabled="creando" @click="crearPassword()">
								{{ creando ? __('One moment…') : __('Create my password') }}
							</button>
						</div>
					</template>

					<!-- Paso: sus datos.

					     Solo aparece si falta algo. Cuando se importen el nombre, el
					     celular y el país de la plataforma anterior, quien ya los tenga
					     no vera esta pantalla. -->
					<template v-else-if="paso === 'datos'">
						<h2 class="taar-titulo">{{ __('Tell us who you are') }} ✍️</h2>
						<p class="taar-apoyo">
							{{ __('So we can greet you by your name and let you know about live classes.') }}
						</p>

						<div class="taar-campos">
							<div class="taar-fila">
								<FormControl v-model="nombre" :label="__('First Name')" />
								<FormControl v-model="apellido" :label="__('Last Name')" />
							</div>
							<div class="taar-fila">
								<FormControl
									v-model="celular"
									:label="__('Mobile number')"
									:placeholder="__('e.g. +52 998 123 4567')"
								/>
								<!-- Sin placeholder propio, frappe-ui pone "Select option"
								     en inglés y se cuela en una pantalla que por lo demás
								     está entera en español. -->
								<FormControl
									v-model="pais"
									type="select"
									:label="__('Country')"
									:options="opcionesPais"
									:placeholder="__('Choose your country')"
								/>
							</div>
							<p class="taar-pista">
								{{ __('This is how we let you know about live classes on WhatsApp.') }}
							</p>
						</div>

						<div class="taar-acciones">
							<button class="taar-boton" :disabled="guardandoDatos" @click="guardarDatos()">
								{{ guardandoDatos ? __('One moment…') : __('Continue') }}
							</button>
							<button v-if="pasoDeCuenta" class="taar-atras" @click="paso = 'cuenta'">
								{{ __('Back to previous') }}
							</button>
						</div>
					</template>

					<!-- Paso: la comunidad.

					     Va antes de las preguntas a propósito: primero recibe algo y
					     luego se le pide. El enlace lo sirve el servidor y solo a
					     quien ha pagado. -->
					<template v-else-if="paso === 'comunidad'">
						<h2 class="taar-titulo">{{ __('You are not painting alone') }} 💛</h2>
						<p class="taar-apoyo">
							{{ __('You have a WhatsApp group with the other students and with me.') }}
						</p>

						<div class="taar-comunidad">
							<div class="taar-comunidad-icono" aria-hidden="true">🎨</div>
							<ul class="taar-ventajas">
								<li>
									<span aria-hidden="true">›</span>
									<span>{{ __('Show what you paint and get real feedback.') }}</span>
								</li>
								<li>
									<span aria-hidden="true">›</span>
									<span>{{ __('Live classes are announced there first.') }}</span>
								</li>
								<li>
									<span aria-hidden="true">›</span>
									<span>{{ __('If you get stuck on a step, just ask.') }}</span>
								</li>
							</ul>
							<a
								v-if="asistente?.comunidad"
								:href="asistente.comunidad"
								target="_blank"
								rel="noopener"
								class="taar-boton taar-boton-wa"
								@click="abrioComunidad()"
							>
								{{ __('Join the WhatsApp group') }}
							</a>
						</div>

						<div class="taar-acciones">
							<button class="taar-boton" :disabled="yendo" @click="irAPreguntas()">
								{{ yendo ? __('One moment…') : __('Continue') }}
							</button>
							<button v-if="puedeVolver" class="taar-atras" @click="volver()">
								{{ __('Back to previous') }}
							</button>
						</div>
					</template>

					<!-- Paso: las preguntas, una por pantalla -->
					<template v-else-if="paso === 'preguntas'">
						<h2 class="taar-titulo">{{ __('Tell us more about you') }} 🤩</h2>
						<p class="taar-apoyo">
							{{ __('Two quick questions so we know what to record next.') }}
						</p>

						<div class="taar-pregunta">
							<div class="taar-pregunta-meta">
								<span class="taar-cuenta">
									{{ __('Question {0} of {1}').format(indicePregunta + 1, preguntas.length) }}
								</span>
								<span class="taar-pastilla">{{ __('Required') }}</span>
							</div>
							<div class="taar-enunciado">
								<span class="taar-indice">{{ indicePregunta + 1 }}</span>
								<p>{{ preguntaActual?.titulo }}</p>
							</div>
						</div>
						<p class="taar-privacidad">🔒 {{ __('Only we see this.') }}</p>

						<div class="taar-opciones">
							<button
								v-for="(opcion, i) in preguntaActual?.opciones || []"
								:key="opcion"
								class="taar-opcion"
								:aria-pressed="respuestas[preguntaActual.campo] === opcion"
								@click="responder(opcion)"
							>
								<span class="taar-marca">
									<span v-if="respuestas[preguntaActual.campo] !== opcion">
										{{ letras[i] }}
									</span>
								</span>
								<span>{{ opcion }}</span>
							</button>
						</div>

						<div class="taar-acciones">
							<button class="taar-boton" :disabled="guardando" @click="siguientePregunta()">
								{{ guardando ? __('One moment…') : __('Continue') }}
							</button>
							<button class="taar-atras" @click="volver()">
								{{ __('Back to previous') }}
							</button>
						</div>
					</template>

					<!-- Paso: listo.

					     Existe además de por celebrarlo: mientras lee esto, el aviso
					     de Stripe termina de repartirle sus cursos por detrás, así
					     que no llega a una lista vacía. -->
					<template v-else-if="paso === 'listo'">
						<div class="taar-palomita" aria-hidden="true">✓</div>
						<h2 class="taar-titulo">{{ __('You are all set, artist!') }} 👩‍🎨</h2>
						<p class="taar-apoyo">
							{{ __('Your course is waiting for you. See you inside.') }}
						</p>
						<div class="taar-acciones">
							<button class="taar-boton" @click="entrar()">
								{{ __('Start painting') }} 🎨
							</button>
						</div>
					</template>
				</template>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { call, createResource, Dialog, FormControl, LoadingIndicator, toast } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/user'

const show = defineModel()

const props = defineProps({
	// Con session_id venimos de pagar. Sin él, esta es una alumna de siempre que
	// entra por el inicio de sesión y a la que todavía no le hemos preguntado.
	sessionId: { type: String, default: null },
	tipo: { type: String, default: 'membresia' },
})

const letras = ['A', 'B', 'C', 'D', 'E', 'F']

const paso = ref('cuenta')
const estado = ref(null)
const datos = ref(null)
const asistente = ref(null)
const cargando = ref(true)

const nombre = ref('')
const apellido = ref('')
const correo = ref('')
const celular = ref('')
const pais = ref('')
const password = ref('')
const password2 = ref('')
const editandoCorreo = ref(false)

const creando = ref(false)
const guardando = ref(false)
const guardandoDatos = ref(false)
const enviandoEnlace = ref(false)
const enlaceEnviado = ref(false)

const indicePregunta = ref(0)
const respuestas = ref({})

const preguntas = computed(() => asistente.value?.preguntas || [])
const preguntaActual = computed(() => preguntas.value[indicePregunta.value])

const opcionesPais = computed(() =>
	(datos.value?.paises || []).map((p) => ({ label: p, value: p }))
)

/*
 * Cada alumna recorre solo los pasos que le faltan, y el contador cuenta esos.
 *
 * Quien ya tenía cuenta no pasa por la contraseña; quien ya nos dio su nombre y
 * su celular no pasa por los datos; quien ya nos contó de ella no pasa por las
 * preguntas. Decirle "paso 2 de 5" a quien solo va a ver tres pantallas sería
 * mentirle, y eso, en la pantalla de después de pagar, se nota.
 *
 * De aquí sale gratis lo de importar los datos de la plataforma anterior: quien
 * los tenga se salta esas pantallas sin que haya que tocar nada.
 */
const pasoDeCuenta = computed(() => estado.value === 'nueva')
const pasoDeDatos = computed(() => asistente.value?.faltan_datos !== false)
const pasoDePreguntas = computed(
	() => asistente.value?.faltan_respuestas !== false && preguntas.value.length > 0
)

/*
 * El recorrido se decide UNA VEZ y no se recalcula por el camino.
 *
 * Si se recalculara, al rellenar sus datos ese paso desaparecería del recorrido
 * y el contador saltaría de "paso 1 de 4" a "paso 1 de 3": después de escribir
 * su nombre y su celular, parecería que no ha avanzado nada. Lo que le falta se
 * mira al abrir el asistente; lo que haga después ya no cambia el mapa.
 */
const recorridoFijo = ref(null)

const suRecorrido = computed(() => {
	if (recorridoFijo.value) return recorridoFijo.value
	const pasos = []
	if (pasoDeCuenta.value) pasos.push('cuenta')
	if (pasoDeDatos.value) pasos.push('datos')
	pasos.push('comunidad')
	if (pasoDePreguntas.value) pasos.push('preguntas')
	pasos.push('listo')
	return pasos
})

/** Congela el recorrido en cuanto sabemos qué le falta. */
const fijarRecorrido = () => {
	if (!recorridoFijo.value && asistente.value) {
		recorridoFijo.value = suRecorrido.value
	}
}

const totalPasos = computed(() => suRecorrido.value.length)
const pasoVisible = computed(() => suRecorrido.value.indexOf(paso.value) + 1)
const puedeVolver = computed(() => suRecorrido.value.indexOf(paso.value) > 0)

/** El siguiente de SU recorrido, saltándose lo que no le toca. */
const siguienteDe = (desde) => {
	const i = suRecorrido.value.indexOf(desde)
	return suRecorrido.value[i + 1] || 'listo'
}

/** El anterior de su recorrido. */
const anteriorDe = (desde) => {
	const i = suRecorrido.value.indexOf(desde)
	return i > 0 ? suRecorrido.value[i - 1] : desde
}

/* ── Carga ────────────────────────────────────────────────────────────────── */

const infoPago = createResource({
	url: 'taar_lms.api.info_post_pago',
	makeParams: () => ({ session_id: props.sessionId }),
})

const estadoAsistente = createResource({
	url: 'taar_lms.api.estado_onboarding',
})

const cargar = async () => {
	cargando.value = true
	try {
		if (props.sessionId) {
			const d = await infoPago.fetch()
			datos.value = d
			estado.value = d?.estado
			correo.value = d?.email || ''
			nombre.value = d?.nombre || ''
			apellido.value = d?.apellido || ''
			celular.value = d?.celular || ''
			pais.value = d?.pais || ''
		} else {
			estado.value = 'con_sesion'
		}

		// El paso de la contraseña solo existe para una cuenta que nace de este
		// pago; el resto empieza por lo primero que le falte.
		if (estado.value === 'nueva') {
			paso.value = 'cuenta'
		}

		// Las preguntas y el enlace del grupo se piden con la sesión ya abierta, y
		// quien acaba de pagar todavía es una invitada: su sesión nace al crear la
		// contraseña, en el paso siguiente. Pedirlos antes devuelve "no tiene
		// permiso para acceder a este recurso" y tumbaba el asistente entero justo
		// cuando más falta hace, recién hecho el pago.
		if (estado.value === 'con_sesion') {
			await cargarAsistente()
		}
	} catch (err) {
		// Si ni siquiera podemos saber en qué punto está, es mejor no enseñar un
		// asistente a medias: se cierra y la escuela funciona con normalidad.
		estado.value = null
		show.value = false
		avisar(err)
	}
	cargando.value = false
}

const cargarAsistente = async () => {
	const a = await estadoAsistente.fetch()
	asistente.value = a
	if (a?.respuestas) respuestas.value = { ...a.respuestas }

	// Lo que ya sabemos de ella se propone en el paso de datos, para que solo
	// tenga que confirmarlo. A quien acaba de pagar, el celular ya le llegó de
	// Stripe y no hay que pisarlo con lo que hubiera en la cuenta.
	if (a?.datos) {
		if (!nombre.value) nombre.value = a.datos.nombre || ''
		if (!apellido.value) apellido.value = a.datos.apellido || ''
		if (!celular.value) celular.value = a.datos.celular || ''
		if (!pais.value) pais.value = a.datos.pais || ''
	}
	if (a?.paises?.length && !datos.value?.paises) {
		datos.value = { ...(datos.value || {}), paises: a.paises }
	}

	if (!a?.pendiente) {
		show.value = false
		return
	}

	fijarRecorrido()

	// Si venía sin pago (una alumna de siempre entrando), su primera pantalla es
	// la primera que le falte.
	if (!props.sessionId) paso.value = suRecorrido.value[0]
}

watch(
	() => [show.value, props.sessionId],
	() => {
		if (show.value) cargar()
	},
	{ immediate: true }
)

/* ── Paso 1 ───────────────────────────────────────────────────────────────── */

const crearPassword = async () => {
	if (password.value.length < 8)
		return toast.warning(__('The password must have at least 8 characters.'))
	if (password.value !== password2.value)
		return toast.warning(__('Passwords do not match.'))

	creando.value = true
	try {
		// Aquí solo van el correo y la contraseña. El nombre y el celular se
		// piden en el paso siguiente, ya con la sesión abierta: seis campos justo
		// después de pagar era demasiado para una sola pantalla.
		const r = await call('taar_lms.api.completar_registro', {
			session_id: props.sessionId,
			password: password.value,
			correo: correo.value || undefined,
		})

		// El servidor puede negarse a poner la contraseña aquí si esa cuenta ya
		// existía antes del pago. No es un error: es el candado que impide
		// quedarse con la cuenta de otra pagando con su correo.
		if (r && r.ok === false) {
			estado.value = 'existente'
			enlaceEnviado.value = true
			creando.value = false
			return
		}

		// La sesión ya quedó abierta en el servidor, pero la escuela todavía se
		// cree invitada: hay que releerla antes de seguir, o el paso siguiente
		// pediría el enlace de la comunidad sin saber quién lo pide.
		await refrescarSesion()

		// Su contraseña ya está puesta y su sesión abierta: pase lo que pase con
		// las preguntas o con el enlace del grupo, tiene que poder seguir. Dejarla
		// en la pantalla de la contraseña, con la contraseña ya creada, sería
		// pedirle que la ponga otra vez.
		try {
			await cargarAsistente()
		} catch (e) {
			asistente.value = null
		}
		paso.value = siguienteDe('cuenta')
	} catch (err) {
		avisar(err)
	}
	creando.value = false
}

const refrescarSesion = async () => {
	// El servidor ya dejó la sesión abierta y puso la cookie, pero la escuela
	// sigue creyéndose invitada hasta que la relee. Sin esto, el paso siguiente
	// pediría el enlace de la comunidad sin saber quién lo pide, y el servidor
	// —que solo se lo da a quien ha pagado— no lo entregaría.
	try {
		const cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
		const quien = cookies.get('user_id')
		if (!quien || quien === 'Guest') throw new Error('la sesión no llegó al navegador')

		// Por propiedad y no desestructurando: así se escribe en el ref de dentro
		// del store y todo lo que dependa de él se entera.
		const session = sessionStore()
		session.user = quien

		const { userResource } = usersStore()
		await userResource.reload()
	} catch (e) {
		// Plan B: recargar. Al arrancar de nuevo, el servidor ya la reconoce y el
		// asistente vuelve a abrirse solo, esta vez por el paso de la comunidad,
		// porque el de la contraseña ya está hecho. Se pierde la continuidad de
		// la animación, no el sitio donde estaba.
		window.location.reload()
	}
}

/* ── Preguntas ────────────────────────────────────────────────────────────── */

const yendo = ref(false)

/**
 * Del grupo a las preguntas, asegurándose de tenerlas.
 *
 * Si el asistente se cargó cuando todavía era una invitada, las preguntas no
 * pudieron pedirse: se piden con la sesión abierta. Aquí ya la tiene, así que se
 * intenta otra vez. Y si aun así no llegan, se pasa al final en vez de dejarla
 * mirando una pantalla vacía: preguntarle es importante, pero menos que dejarla
 * entrar a lo que ha pagado.
 */
const irAPreguntas = async () => {
	const siguiente = siguienteDe('comunidad')
	if (siguiente !== 'preguntas' || preguntas.value.length) {
		paso.value = siguiente
		return
	}
	yendo.value = true
	try {
		await cargarAsistente()
	} catch (e) {
		/* se decide abajo con lo que haya */
	}
	yendo.value = false
	paso.value = preguntas.value.length ? 'preguntas' : 'listo'
}

/** Guarda sus datos y sigue. Nombre y celular son obligatorios. */
const guardarDatos = async () => {
	if (!nombre.value.trim()) return toast.warning(__('Tell us your name.'))
	if (!celular.value.trim())
		return toast.warning(__('Leave us your mobile number so we can reach you.'))

	guardandoDatos.value = true
	try {
		await call('taar_lms.api.guardar_datos', {
			nombre: nombre.value,
			apellido: apellido.value || undefined,
			celular: celular.value,
			pais: pais.value || undefined,
		})
		// Aquí NO se recarga el estado. El recorrido ya está congelado, así que no
		// hay nada que refrescar, y en cambio `cargarAsistente` cierra el modal
		// cuando el servidor responde que ya no le falta nada: justo lo que acaba
		// de pasar al guardar sus datos. Se le cerraba en la cara y se quedaba sin
		// el grupo de WhatsApp ni la pantalla de cierre.
		paso.value = 'comunidad'
	} catch (err) {
		avisar(err)
	}
	guardandoDatos.value = false
}

const responder = (opcion) => {
	if (!preguntaActual.value) return
	respuestas.value = { ...respuestas.value, [preguntaActual.value.campo]: opcion }
}

const siguientePregunta = async () => {
	const actual = preguntaActual.value
	if (!actual) return
	if (!respuestas.value[actual.campo]) return toast.warning(__('Choose an option to continue.'))

	if (indicePregunta.value < preguntas.value.length - 1) {
		indicePregunta.value += 1
		return
	}

	guardando.value = true
	try {
		const r = await call('taar_lms.api.guardar_onboarding', {
			respuestas: respuestas.value,
			celular: celular.value || undefined,
			pais: pais.value || undefined,
		})
		destino.value = r?.destino || '/lms/courses?tab=enrolled'

		// Antes de cerrar hay que apagar la señal en memoria. Si no, la escuela
		// sigue pensando que le falta el asistente y se lo vuelve a poner encima
		// de lo que estuviera mirando.
		try {
			const { userResource } = usersStore()
			if (userResource?.data) userResource.data.taar_onboarding_pendiente = 0
		} catch (e) {
			/* si no se puede, el destino recarga la página igualmente */
		}

		paso.value = 'listo'
	} catch (err) {
		avisar(err)
	}
	guardando.value = false
}

const volver = () => {
	// Dentro de las preguntas, "atrás" es la pregunta anterior antes que la
	// pantalla anterior: es lo que espera quien acaba de contestar mal.
	if (paso.value === 'preguntas' && indicePregunta.value > 0) {
		indicePregunta.value -= 1
		return
	}
	paso.value = anteriorDe(paso.value)
}

/* ── Cierre y auxiliares ──────────────────────────────────────────────────── */

const destino = ref('/lms/courses?tab=enrolled')

const entrar = () => {
	show.value = false
	window.location.href = destino.value
}

const abrioComunidad = () => {
	// Un registro, no un requisito: si falla, ella ya está en el grupo.
	call('taar_lms.api.marcar_paso', { paso: 'comunidad' }).catch(() => {})
}

const enviarEnlace = async () => {
	enviandoEnlace.value = true
	try {
		await call('taar_lms.api.enviar_enlace_acceso', { session_id: props.sessionId })
		enlaceEnviado.value = true
	} catch (err) {
		avisar(err)
	}
	enviandoEnlace.value = false
}

const irALogin = () => {
	window.location.href = `/login?redirect-to=${encodeURIComponent(window.location.pathname)}`
}

const avisar = (err) => {
	const msg = typeof err === 'string' ? err : (err?.messages?.[0] ?? err?.message ?? 'Error')
	toast.error(__(msg))
}
</script>

<style scoped>
.taar-asistente {
	display: flex;
	flex-direction: column;
	gap: 22px;
	padding: 34px 30px 30px;
}

/* Progreso */
.taar-progreso {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8px;
}
.taar-progreso-rotulo {
	font-size: 12.5px;
	font-weight: 600;
	color: var(--ink-gray-5);
}
.taar-segmentos {
	display: flex;
	gap: 6px;
}
.taar-segmentos i {
	display: block;
	width: 32px;
	height: 3px;
	border-radius: 2px;
	background: var(--gray-200);
}
.taar-segmentos i.hecho {
	background: var(--taar-primary, #807fec);
}

.taar-titulo {
	margin: 0;
	text-align: center;
	font-size: 26px;
	font-weight: 600;
	line-height: 1.15;
	text-wrap: balance;
	color: var(--ink-gray-9);
}
.taar-apoyo {
	margin: -12px auto 0;
	max-width: 44ch;
	text-align: center;
	font-size: 14.5px;
	color: var(--ink-gray-6);
}

/* Campos */
.taar-campos {
	display: flex;
	flex-direction: column;
	gap: 13px;
}
.taar-fila {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 12px;
}
.taar-caja-dato {
	border-radius: 10px;
	padding: 11px 13px;
	background: var(--surface-gray-2);
	display: flex;
	flex-direction: column;
	gap: 3px;
}
.taar-caja-et {
	font-size: 12px;
	font-weight: 600;
	color: var(--ink-gray-6);
}
.taar-caja-val {
	display: flex;
	align-items: center;
	gap: 10px;
	flex-wrap: wrap;
	font-weight: 600;
	word-break: break-all;
	color: var(--ink-gray-9);
}
.taar-enlace {
	font-size: 13px;
	text-decoration: underline;
	text-underline-offset: 3px;
	color: var(--ink-gray-6);
}
.taar-pista {
	margin: 0;
	font-size: 12.5px;
	color: var(--ink-gray-6);
}

/* Comunidad */
.taar-comunidad {
	border: 1.5px solid rgba(128, 127, 236, 0.35);
	background: linear-gradient(160deg, rgba(231, 224, 250, 0.7), rgba(255, 250, 117, 0.18));
	border-radius: 15px;
	padding: 20px;
	display: flex;
	flex-direction: column;
	gap: 14px;
	text-align: center;
}
.taar-comunidad-icono {
	font-size: 30px;
	line-height: 1;
}
.taar-ventajas {
	margin: 0;
	padding: 0;
	list-style: none;
	text-align: left;
	display: flex;
	flex-direction: column;
	gap: 7px;
	font-size: 14.5px;
	color: var(--ink-gray-8);
}
.taar-ventajas li {
	display: flex;
	gap: 9px;
	align-items: flex-start;
}
.taar-ventajas li > span:first-child {
	color: var(--taar-primary, #807fec);
	font-weight: 800;
}

/* Preguntas */
.taar-pregunta {
	background: var(--surface-gray-2);
	border-radius: 13px;
	padding: 15px 17px;
	display: flex;
	flex-direction: column;
	gap: 10px;
}
.taar-pregunta-meta {
	display: flex;
	align-items: center;
	gap: 9px;
	flex-wrap: wrap;
}
.taar-cuenta {
	font-size: 10.5px;
	font-weight: 800;
	letter-spacing: 0.11em;
	text-transform: uppercase;
	color: var(--ink-gray-5);
}
.taar-pastilla {
	font-size: 11px;
	font-weight: 700;
	padding: 3px 9px;
	border-radius: 999px;
	background: #fffa75;
	color: #07181f;
}
.taar-enunciado {
	display: flex;
	align-items: flex-start;
	gap: 12px;
}
.taar-indice {
	flex: none;
	width: 30px;
	height: 30px;
	border-radius: 8px;
	background: var(--taar-primary, #807fec);
	color: #fff;
	display: grid;
	place-items: center;
	font-weight: 700;
	font-size: 15px;
}
.taar-enunciado p {
	margin: 3px 0 0;
	font-size: 16.5px;
	font-weight: 500;
	color: var(--ink-gray-9);
}
.taar-privacidad {
	margin: -14px 0 0;
	font-size: 12.5px;
	color: var(--ink-gray-6);
}

.taar-opciones {
	display: flex;
	flex-direction: column;
	gap: 10px;
}
.taar-opcion {
	display: flex;
	align-items: center;
	gap: 13px;
	width: 100%;
	text-align: left;
	font-size: 15.5px;
	padding: 15px 17px;
	border-radius: 12px;
	border: 1.5px solid var(--gray-300);
	background: var(--surface-white);
	color: var(--ink-gray-9);
	transition: border-color 0.15s, background 0.15s;
}
.taar-opcion:hover {
	border-color: rgba(128, 127, 236, 0.6);
}
.taar-marca {
	flex: none;
	width: 26px;
	height: 26px;
	border-radius: 50%;
	display: grid;
	place-items: center;
	font-size: 12.5px;
	font-weight: 700;
	background: var(--surface-gray-3);
	color: var(--ink-gray-6);
}
.taar-opcion[aria-pressed='true'] {
	border-color: var(--taar-primary, #807fec);
	background: rgba(128, 127, 236, 0.1);
}
.taar-opcion[aria-pressed='true'] .taar-marca {
	background: var(--taar-primary, #807fec);
	color: #fff;
}
.taar-opcion[aria-pressed='true'] .taar-marca::after {
	content: '●';
	font-size: 11px;
}

/* Cierre */
.taar-palomita {
	width: 58px;
	height: 58px;
	margin: 0 auto;
	border-radius: 50%;
	display: grid;
	place-items: center;
	background: rgba(31, 169, 122, 0.14);
	color: #1fa97a;
	font-size: 29px;
	font-weight: 700;
}

.taar-aviso {
	border-left: 3px solid var(--taar-primary, #807fec);
	background: rgba(128, 127, 236, 0.09);
	padding: 13px 15px;
	border-radius: 0 10px 10px 0;
	font-size: 14.5px;
	color: var(--ink-gray-8);
}

/* Botones */
.taar-acciones {
	display: flex;
	flex-direction: column;
	gap: 11px;
	align-items: center;
}
.taar-boton {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	width: 100%;
	font-size: 15.5px;
	font-weight: 600;
	padding: 13px 26px;
	border-radius: 58px;
	background: var(--taar-primary, #807fec);
	color: #fff;
	text-decoration: none;
	transition: background 0.15s, opacity 0.15s;
}
.taar-boton:hover {
	background: #6b6ae0;
}
.taar-boton:disabled {
	opacity: 0.65;
}
.taar-boton-wa {
	background: #1fa97a;
}
.taar-boton-wa:hover {
	background: #188c64;
}
.taar-boton-fantasma {
	background: transparent;
	border: 1.5px solid var(--gray-300);
	color: var(--ink-gray-8);
}
.taar-boton-fantasma:hover {
	background: var(--surface-gray-2);
}
.taar-atras {
	font-size: 14px;
	font-weight: 600;
	color: var(--ink-gray-6);
}
.taar-atras:hover {
	color: var(--taar-primary, #807fec);
}

/* En el teléfono el asistente ocupa lo que necesita y los campos van uno debajo
   de otro: dos columnas de 190 px con el teclado abierto no se pueden usar. */
@media (max-width: 640px) {
	.taar-asistente {
		padding: 26px 18px 24px;
		gap: 18px;
	}
	.taar-fila {
		grid-template-columns: 1fr;
	}
	.taar-titulo {
		font-size: 22px;
	}
	.taar-segmentos i {
		width: 24px;
	}
}

@media (prefers-reduced-motion: reduce) {
	.taar-opcion,
	.taar-boton {
		transition: none;
	}
}
</style>
