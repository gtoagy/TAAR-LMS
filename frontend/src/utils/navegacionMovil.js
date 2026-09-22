import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getSidebarLinks } from '@/utils'
import { useSettings } from '@/stores/settings'
import { usersStore } from '@/stores/user'
import { pedirSesiones } from '@/utils/envivo'
import { panelVisible } from '@/stores/notifications'

/**
 * La navegación del móvil, sacada de la lista única de `getSidebarLinks`.
 *
 * Todo es `computed` a propósito. Antes la barra se armaba una sola vez, cuando
 * llegaba la usuaria, y lo que llegaba después no la cambiaba: «En vivo» solo
 * aparecía si las sesiones ya estaban en caché en ese instante. Ahora cualquier
 * dato que llegue tarde (sesiones, programas, flags, los enlaces de ayuda)
 * redibuja la barra solo.
 *
 * Reglas (docs/navegacion-y-tipografia.md):
 * - Como mucho cuatro destinos con `pestana`, más «Más». Nunca una sexta.
 * - Lo que no es pestaña vive en la hoja de «Más», agrupado como en la lista.
 * - Si la ruta actual vive en «Más», se marca «Más»: la barra nunca queda
 *   entera apagada.
 */

/** La clave con la que LMS Settings apaga un destino: «Live sessions» → live_sessions. */
const claveDe = (label) => label.toLowerCase().split(' ').join('_')

/** ¿La ruta actual es una de las de este destino? Mira también las rutas hijas (Perfil). */
export function esDeLaRuta(item, route) {
	if (!item?.activeFor?.length) return false
	return route.matched.some((r) => item.activeFor.includes(r.name))
}

/** @param {import('vue').Ref<boolean>} hojaAbierta si la hoja de «Más» está abierta */
export function useNavegacionMovil(hojaAbierta) {
	const route = useRoute()
	const { userResource } = usersStore()
	const { sidebarSettings, programs } = useSettings()

	if (!sidebarSettings.fetched && !sidebarSettings.loading) sidebarSettings.reload()
	pedirSesiones()
	watch(
		() => userResource.data,
		(usuaria) => {
			if (usuaria && !programs.fetched && !programs.loading) programs.reload()
		},
		{ immediate: true }
	)

	/** Los grupos de la lista, ya filtrados por condición y por LMS Settings. */
	const grupos = computed(() => {
		// Hasta saber qué destinos están apagados no se pinta nada: con la lista
		// sin filtrar salían durante un instante Grupos, Empleos, Estadísticas...
		const flags = sidebarSettings.data
		if (!flags) return []
		const apagados = Object.keys(flags).filter((k) => !parseInt(flags[k]))
		return getSidebarLinks(true)
			.map((grupo) => ({
				...grupo,
				items: grupo.items.filter((i) => !apagados.includes(claveDe(i.label))),
			}))
			.filter((grupo) => grupo.items.length)
	})

	const pestanas = computed(() =>
		grupos.value
			.flatMap((g) => g.items)
			.filter((i) => i.pestana)
			.sort((a, b) => a.pestana - b.pestana)
			.slice(0, 4)
	)

	/** Lo que va detrás de «Más», con sus grupos. */
	const gruposMas = computed(() => {
		const enBarra = new Set(pestanas.value)
		return grupos.value
			.map((g) => ({ ...g, items: g.items.filter((i) => !enBarra.has(i)) }))
			.filter((g) => g.items.length)
	})

	const rutaEnMas = computed(() =>
		gruposMas.value.some((g) => g.items.some((i) => esDeLaRuta(i, route)))
	)

	/**
	 * La columna marcada. Con la hoja de «Más» abierta, o con el panel de
	 * notificaciones (que es un panel y no una página), se marca «Más», que es de
	 * donde salieron. `null` = ninguna: una ruta que no sale en la navegación.
	 */
	const indiceActivo = computed(() => {
		if (hojaAbierta.value || panelVisible.value) return pestanas.value.length
		const i = pestanas.value.findIndex((t) => esDeLaRuta(t, route))
		if (i !== -1) return i
		return rutaEnMas.value ? pestanas.value.length : null
	})

	return { grupos, pestanas, gruposMas, indiceActivo }
}
