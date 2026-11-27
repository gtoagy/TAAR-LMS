import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
	activarDobleToque,
	crearContadorDeToques,
	SALTO_SEGUNDOS,
} from '@/utils/dobleToque'

describe('crearContadorDeToques', () => {
	it('un toque suelto no salta', () => {
		const tocar = crearContadorDeToques()
		expect(tocar('atras', 1000)).toBe(0)
	})

	it('dos toques seguidos en el mismo lado saltan 10 s', () => {
		const tocar = crearContadorDeToques()
		tocar('atras', 1000)
		expect(tocar('atras', 1200)).toBe(SALTO_SEGUNDOS)
	})

	it('dos toques muy separados no cuentan como doble', () => {
		const tocar = crearContadorDeToques()
		tocar('adelante', 1000)
		expect(tocar('adelante', 1500)).toBe(0)
	})

	it('un toque en cada lado no salta', () => {
		const tocar = crearContadorDeToques()
		tocar('atras', 1000)
		expect(tocar('adelante', 1100)).toBe(0)
	})

	it('ya en racha, cada toque suma otros 10 s', () => {
		const tocar = crearContadorDeToques()
		tocar('atras', 1000)
		expect(tocar('atras', 1200)).toBe(10)
		// Más lento que un doble toque, pero dentro de la racha.
		expect(tocar('atras', 1800)).toBe(20)
		expect(tocar('atras', 2400)).toBe(30)
		// Se acabó la racha: vuelve a empezar.
		expect(tocar('atras', 4000)).toBe(0)
	})
})

describe('activarDobleToque', () => {
	let player: any
	let handlers: Record<string, () => void>

	beforeEach(() => {
		vi.useFakeTimers()
		document.body.innerHTML = ''
		const container = document.createElement('div')
		const wrapper = document.createElement('div')
		container.appendChild(wrapper)
		document.body.appendChild(container)
		handlers = {}
		player = {
			elements: { container, wrapper },
			rewind: vi.fn(),
			forward: vi.fn(),
			on: (evento: string, fn: () => void) => (handlers[evento] = fn),
		}
	})

	afterEach(() => vi.useRealTimers())

	const dobleToque = (zona: string) => {
		const el = player.elements.wrapper.querySelector(`.taar-toque--${zona}`)
		el.click()
		vi.advanceTimersByTime(100)
		el.click()
		return el
	}

	it('pone una franja a cada lado, una sola vez', () => {
		activarDobleToque(player, { puedeAdelantar: () => true })
		activarDobleToque(player, { puedeAdelantar: () => true })
		expect(player.elements.wrapper.querySelectorAll('.taar-toque')).toHaveLength(2)
	})

	it('las franjas se encienden hasta que el vídeo arrancó', () => {
		activarDobleToque(player, { puedeAdelantar: () => true })
		expect(player.elements.container.classList.contains('taar-toque-listo')).toBe(false)
		handlers.playing()
		expect(player.elements.container.classList.contains('taar-toque-listo')).toBe(true)
	})

	it('doble toque a la izquierda retrocede 10 s y lo dice', () => {
		activarDobleToque(player, { puedeAdelantar: () => true })
		const el = dobleToque('atras')
		expect(player.rewind).toHaveBeenCalledWith(10)
		expect(el.textContent).toBe('« 10 s')
		expect(el.classList.contains('taar-toque--visible')).toBe(true)
		vi.advanceTimersByTime(1000)
		expect(el.classList.contains('taar-toque--visible')).toBe(false)
	})

	it('doble toque a la derecha adelanta 10 s', () => {
		activarDobleToque(player, { puedeAdelantar: () => true })
		dobleToque('adelante')
		expect(player.forward).toHaveBeenCalledWith(10)
	})

	it('si la escuela no deja adelantar, la derecha no hace nada', () => {
		activarDobleToque(player, { puedeAdelantar: () => false })
		const el = dobleToque('adelante')
		expect(player.forward).not.toHaveBeenCalled()
		expect(el.classList.contains('taar-toque--visible')).toBe(false)
	})
})
