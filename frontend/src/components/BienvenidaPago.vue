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
						<h2 class="taar-titulo">{{ __('Welcome to TanArtistic') }} 🎨</h2>
						<p class="taar-apoyo">
							{{ __('Create your password to get in!') }}
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
						<h2 class="taar-titulo">{{ __('Complete your details') }} ✍️</h2>
						<p class="taar-apoyo">
							{{ __('This helps us reach you about anything related to your account.') }}
						</p>

						<div class="taar-campos">
							<div class="taar-fila">
								<FormControl v-model="nombre" :label="__('First Name')" />
								<FormControl v-model="apellido" :label="__('Last Name')" />
							</div>
							<!-- El país va DELANTE del celular, como en Stripe, y por la
							     misma razón: de él sale la lada, así que preguntarlo
							     después obligaba a rehacer un número ya escrito.

							     El país se escribe y se elige, no se busca en un
							     desplegable. Antes eran diecinueve —los que sabemos
							     deducir por el prefijo— y quien no estuviera en ellos
							     no tenía dónde ponerse. -->
							<div class="taar-fila">
								<div class="taar-buscador">
									<label class="taar-buscador-et" :for="idPais">
										{{ __('Country') }}
									</label>
									<input
										:id="idPais"
										v-model="paisTexto"
										class="taar-buscador-campo"
										type="text"
										autocomplete="off"
										:placeholder="__('Start typing…')"
										@focus="paisAbierto = true"
										@input="paisAbierto = true"
										@blur="cerrarPais()"
									/>
									<ul v-if="paisAbierto && paisesFiltrados.length" class="taar-buscador-lista">
										<!-- mousedown y no click: el blur del campo llega
										     antes que el click y se cerraría la lista sin
										     haber elegido nada. -->
										<li v-for="p in paisesFiltrados" :key="p">
											<button
												type="button"
												:class="{ elegido: p === pais }"
												@mousedown.prevent="elegirPais(p)"
											>
												{{ p }}
											</button>
										</li>
									</ul>
								</div>

								<!-- La lada no se escribe ni se borra: sale del país y se
								     queda. Cuando era texto dentro del campo, cualquier
								     borrado de más dejaba el número inservible para
								     WhatsApp sin que ella se enterara. -->
								<div class="taar-tel-campo">
									<label class="taar-buscador-et" :for="idTel">
										{{ __('Mobile number') }}
									</label>
									<div class="taar-tel" :class="{ enfocado: telEnfocado }">
										<span v-if="lada" class="taar-tel-lada">{{ lada }}</span>
										<!-- Y si su país no está en nuestra lista de prefijos,
										     la escribe ella. Preferible a bloquearla. -->
										<input
											v-else
											v-model="ladaEscrita"
											class="taar-tel-lada taar-tel-lada-libre"
											type="tel"
											inputmode="tel"
											placeholder="+00"
											@focus="telEnfocado = true"
											@blur="telEnfocado = false"
										/>
										<input
											:id="idTel"
											v-model="celularLocal"
											class="taar-tel-num"
											type="tel"
											inputmode="tel"
											autocomplete="tel-national"
											:placeholder="__('998 123 4567')"
											@focus="telEnfocado = true"
											@blur="telEnfocado = false"
										/>
									</div>
								</div>
							</div>
							<p class="taar-pista">
								{{ __('This is the WhatsApp where we write to you.') }}
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
						<h2 class="taar-titulo">{{ __('Be part of the community') }} 💛</h2>

						<div class="taar-comunidad">
							<div class="taar-comunidad-icono" aria-hidden="true">🎨</div>
							<ul class="taar-ventajas">
								<li>
									<span aria-hidden="true">›</span>
									<span>{{ __('Ask questions') }}</span>
								</li>
								<li>
									<span aria-hidden="true">›</span>
									<span>{{ __('Share your work and your process') }}</span>
								</li>
								<li>
									<span aria-hidden="true">›</span>
									<span>{{ __('Keep up with the news from TanArtistic') }}</span>
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

						<!-- El contador de preguntas y el enunciado, sin nada más.
						     Tenía un número morado repitiendo el "1 de 2" de al lado,
						     una pastilla que decía "Obligatoria" cuando todo lo es, y
						     letras A/B/C en las opciones: tres cosas que pedían
						     atención sin contar nada. -->
						<div class="taar-pregunta">
							<span class="taar-cuenta">
								{{ __('Question {0} of {1}').format(indicePregunta + 1, preguntas.length) }}
							</span>
							<p class="taar-enunciado">{{ preguntaActual?.titulo }}</p>
						</div>

						<div class="taar-opciones">
							<button
								v-for="opcion in preguntaActual?.opciones || []"
								:key="opcion"
								class="taar-opcion"
								:aria-pressed="respuestas[preguntaActual.campo] === opcion"
								@click="responder(opcion)"
							>
								<span class="taar-marca"></span>
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
							{{ __('We hope you love it. Thank you for being here.') }}
						</p>
						<div class="taar-acciones">
							<button class="taar-boton" @click="entrar()">
								{{ __('Start painting') }} 🎨
							</button>
						</div>
					</template>

					<!-- El pie, en todos los pasos menos el último.
					     Va en casi todos porque el momento en que más falta hace un
					     teléfono al que escribir es cuando algo se tuerce a mitad de
					     camino. Pero en la pantalla de cierre sobra: ahí ya no se le
					     pide nada y lo único que se quiere es que pulse y entre. -->
					<p v-if="soporteNumero && paso !== 'listo'" class="taar-pie">
						{{ __('Save our support number in case you need anything:') }}
						<a :href="soporte" target="_blank" rel="noopener">{{ soporteNumero }}</a>
					</p>
				</template>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { call, createResource, Dialog, FormControl, LoadingIndicator, toast } from 'frappe-ui'
import { computed, onUnmounted, ref, watch } from 'vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/user'

const show = defineModel()

const props = defineProps({
	// Con session_id venimos de pagar. Sin él, esta es una alumna de siempre que
	// entra por el inicio de sesión y a la que todavía no le hemos preguntado.
	sessionId: { type: String, default: null },
	tipo: { type: String, default: 'membresia' },
})


const paso = ref('cuenta')
const estado = ref(null)
const datos = ref(null)
const asistente = ref(null)
const cargando = ref(true)

const nombre = ref('')
const apellido = ref('')
const correo = ref('')
/* El celular se guarda partido: la lada por un lado y el número por otro.
 *
 * Junto en un solo campo, cualquier borrado de más se llevaba la lada por
 * delante y el número quedaba inservible para WhatsApp sin que ella lo notara.
 * Así la lada sale del país y no se puede tocar, que es como lo hace Stripe.
 */
const celularLocal = ref('')
const ladaEscrita = ref('')
const telEnfocado = ref(false)
const idTel = `taar-tel-${Math.random().toString(36).slice(2, 8)}`
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

/* El buscador de país.
 *
 * `pais` es lo que se guarda y tiene que ser un país del doctype Country;
 * `paisTexto` es solo lo que ella ve escrito mientras busca. Se separan a
 * propósito: si fueran lo mismo, teclear media palabra guardaría media palabra.
 */
/* El soporte y los prefijos llegan por dos caminos según el paso: en los
 * primeros todavía es invitada y vienen con los datos del pago; después vienen
 * con el estado del asistente. Se mira en los dos sitios para no tener que
 * saber en cuál está. */
const soporte = computed(() => asistente.value?.soporte || datos.value?.soporte || '')
const soporteNumero = computed(
	() => asistente.value?.soporte_numero || datos.value?.soporte_numero || ''
)
const prefijos = computed(() => asistente.value?.prefijos || datos.value?.prefijos || {})

const idPais = `taar-pais-${Math.random().toString(36).slice(2, 8)}`
const paisTexto = ref('')
const paisAbierto = ref(false)

const paisesFiltrados = computed(() => {
	const lista = datos.value?.paises || []
	const busca = paisTexto.value.trim().toLowerCase()
	// Sin nada escrito se ven los de siempre, que ya vienen ordenados del
	// servidor con México primero. No los doscientos de golpe.
	if (!busca || busca === (pais.value || '').toLowerCase()) return lista.slice(0, 8)
	return lista.filter((p) => p.toLowerCase().includes(busca)).slice(0, 8)
})

const elegirPais = (p) => {
	pais.value = p
	paisTexto.value = p
	paisAbierto.value = false
}

const cerrarPais = () => {
	// Con un respiro, para que el mousedown de la lista llegue primero.
	setTimeout(() => {
		paisAbierto.value = false
		// Texto suelto que no es ningún país no vale de nada: se guarda contra el
		// doctype Country. Se vuelve a lo último bueno en vez de dejarla creer
		// que puso algo.
		if (paisTexto.value !== pais.value) paisTexto.value = pais.value || ''
	}, 140)
}

// Si el país llega ya sabido —importado, o de la dirección de Stripe—, el
// campo tiene que enseñarlo escrito.
watch(pais, (v) => {
	if (v && paisTexto.value !== v) paisTexto.value = v
})

/* La lada sale del país elegido, y de ningún otro sitio.
 *
 * Antes se deducía el país del número y el número se prefijaba con el país, los
 * dos a la vez. Funcionaba, pero era adivinar en las dos direcciones. Ahora
 * manda el país y ya está: uno decide, el otro obedece.
 */
const ladaDe = (nombre) =>
	Object.entries(prefijos.value).find(([, p]) => p === nombre)?.[0] || ''

const lada = computed(() => ladaDe(pais.value))

/** El número completo, que es lo único que viaja al servidor. */
const celular = computed(() => {
	const l = (lada.value || ladaEscrita.value || '').replace(/[^\d+]/g, '')
	const n = (celularLocal.value || '').replace(/\D/g, '')
	if (!l || !n) return ''
	return `${l.startsWith('+') ? l : `+${l}`}${n}`
})

/* Al revés solo una vez: al cargar.
 *
 * Lo que llega de Stripe o de la importación viene entero y en formato
 * internacional, así que hay que partirlo para poder enseñarlo en dos casillas.
 * Y el país se toma de esa lada, no de la dirección de facturación: el número
 * es lo que se va a usar para escribirle, y tiene que mandar él.
 */
const ponerCelular = (valor) => {
	const texto = (valor || '').trim()
	if (!texto) return
	const digitos = texto.replace(/[^\d+]/g, '')
	if (!digitos.startsWith('+')) {
		celularLocal.value = digitos
		return
	}
	// De más larga a más corta: +593 antes que +59, o Ecuador nunca aparecería.
	const l = Object.keys(prefijos.value)
		.sort((a, b) => b.length - a.length)
		.find((p) => digitos.startsWith(p))
	if (l) {
		celularLocal.value = digitos.slice(l.length)
		elegirPais(prefijos.value[l])
		return
	}
	// Una lada que no conocemos: se toma "+" y dos dígitos, que es lo que miden
	// casi todas. Las de tres que le importan a esta escuela (+593, +351, +502…)
	// están todas en el mapa, así que aquí solo caen casos raros —y de todos
	// modos la casilla queda escribible para que lo corrija.
	ladaEscrita.value = digitos.slice(0, 3)
	celularLocal.value = digitos.slice(3)
}

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
			ponerCelular(d?.celular)
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
		if (!celularLocal.value) ponerCelular(a.datos.celular)
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

	// Su primera pantalla es la primera que le falte. Se mira contra el recorrido
	// y no contra si trae pago: el identificador del pago vive un día entero en
	// el navegador, así que quien paga, crea su contraseña y deja el asistente a
	// medias vuelve con ese identificador puesto y ya con la sesión abierta. Ahí
	// el paso de la contraseña ya no está en su recorrido, pero seguía siendo el
	// que había por defecto: le salía "Paso 0 de 4" pidiéndole una contraseña que
	// el servidor se niega a cambiar —"esta cuenta ya tiene acceso"—, y como el
	// asistente no se puede cerrar, se quedaba encerrada fuera de lo que ya pagó.
	if (!suRecorrido.value.includes(paso.value)) paso.value = suRecorrido.value[0]
}

watch(
	() => [show.value, props.sessionId],
	() => {
		if (show.value) cargar()
	},
	{ immediate: true }
)

/* Mientras el asistente está abierto, lo de detrás no se mueve.
 *
 * Se podía desplazar el catálogo por debajo del modal, y en el móvil eso hace
 * que el asistente parezca despegado de la pantalla y que el dedo mueva cosas
 * que no debería estar tocando todavía.
 */
watch(
	show,
	(abierto) => {
		document.body.style.overflow = abierto ? 'hidden' : ''
	},
	{ immediate: true }
)

// Y si el componente se va sin cerrarse —al navegar—, se devuelve el scroll.
// Sin esto la escuela entera se queda sin poder desplazarse.
onUnmounted(() => {
	document.body.style.overflow = ''
})

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
	// En el orden en que los ve, que es el orden en que los rellena.
	if (!nombre.value.trim()) return toast.warning(__('Tell us your name.'))
	if (!pais.value)
		return toast.warning(__('Tell us which country you are painting from.'))
	if (!celularLocal.value.trim())
		return toast.warning(__('Leave us your mobile number so we can reach you.'))
	if (!celular.value || celular.value.replace(/\D/g, '').length < 8)
		return toast.warning(__('That mobile number does not look complete.'))

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

<style>
/* ─────────────────────────────────────────────────────────────────────────────
   Este bloque NO es scoped a propósito: hay que llegar al contenedor que pinta
   frappe-ui por fuera del modal, que no lleva nuestro atributo de ámbito.

   Todo cuelga de `:has(.taar-asistente)`, así que solo toca a este modal y
   ningún otro diálogo de la escuela se entera.

   El porqué: frappe-ui monta el diálogo como un overlay `fixed inset-0
   overflow-y-auto`, con dentro un `min-h-screen` y una tarjeta con `my-8`. En
   un iPhone `100vh` NO descuenta la barra del navegador, así que el contenido
   siempre mide más que lo que se ve —y encima 64 px de márgenes—: sobran unos
   150 px de scroll aunque la tarjeta quepa de sobra. De ahí que la carta se
   moviera al arrastrar.

   La cura es centrarla con grid sobre la altura real (`100dvh`) y que, cuando
   de verdad no quepa, lo que se desplace sea el contenido de dentro y no la
   tarjeta entera.
   ───────────────────────────────────────────────────────────────────────────── */
.dialog-overlay:has(.taar-asistente) {
	display: grid;
	place-items: center;
	height: 100dvh;
	padding: 10px;
	overflow: hidden;
	overscroll-behavior: contain;
}
.dialog-overlay:has(.taar-asistente) > div {
	display: flex;
	justify-content: center;
	width: 100%;
	min-height: 0;
	max-height: 100%;
	padding: 0;
}
.dialog-overlay:has(.taar-asistente) .dialog-content {
	margin: 0;
	max-height: 100%;
	display: flex;
	flex-direction: column;
	min-height: 0;
}
</style>

<style scoped>
.taar-asistente {
	display: flex;
	flex-direction: column;
	gap: 18px;
	padding: 28px 26px 26px;
	/* Si el paso no cabe —pantalla corta, teclado abierto— se desplaza esto y no
	   la tarjeta. `contain` impide además que el gesto se contagie a la página
	   de detrás al llegar al final. */
	min-height: 0;
	overflow-y: auto;
	overscroll-behavior: contain;
}

/* Progreso */
.taar-progreso {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8px;
}
.taar-progreso-rotulo {
	font-size: 12px;
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
	font-size: 22px;
	font-weight: 600;
	line-height: 1.18;
	text-wrap: balance;
	color: var(--ink-gray-9);
}
.taar-apoyo {
	margin: -12px auto 0;
	max-width: 46ch;
	text-align: center;
	font-size: 13.5px;
	line-height: 1.5;
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

/* Safari en iPhone hace zoom al enfocar un campo cuya letra mide menos de 16px,
   y deja la página corrida donde no estaba. No es un capricho del navegador: es
   su forma de hacer legible lo que no lo es. La cura es que midan 16 de verdad,
   no prohibir el zoom con `maximum-scale`, que se lo quitaría también a quien
   lo necesita para leer. */
.taar-asistente :is(input, select, textarea) {
	font-size: 16px;
}
/* Ojo al bajar tamaños por aquí: los 16px de arriba son los únicos que no
   pueden bajar. Son el umbral exacto de Safari, no una decisión de diseño. */

/* El celular: la lada y el número en una sola caja, pero en dos casillas.
   La de la lada no se puede escribir —sale del país— y se ve distinta a
   propósito, para que no invite a intentarlo. */
.taar-tel-campo {
	display: flex;
	flex-direction: column;
	gap: 3px;
}
.taar-tel {
	display: flex;
	align-items: stretch;
	border-radius: 8px;
	border: 1px solid var(--gray-400);
	background: var(--surface-gray-2);
	overflow: hidden;
	transition: border-color 0.15s, background 0.15s;
}
.taar-tel.enfocado {
	border-color: var(--taar-primary, #807fec);
	background: var(--surface-elevation-1);
}
.taar-tel-lada {
	display: flex;
	align-items: center;
	padding: 5px 10px;
	font-weight: 600;
	color: var(--ink-gray-6);
	background: var(--surface-gray-3);
	border-right: 1px solid var(--gray-300);
	white-space: nowrap;
	user-select: none;
}
.taar-tel-lada-libre {
	width: 4.4em;
	border: 0;
	border-right: 1px solid var(--gray-300);
	outline: none;
	user-select: auto;
}
.taar-tel-num {
	flex: 1;
	min-width: 0;
	padding: 5px 10px;
	border: 0;
	outline: none;
	background: transparent;
	color: var(--ink-gray-8);
	line-height: 1.5;
}

/* El buscador de país */
.taar-buscador {
	position: relative;
	display: flex;
	flex-direction: column;
	gap: 3px;
}
.taar-buscador-et {
	font-size: 12px;
	color: var(--ink-gray-5);
}
.taar-buscador-campo {
	width: 100%;
	padding: 5px 10px;
	border-radius: 8px;
	border: 1px solid var(--gray-400);
	background: var(--surface-gray-2);
	color: var(--ink-gray-8);
	line-height: 1.5;
}
/* OJO: `--surface-white` NO existe. `bg-surface-white` es una clase de Tailwind,
   pero como variable CSS no está definida en ningún sitio, así que
   `background: var(--surface-white)` es una declaración **inválida** y el fondo
   queda transparente. Se vio en un iPhone: la lista de países dejaba pasar el
   texto y el botón de debajo. Las que sí existen son `--surface-elevation-1`
   (#fff en claro, #1f1f1f en oscuro) y `--surface-elevation-2`, que es la que
   usa el propio diálogo de frappe-ui. */
.taar-buscador-campo:focus {
	outline: none;
	border-color: var(--taar-primary, #807fec);
	background: var(--surface-elevation-1);
}
.taar-buscador-lista {
	position: absolute;
	z-index: 20;
	top: calc(100% + 4px);
	left: 0;
	right: 0;
	margin: 0;
	padding: 4px;
	list-style: none;
	/* Cabe dentro de la tarjeta, que desde el arreglo del scroll es quien
	   recorta. Con más alto, los últimos países se quedaban fuera. */
	max-height: 168px;
	overflow-y: auto;
	overscroll-behavior: contain;
	border-radius: 10px;
	border: 1px solid var(--gray-300);
	background: var(--surface-elevation-2);
	box-shadow: 0 12px 30px rgba(0, 0, 0, 0.13);
}
.taar-buscador-lista button {
	width: 100%;
	text-align: left;
	padding: 8px 10px;
	border-radius: 7px;
	font-size: 15px;
	color: var(--ink-gray-8);
}
.taar-buscador-lista button:hover,
.taar-buscador-lista button.elegido {
	background: var(--surface-gray-2);
}
.taar-buscador-lista button.elegido {
	color: var(--taar-primary, #807fec);
	font-weight: 600;
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
/* El correo ocupa su propia linea y el "¿No es tu correo?" va debajo.
   En la misma fila, un correo normal ya empujaba al enlace y se partía en dos
   renglones dentro de una caja que mide media pantalla en el móvil. */
.taar-caja-val {
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	gap: 5px;
	font-weight: 600;
	overflow-wrap: anywhere;
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
	font-size: 26px;
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
	font-size: 13.5px;
	line-height: 1.45;
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
	padding: 14px 16px;
	display: flex;
	flex-direction: column;
	gap: 7px;
}
.taar-cuenta {
	font-size: 10.5px;
	font-weight: 800;
	letter-spacing: 0.11em;
	text-transform: uppercase;
	color: var(--ink-gray-5);
}
.taar-enunciado {
	margin: 0;
	font-size: 14.5px;
	font-weight: 500;
	line-height: 1.4;
	text-wrap: balance;
	color: var(--ink-gray-9);
}

.taar-opciones {
	display: flex;
	flex-direction: column;
	gap: 10px;
}
.taar-opcion {
	display: flex;
	align-items: center;
	gap: 12px;
	width: 100%;
	text-align: left;
	font-size: 14.5px;
	line-height: 1.4;
	padding: 12px 15px;
	border-radius: 12px;
	border: 1.5px solid var(--gray-300);
	background: var(--surface-elevation-1);
	color: var(--ink-gray-9);
	transition: border-color 0.15s, background 0.15s;
}
.taar-opcion:hover {
	border-color: rgba(128, 127, 236, 0.6);
}
/* Un circulo vacio, como el de toda la vida. Las letras A/B/C de Disco no
   servian para nada aqui: nadie dice "la B", se toca la opcion. */
.taar-marca {
	flex: none;
	width: 21px;
	height: 21px;
	border-radius: 50%;
	display: grid;
	place-items: center;
	border: 1.5px solid var(--gray-400);
	background: var(--surface-elevation-1);
}
.taar-opcion[aria-pressed='true'] {
	border-color: var(--taar-primary, #807fec);
	background: rgba(128, 127, 236, 0.1);
}
.taar-opcion[aria-pressed='true'] .taar-marca {
	border-color: var(--taar-primary, #807fec);
	background: var(--taar-primary, #807fec);
}
.taar-opcion[aria-pressed='true'] .taar-marca::after {
	content: '';
	width: 7px;
	height: 7px;
	border-radius: 50%;
	background: #fff;
}

/* El pie */
.taar-pie {
	margin: 2px 0 0;
	text-align: center;
	font-size: 12px;
	line-height: 1.5;
	color: var(--ink-gray-5);
}
.taar-pie a {
	color: var(--taar-primary, #807fec);
	font-weight: 600;
	white-space: nowrap;
}

/* Cierre */
.taar-palomita {
	width: 50px;
	height: 50px;
	margin: 0 auto;
	border-radius: 50%;
	display: grid;
	place-items: center;
	background: rgba(31, 169, 122, 0.14);
	color: #1fa97a;
	font-size: 25px;
	font-weight: 700;
}

.taar-aviso {
	border-left: 3px solid var(--taar-primary, #807fec);
	background: rgba(128, 127, 236, 0.09);
	padding: 13px 15px;
	border-radius: 0 10px 10px 0;
	font-size: 13.5px;
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
	font-size: 14.5px;
	font-weight: 600;
	padding: 12px 24px;
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
	font-size: 13px;
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
		padding: 22px 16px 20px;
		gap: 15px;
	}
	.taar-fila {
		grid-template-columns: 1fr;
	}
	.taar-titulo {
		font-size: 19px;
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
