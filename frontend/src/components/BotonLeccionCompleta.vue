<!--
	Marcar una lección a mano, y poder deshacerlo.

	Existe por dos motivos. El primero es la última lección de cada curso: no
	tiene botón de "Siguiente" —ahí pone "Volver al curso"—, así que sin esto la
	única forma de cerrarla era llegar al final del vídeo, y sin cerrarla no hay
	cien por cien ni certificado. El segundo son las alumnas que vienen de la
	plataforma anterior con parte del curso ya visto: la escuela nueva no sabe
	nada de ese avance, y esto les deja ponerlo al día.

	Quien decide sigue siendo el servidor: si la lección lleva un cuestionario o
	una tarea obligatorios, no se cierra por mucho que se pulse aquí, y entonces
	el aviso dice qué falta en vez de dejar el botón mudo.
-->
<template>
	<Tooltip :text="etiqueta">
		<Button :loading="enviando" @click="alternar()">
			<template #prefix>
				<CircleCheck
					v-if="completada"
					class="size-4 stroke-1.5 text-green-700 fill-none"
				/>
				<Circle v-else class="size-4 stroke-1.5 text-ink-gray-5" />
			</template>
			<!--
				En el móvil no hay tooltip que valga —no hay puntero que se pose—,
				así que el botón tiene que decir lo que es por sí mismo. Se acorta
				en vez de callarse: sin texto, el círculo se pierde entre los demás
				botones del encabezado y nadie lo pulsa.
			-->
			<span class="md:hidden">{{ etiquetaCorta }}</span>
			<span class="hidden md:inline">{{ etiqueta }}</span>
		</Button>
	</Tooltip>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button, Tooltip, call, toast } from 'frappe-ui'
import { Circle, CircleCheck } from 'lucide-vue-next'

const props = defineProps({
	lesson: {
		type: String,
		required: true,
	},
	course: {
		type: String,
		required: true,
	},
	completada: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits(['marcada', 'desmarcada'])

const enviando = ref(false)

const etiqueta = computed(() =>
	props.completada ? __('Mark as Incomplete') : __('Mark as Complete')
)

// La del móvil, donde el encabezado ya va lleno. Nombra el estado en vez de la
// acción: junto a la palomita se lee de un vistazo, y "Marcar como pendiente"
// no cabe al lado de Anterior y Siguiente.
const etiquetaCorta = computed(() =>
	props.completada ? __('Lesson completed') : __('Complete lesson')
)

// Lo que falta por hacer, dicho en términos de la alumna. El servidor solo
// devuelve la palabra: 'quiz' o 'assignment'.
const motivo = (razon) => {
	if (razon === 'quiz')
		return __('Answer the quiz in this lesson to complete it.')
	if (razon === 'assignment')
		return __('Submit the assignment in this lesson to complete it.')
	return __('This lesson could not be marked as complete.')
}

const alternar = async () => {
	if (enviando.value) return
	enviando.value = true
	const metodo = props.completada
		? 'lms.lms.doctype.course_lesson.course_lesson.unmark_lesson_complete'
		: 'lms.lms.doctype.course_lesson.course_lesson.mark_lesson_complete'
	try {
		const data = await call(metodo, {
			lesson: props.lesson,
			course: props.course,
		})
		if (props.completada) {
			emit('desmarcada', data)
		} else if (data?.completed) {
			emit('marcada', data)
		} else {
			toast.warning(motivo(data?.blocked_by))
		}
	} catch (err) {
		toast.error(err.messages?.[0] || err)
	} finally {
		enviando.value = false
	}
}
</script>
