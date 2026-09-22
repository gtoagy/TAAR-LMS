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
 */
export const enlacesDeAyuda = createResource({
	url: 'taar_lms.api.enlaces_de_ayuda',
	cache: 'Enlaces de ayuda TAAR',
	auto: true,
})
