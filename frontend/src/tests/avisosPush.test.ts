import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

// Lo que devuelven frappe-ui y los stores, compartido con cada prueba.
const falso = vi.hoisted(() => ({
	configuracion: { data: null as any, fetch: vi.fn() },
	call: vi.fn(),
	ios: false,
	instalada: false,
}))

vi.mock('frappe-ui', () => ({
	createResource: () => falso.configuracion,
	call: (...args: any[]) => falso.call(...args),
	getCachedResource: () => ({ reload: vi.fn() }),
}))
vi.mock('@/stores/notifications', async () => {
	const { ref } = await import('vue')
	return { notifications: { reload: vi.fn() }, panelVisible: ref(false) }
})
vi.mock('@/stores/session', () => ({ sessionStore: () => ({ isLoggedIn: true }) }))
vi.mock('@/utils/appInstalable', () => ({
	esIOS: () => falso.ios,
	esInstalada: () => falso.instalada,
}))

const LLAVE = new Uint8Array([4, 1, 2, 3, 4, 5])
const LLAVE_B64 = btoa(String.fromCharCode(...LLAVE))
	.replace(/\+/g, '-')
	.replace(/\//g, '_')
	.replace(/=+$/, '')

function suscripcion(llave = LLAVE, endpoint = 'https://fcm.example/1') {
	return {
		endpoint,
		options: { applicationServerKey: llave.buffer },
		unsubscribe: vi.fn(async () => true),
		toJSON: () => ({ endpoint, keys: { p256dh: 'p256dh', auth: 'auth' } }),
	}
}

/** Un navegador con avisos: permiso, service worker y PushManager. */
function navegador({ permiso = 'granted', actual = null as any } = {}) {
	const pushManager = {
		getSubscription: vi.fn(async () => actual),
		// Tarda, como el de verdad: es la ventana en que Wapido registró tres.
		subscribe: vi.fn(
			() => new Promise((resolver) => setTimeout(() => resolver(suscripcion()), 20))
		),
	}
	Object.defineProperty(navigator, 'serviceWorker', {
		configurable: true,
		value: { ready: Promise.resolve({ pushManager }), addEventListener: vi.fn() },
	})
	;(window as any).PushManager = function () {}
	;(window as any).Notification = {
		permission: permiso,
		requestPermission: vi.fn(async () => 'granted'),
	}
	return pushManager
}

async function modulo() {
	vi.resetModules()
	return await import('@/utils/avisosPush')
}

beforeEach(() => {
	falso.configuracion.data = { habilitado: true, clave_publica: LLAVE_B64, silenciado: false }
	falso.configuracion.fetch = vi.fn(async () => falso.configuracion.data)
	falso.call = vi.fn(async () => ({ guardada: true }))
	falso.ios = false
	falso.instalada = false
})

describe('la suscripción', () => {
	it('tres llamadas a la vez registran el aparato UNA sola vez', async () => {
		const pushManager = navegador()
		const { asegurarSuscripcion, estadoPush } = await modulo()

		const estados = await Promise.all([
			asegurarSuscripcion(),
			asegurarSuscripcion(),
			asegurarSuscripcion(),
		])

		expect(estados).toEqual(['activos', 'activos', 'activos'])
		expect(pushManager.subscribe).toHaveBeenCalledTimes(1)
		expect(falso.call).toHaveBeenCalledTimes(1)
		expect(falso.call).toHaveBeenCalledWith(
			'taar_lms.avisos_push.guardar_suscripcion',
			expect.objectContaining({ endpoint: 'https://fcm.example/1', plataforma: 'computadora' })
		)
		expect(estadoPush.value).toBe('activos')
	})

	it('si cambió la llave del servidor, da de baja la vieja y se suscribe de nuevo', async () => {
		const vieja = suscripcion(new Uint8Array([4, 9, 9, 9, 9, 9]), 'https://fcm.example/viejo')
		const pushManager = navegador({ actual: vieja })
		const { asegurarSuscripcion } = await modulo()

		expect(await asegurarSuscripcion()).toBe('activos')
		expect(vieja.unsubscribe).toHaveBeenCalled()
		expect(pushManager.subscribe).toHaveBeenCalledTimes(1)
	})

	it('con la misma llave reutiliza la suscripción y solo la vuelve a guardar', async () => {
		const pushManager = navegador({ actual: suscripcion() })
		const { asegurarSuscripcion } = await modulo()

		expect(await asegurarSuscripcion()).toBe('activos')
		expect(pushManager.subscribe).not.toHaveBeenCalled()
		expect(falso.call).toHaveBeenCalledTimes(1)
	})

	it('con permiso pero sin poder guardar NO se da por activo', async () => {
		navegador()
		falso.call = vi.fn(async () => {
			throw new Error('sin red')
		})
		const { asegurarSuscripcion } = await modulo()

		expect(await asegurarSuscripcion()).toBe('con-permiso')
	})
})

describe('los estados', () => {
	it('iPhone sin instalar: le falta instalar, no «tu teléfono no puede»', async () => {
		delete (window as any).PushManager
		falso.ios = true
		const { refrescarEstadoPush } = await modulo()

		expect(await refrescarEstadoPush()).toBe('falta-instalar')
	})

	it('sin avisos en el servidor no se ofrece nada, ni instalar', async () => {
		delete (window as any).PushManager
		falso.ios = true
		falso.configuracion.data = { habilitado: false, clave_publica: null }
		const { refrescarEstadoPush } = await modulo()

		expect(await refrescarEstadoPush()).toBe('sin-configurar')
	})

	it('permiso negado y sin preguntar se distinguen', async () => {
		navegador({ permiso: 'denied' })
		let m = await modulo()
		expect(await m.refrescarEstadoPush()).toBe('negado')

		navegador({ permiso: 'default' })
		m = await modulo()
		expect(await m.refrescarEstadoPush()).toBe('sin-preguntar')
	})
})

describe('navegarDentro', () => {
	const vacio = { template: '<div />' }
	function enrutador() {
		return createRouter({
			history: createMemoryHistory('/lms'),
			routes: [
				{ path: '/', name: 'Home', component: vacio },
				{ path: '/en-vivo', name: 'EnVivo', component: vacio },
				{
					path: '/courses/:courseName/learn/:chapterNumber-:lessonNumber',
					name: 'Lesson',
					component: vacio,
				},
				{ path: '/batches/:batchName', name: 'BatchDetail', component: vacio },
			],
		})
	}

	it('lleva cada enlace de aviso a su pantalla', async () => {
		const { navegarDentro } = await modulo()
		const router = enrutador()
		const push = vi.spyOn(router, 'push')

		expect(navegarDentro(router, '/lms/en-vivo')).toBe(true)
		expect(push.mock.calls[0][0]).toMatchObject({ name: 'EnVivo' })

		expect(navegarDentro(router, `${location.origin}/lms/courses/mar/learn/1-2`)).toBe(true)
		expect(push.mock.calls[1][0]).toMatchObject({
			name: 'Lesson',
			params: { courseName: 'mar', chapterNumber: '1', lessonNumber: '2' },
		})

		// El comentario en un grupo: antes el `#discussions` rompía el nombre.
		expect(navegarDentro(router, '/lms/batches/grupo-1#discussions')).toBe(true)
		expect(push.mock.calls[2][0]).toMatchObject({
			name: 'BatchDetail',
			params: { batchName: 'grupo-1' },
			hash: '#discussions',
		})
	})

	it('no toca lo que no es una pantalla de la escuela', async () => {
		const { navegarDentro } = await modulo()
		const router = enrutador()

		expect(navegarDentro(router, '')).toBe(false)
		expect(navegarDentro(router, 'https://otro.com/lms/en-vivo')).toBe(false)
		expect(navegarDentro(router, '/app/notification-log')).toBe(false)
		expect(navegarDentro(router, '/lms/no-existe/de/verdad')).toBe(false)
	})
})
