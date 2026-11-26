import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock the heavy Plyr dependency — the guard only cares that the constructor
// runs once per element, not what the player does. The settings store is mocked
// too (the seek listener reads it); neither is exercised in this test.
const plyrCtor = vi.hoisted(() =>
	vi.fn(function FakePlyr(this: { on: () => void }) {
		this.on = () => {}
	})
)
vi.mock('plyr', () => ({ default: plyrCtor }))
vi.mock('plyr/dist/plyr.css', () => ({}))
const ajustes = vi.hoisted(() => ({ data: {} as Record<string, unknown> }))
vi.mock('@/stores/settings', () => ({
	useSettings: () => ({ settings: ajustes }),
}))
// En la app, `__` lo pone frappe-ui como global; aquí devuelve el texto tal cual.
vi.stubGlobal('__', (texto: string) => texto)

import { enablePlyr } from '@/utils/plyr'

describe('enablePlyr double-init guard', () => {
	beforeEach(() => {
		plyrCtor.mockClear()
		document.body.innerHTML = ''
	})

	it('initialises Plyr once per .video-player even when enablePlyr runs repeatedly', async () => {
		const el = document.createElement('div')
		el.className = 'video-player'
		el.setAttribute('src', 'dQw4w9WgXcQ')
		document.body.appendChild(el)

		const first = await enablePlyr()
		const second = await enablePlyr()

		// The second pass must reuse the instance, not stack a second player
		// (which is what produced the duplicate controls).
		expect(plyrCtor).toHaveBeenCalledTimes(1)
		expect(first).toHaveLength(1)
		expect(second).toHaveLength(1)
		expect(second[0]).toBe(first[0])
	})

	it('initialises each distinct .video-player exactly once', async () => {
		for (const id of ['aaa', 'bbb']) {
			const el = document.createElement('div')
			el.className = 'video-player'
			el.setAttribute('src', id)
			document.body.appendChild(el)
		}

		await enablePlyr()
		await enablePlyr()

		expect(plyrCtor).toHaveBeenCalledTimes(2)
	})
})

describe('saltar 10 s', () => {
	const crearReproductor = async () => {
		plyrCtor.mockClear()
		document.body.innerHTML = ''
		const el = document.createElement('div')
		el.className = 'video-player'
		document.body.appendChild(el)
		await enablePlyr()
		return plyrCtor.mock.calls[0][1]
	}

	it('pone los botones de retroceder y adelantar junto al play, de 10 s', async () => {
		ajustes.data = {}
		const opciones = await crearReproductor()
		expect(opciones.controls.slice(0, 3)).toEqual(['play', 'rewind', 'fast-forward'])
		expect(opciones.seekTime).toBe(10)
		expect(opciones.listeners.fastForward()).toBe(true)
	})

	it('si la escuela no deja adelantar, no hay botón de adelantar y se frena', async () => {
		ajustes.data = { prevent_skipping_videos: 1 }
		const opciones = await crearReproductor()
		expect(opciones.controls).toContain('rewind')
		expect(opciones.controls).not.toContain('fast-forward')
		expect(opciones.listeners.fastForward()).toBe(false)
		ajustes.data = {}
	})
})
