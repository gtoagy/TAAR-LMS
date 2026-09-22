import { createResource } from 'frappe-ui'

/**
 * Los dos WhatsApp de la escuela: soporte y comunidad.
 *
 * Un solo recurso para toda la aplicación. Antes lo pedían por separado el panel
 * lateral del ordenador y la barra del móvil, cada uno con su copia de la misma
 * lógica; ahora los dos leen de aquí a través de `getSidebarItems`, igual que el
 * resto de destinos.
 *
 * Quién ve la comunidad lo decide el servidor, que solo manda ese enlace a quien
 * ha pagado. Aquí solo se pinta lo que llegue. El de soporte llega siempre, también
 * a quien no ha iniciado sesión: es el sitio donde se mira cuando algo no funciona.
 *
 * Sin `auto`, y se pide con `pedirEnlacesDeAyuda()`: este archivo se importa antes
 * de que main.js registre `frappeRequest`, y un recurso que arranca al importarse
 * sale con el fetch por defecto, que pide `/lms/taar_lms.api...` y recibe el HTML
 * de la página. Es el mismo arreglo que el de las sesiones en vivo (utils/envivo.js).
 */
export const enlacesDeAyuda = createResource({
	url: 'taar_lms.api.enlaces_de_ayuda',
	cache: 'Enlaces de ayuda TAAR',
})

let pedidos = false

export function pedirEnlacesDeAyuda() {
	if (pedidos) return
	pedidos = true
	enlacesDeAyuda.fetch()
}
