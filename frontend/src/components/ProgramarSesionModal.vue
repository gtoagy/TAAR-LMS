<!--
	Programar una sesión en vivo de la escuela.

	Es hermano del `LiveClassModal` de fábrica y se le parece a propósito: los
	mismos campos y la misma forma, para que no haya dos maneras distintas de
	pedir lo mismo. Lo único que cambia es a dónde llama. Aquel crea la clase
	dentro de un grupo, y aquí no hay grupos: estas sesiones son de la escuela
	entera, así que van por `taar_lms.envivo.crear_sesion`, que es quien sabe
	crearlas sin grupo.

	La reunión de Zoom se crea de verdad al guardar — el enlace no se pega a
	mano—, y quién puede programar lo decide el servidor, no este botón.
-->
<template>
	<Dialog
		v-model:open="show"
		:title="__('Schedule a live session')"
		size="xl"
		:actions="[
			{
				// No es `__('Schedule')`: ese texto ya está traducido como
				// «Calendario» por la pantalla del evaluador, y ahí lo correcto
				// es «Programar». Con un texto propio cada uno lleva el suyo.
				label: __('Schedule session'),
				variant: 'solid',
				loading: crearSesion.loading,
				onClick: ({ close }) => programar(close),
			},
		]"
	>
		<template #default>
			<div class="flex flex-col gap-4">
				<div class="grid gap-4 sm:grid-cols-2">
					<div class="space-y-4">
						<FormControl
							v-model="sesion.titulo"
							type="text"
							:label="__('Title')"
							:required="true"
						/>
						<!-- Los `placeholder` se pasan a mano porque los de fábrica
						     vienen en inglés y no pasan por el traductor. -->
						<FormControl
							v-model="sesion.fecha"
							type="date"
							:label="__('Date')"
							:placeholder="__('Select date')"
							:required="true"
						/>
						<FormControl
							v-model="sesion.minutos"
							type="number"
							:label="__('Duration (in minutes)')"
							:required="true"
						/>
					</div>

					<div class="space-y-4">
						<!-- La etiqueta va a mano: el `TimePicker` al que despacha
						     `FormControl` no dibuja la suya, y sin esto el campo se
						     queda mudo y desalineado de la columna de al lado. -->
						<div class="space-y-1.5">
							<label
								class="block text-p-sm-medium text-ink-gray-7"
								for="horaSesion"
							>
								{{ __('Time') }}
								<span class="text-ink-red-6">*</span>
							</label>
							<FormControl
								id="horaSesion"
								v-model="sesion.hora"
								type="time"
								:placeholder="__('Select time')"
							/>
						</div>

						<div class="space-y-1.5">
							<label
								class="block text-p-sm-medium text-ink-gray-7"
								for="zonaSesion"
							>
								{{ __('Timezone') }}
								<span class="text-ink-red-6">*</span>
							</label>
							<Combobox
								id="zonaSesion"
								:modelValue="sesion.zona"
								:options="opcionesDeZona()"
								@update:modelValue="(opt) => (sesion.zona = opt.value)"
							/>
						</div>

						<FormControl
							v-model="sesion.grabar"
							type="select"
							:options="opcionesDeGrabacion()"
							:label="__('Auto Recording')"
						/>
					</div>
				</div>

				<FormControl
					v-model="sesion.descripcion"
					type="textarea"
					:label="__('Description')"
				/>

				<!-- Se dice aquí y no después: lo que se guarda no es una fecha en
				     una lista, es una reunión que queda creada en Zoom. -->
				<p class="text-sm text-ink-gray-5">
					{{
						__(
							'The Zoom meeting is created when you schedule this. Students see the link 15 minutes before it starts.'
						)
					}}
				</p>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import {
	Combobox,
	Dialog,
	FormControl,
	createResource,
	toast,
} from 'frappe-ui'
import { onMounted, reactive } from 'vue'
import { getTimezones } from '@/utils/'
import { refrescarSesiones } from '@/utils/envivo'

const show = defineModel()

const sesion = reactive({
	titulo: '',
	fecha: '',
	hora: '',
	minutos: 90,
	zona: '',
	grabar: 'No Recording',
	descripcion: '',
})

// La zona en la que está quien programa. No se usa `getUserTimezone()` porque
// esa devuelve `null` en cuanto la zona real no sale en la lista de fábrica —y
// `America/Cancun`, que es donde vive la escuela, no sale—, y entonces el campo
// aparece vacío y marcado como obligatorio.
function zonaDelNavegador() {
	try {
		return Intl.DateTimeFormat().resolvedOptions().timeZone || ''
	} catch {
		return ''
	}
}

onMounted(() => {
	sesion.zona = zonaDelNavegador()
})

const opcionesDeZona = () => {
	const zonas = getTimezones()
	const mia = zonaDelNavegador()
	// La propia va la primera y, si falta en el catálogo, se añade: la lista de
	// fábrica no pretende ser todas las zonas del mundo.
	if (mia && !zonas.includes(mia)) zonas.unshift(mia)
	return zonas.map((zona) => ({ label: zona, value: zona }))
}

const opcionesDeGrabacion = () => [
	{ label: __('No Recording'), value: 'No Recording' },
	{ label: __('Local'), value: 'Local' },
	{ label: __('Cloud'), value: 'Cloud' },
]

const crearSesion = createResource({
	url: 'taar_lms.envivo.crear_sesion',
})

function programar(close) {
	// Se comprueba antes de llamar porque la llamada crea una reunión en Zoom:
	// que falle la validación a estas alturas ya deja rastro fuera de aquí.
	if (!sesion.titulo || !sesion.fecha || !sesion.hora) {
		toast.error(__('Title, date and time are required.'))
		return
	}

	crearSesion.submit(
		{ ...sesion },
		{
			onSuccess() {
				refrescarSesiones()
				toast.success(__('Session scheduled.'))
				close()
			},
			onError(err) {
				toast.error(
					err.messages?.[0] || err.message || __('The session was not created.')
				)
			},
		}
	)
}
</script>
