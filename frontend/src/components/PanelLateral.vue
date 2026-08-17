<template>
	<Teleport to="body">
		<Transition name="taar-velo">
			<div
				v-if="modelValue"
				class="fixed inset-0 z-40 bg-black/40"
				@click="cerrar"
			/>
		</Transition>
		<Transition name="taar-panel">
			<aside
				v-if="modelValue"
				class="fixed inset-y-0 end-0 z-50 flex w-[88%] max-w-sm flex-col bg-surface-base shadow-2xl"
				role="dialog"
				aria-modal="true"
			>
				<div class="flex items-center justify-end px-2 py-2">
					<Button variant="ghost" :label="__('Close')" @click="cerrar">
						<template #icon>
							<span class="lucide-x size-4 text-ink-gray-7" />
						</template>
					</Button>
				</div>
				<div class="min-h-0 flex-1 overflow-y-auto">
					<slot />
				</div>
			</aside>
		</Transition>
	</Teleport>
</template>

<script setup>
import { Button } from 'frappe-ui'
import { onBeforeUnmount, watch } from 'vue'

const props = defineProps({
	modelValue: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const cerrar = () => emit('update:modelValue', false)

const conEscape = (evento) => {
	if (evento.key === 'Escape') cerrar()
}

// Con el panel abierto, la página de detrás no debe moverse: si se desplaza,
// al cerrar el panel se ha perdido el sitio donde se estaba leyendo.
watch(
	() => props.modelValue,
	(abierto) => {
		document.body.style.overflow = abierto ? 'hidden' : ''
		if (abierto) document.addEventListener('keydown', conEscape)
		else document.removeEventListener('keydown', conEscape)
	}
)

onBeforeUnmount(() => {
	document.body.style.overflow = ''
	document.removeEventListener('keydown', conEscape)
})
</script>

<style scoped>
.taar-panel-enter-active,
.taar-panel-leave-active {
	transition: transform 0.25s ease;
}

.taar-panel-enter-from,
.taar-panel-leave-to {
	transform: translateX(100%);
}

/* En árabe o hebreo el panel entra por el lado contrario. */
:global([dir='rtl']) .taar-panel-enter-from,
:global([dir='rtl']) .taar-panel-leave-to {
	transform: translateX(-100%);
}

.taar-velo-enter-active,
.taar-velo-leave-active {
	transition: opacity 0.25s ease;
}

.taar-velo-enter-from,
.taar-velo-leave-to {
	opacity: 0;
}
</style>
