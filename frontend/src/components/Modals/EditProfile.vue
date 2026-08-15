<template>
	<Dialog v-model:open="show" size="3xl">
		<template #body-header>
			<div class="flex items-center justify-between mb-5">
				<div class="text-4xl-semibold leading-6 text-ink-gray-9">
					{{ __('Edit Profile') }}
				</div>
				<div class="flex items-center gap-x-2">
					<Badge v-if="isDirty" theme="orange">
						{{ __('Not Saved') }}
					</Badge>
					<div class="pb-5 float-end">
						<Button variant="solid" @click="saveProfile()">
							{{ __('Save') }}
						</Button>
					</div>
				</div>
			</div>
		</template>
		<template #default>
			<div class="text-base">
				<!-- En el teléfono las dos columnas dejaban cada campo en media
				     pantalla; ahí va todo en una sola tira. -->
				<div class="grid grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-10">
					<div class="space-y-4">
						<div class="space-y-4">
							<FotoDePerfil
								v-model="profile.image"
								:label="__('Profile Image')"
								:required="true"
							/>

							<FormControl
								v-model="profile.first_name"
								:label="__('First Name')"
								:required="true"
							/>
							<FormControl
								v-model="profile.last_name"
								:label="__('Last Name')"
								:required="true"
							/>

							<FormControl
								v-model="profile.instagram"
								:label="__('Instagram')"
							/>
						</div>
					</div>
					<div class="space-y-4">
						<!-- Texto corriente y nada más: aquí se cuenta quién eres en
						     tres líneas, no se maqueta una página. -->
						<FormControl
							v-model="bioTexto"
							type="textarea"
							:label="__('Bio')"
							:rows="10"
							:placeholder="__('Tell us a bit about yourself.')"
						/>
					</div>
				</div>
			</div>
		</template>
	</Dialog>
</template>
<script setup>
import {
	Badge,
	Button,
	createResource,
	Dialog,
	FormControl,
	toast,
} from 'frappe-ui'
import { ref, reactive, watch } from 'vue'
import { sanitizeHTML } from '@/utils'
import { usersStore } from '@/stores/user'
import FotoDePerfil from '@/components/Controls/FotoDePerfil.vue'

const { userResource } = usersStore()

const show = defineModel()
const reloadProfile = defineModel('reloadProfile')
const isDirty = ref(false)
const bioTexto = ref('')

const props = defineProps({
	profile: {
		type: Object,
		required: true,
	},
})

const profile = reactive({
	first_name: '',
	last_name: '',
	image: '',
	instagram: '',
})

// La biografía se guarda en HTML porque el perfil y la ficha del curso la
// pintan tal cual, pero se escribe como un texto normal: línea en blanco para
// separar párrafos y punto.
const bioAHtml = (texto) => {
	const limpio = (texto || '').trim()
	if (!limpio) return ''
	const escapar = (t) =>
		t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
	return limpio
		.split(/\n{2,}/)
		.map((parrafo) => `<p>${escapar(parrafo).replace(/\n/g, '<br>')}</p>`)
		.join('')
}

const htmlABio = (html) => {
	if (!html) return ''
	const caja = document.createElement('div')
	caja.innerHTML = String(html)
		.replace(/<\/(p|div|h[1-6]|li)>/gi, '\n\n')
		.replace(/<br\s*\/?>/gi, '\n')
	return (caja.textContent || '').replace(/\n{3,}/g, '\n\n').trim()
}

const updateProfile = createResource({
	url: 'frappe.client.set_value',
	makeParams(values) {
		return {
			doctype: 'User',
			name: props.profile.data.name,
			fieldname: {
				user_image: profile.image || null,
				bio: sanitizeHTML(bioAHtml(bioTexto.value)),
				...profile,
			},
		}
	},
	onSuccess(data) {
		props.profile.data = data
	},
})

const validateMandatoryFields = () => {
	let missingFields = []
	if (!profile.first_name) missingFields.push(__('First Name'))
	if (!profile.last_name) missingFields.push(__('Last Name'))
	if (!profile.image) missingFields.push(__('Profile Image'))
	if (missingFields.length) {
		toast.error(
			__('Please fill the mandatory fields: {0}').format(
				missingFields.join(', ')
			)
		)
		console.error('Missing mandatory fields:', missingFields)
	}
	return missingFields.length
}

const saveProfile = () => {
	let missingMandatoryFields = validateMandatoryFields()
	if (missingMandatoryFields) return
	updateProfile.submit(
		{},
		{
			onSuccess() {
				show.value = false
				reloadProfile.value.reload()
				// El aviso de "completa tu perfil" del menú lateral mira estos
				// mismos datos: sin releerlos seguiría ahí hasta recargar.
				userResource.reload()
			},
			onError(err) {
				toast.error(err.messages?.[0] || err)
			},
		}
	)
}

watch(
	[profile, bioTexto],
	() => {
		if (!props.profile.data) return
		for (let key of Object.keys(profile)) {
			if (key === 'image') continue
			if (profile[key] !== props.profile.data[key]) {
				isDirty.value = true
				return
			}
		}
		if (profile.image !== props.profile.data.user_image) {
			isDirty.value = true
			return
		}
		if (bioAHtml(bioTexto.value) !== (props.profile.data.bio || '')) {
			isDirty.value = true
			return
		}
		isDirty.value = false
	},
	{ deep: true }
)

watch(
	() => props.profile.data,
	(newVal) => {
		if (newVal) {
			profile.first_name = newVal.first_name
			profile.last_name = newVal.last_name
			profile.instagram = newVal.instagram
			profile.image = newVal.user_image
			bioTexto.value = htmlABio(newVal.bio)
			isDirty.value = false
		}
	}
)
</script>
