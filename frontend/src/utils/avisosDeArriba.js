import { computed, reactive } from 'vue'

/**
 * Los avisos que van arriba del contenido salen de uno en uno.
 *
 * Pedir dos cosas a la vez es la forma más segura de no conseguir ninguna, y dos
 * franjas apiladas le comen al teléfono media pantalla. Cada aviso dice si
 * quiere salir; sale el primero de la lista que quiera, y el siguiente espera a
 * que ese se vaya (lo cierren, lo resuelvan o deje de tocar).
 *
 * El orden:
 * 1. La reseña: tiene fecha y un descuento detrás.
 * 2. Instalar la app. En iPhone, además, sin instalar no llegarán los avisos
 *    con la app cerrada, así que va antes que el permiso de esos avisos.
 */
const ORDEN = ['resena', 'instalar']

const quieren = reactive({})

/**
 * @param {string} nombre uno de ORDEN
 * @param {import('vue').Ref<boolean>} quiere si este aviso quiere salir ahora
 * @returns {import('vue').ComputedRef<boolean>} si le toca salir
 */
export function avisoDeArriba(nombre, quiere) {
	quieren[nombre] = quiere
	return computed(
		() => !!quiere.value && ORDEN.find((n) => quieren[n]) === nombre
	)
}
