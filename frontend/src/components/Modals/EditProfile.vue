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
							<Uploader
								v-model="profile.image"
								:label="__('Profile Image')"
								:required="true"
								shape="circle"
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
						<Link
							:label="__('Language')"
							v-model="profile.language"
							doctype="Language"
						/>
						<div>
							<div class="mb-1.5 text-p-sm-medium text-ink-gray-7">
								{{ __('Bio') }}
							</div>
							<TextEditor
								:fixedMenu="true"
								@change="(val) => (profile.bio = val)"
								:content="profile.bio"
								:rows="15"
								editorClass="prose-sm py-2 px-2 min-h-[160px] sm:min-h-[280px] border-outline-gray-2 hover:border-outline-gray-3 rounded-b-md bg-surface-gray-3"
							/>
						</div>
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
	TextEditor,
	toast,
} from 'frappe-ui'
import { ref, reactive, watch } from 'vue'
import { sanitizeHTML } from '@/utils'
import { usersStore } from '@/stores/user'
import Link from '@/components/Controls/Link.vue'

const { userResource } = usersStore()

const show = defineModel()
const reloadProfile = defineModel('reloadProfile')
const hasLanguageChanged = ref(false)
const isDirty = ref(false)

const props = defineProps({
	profile: {
		type: Object,
		required: true,
	},
})

const profile = reactive({
	first_name: '',
	last_name: '',
	bio: '',
	image: '',
	instagram: '',
})

const updateProfile = createResource({
	url: 'frappe.client.set_value',
	makeParams(values) {
		return {
			doctype: 'User',
			name: props.profile.data.name,
			fieldname: {
				user_image: profile.image || null,
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
	profile.bio = sanitizeHTML(profile.bio)
	updateProfile.submit(
		{},
		{
			onSuccess() {
				show.value = false
				reloadProfile.value.reload()
				// El aviso de "completa tu perfil" del menú lateral mira estos
				// mismos datos: sin releerlos seguiría ahí hasta recargar.
				userResource.reload()
				if (hasLanguageChanged.value) {
					hasLanguageChanged.value = false
					window.location.reload()
				}
			},
			onError(err) {
				toast.error(err.messages?.[0] || err)
			},
		}
	)
}

watch(
	() => profile,
	(newVal) => {
		if (!props.profile.data) return
		let keys = Object.keys(newVal)
		keys.splice(keys.indexOf('image'), 1)
		for (let key of keys) {
			if (newVal[key] !== props.profile.data[key]) {
				isDirty.value = true
				return
			}
		}
		if (profile.image !== props.profile.data.user_image) {
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
			profile.language = newVal.language
			profile.bio = newVal.bio
			profile.instagram = newVal.instagram
			profile.image = newVal.user_image
			isDirty.value = false
		}
	}
)

watch(
	() => profile.language,
	() => {
		if (profile.language !== props.profile.data.language) {
			hasLanguageChanged.value = true
		}
	}
)
</script>
