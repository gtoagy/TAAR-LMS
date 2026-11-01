import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'

vi.mock('@/stores/session', () => ({ sessionStore: () => ({ user: null }) }))
vi.mock('@/stores/user', () => ({
	usersStore: () => ({ userResource: { data: null } }),
}))
vi.mock('@/utils', () => ({
	formatEnrollments: () => '',
	formatRating: () => '',
}))
vi.mock('frappe-ui', () => ({
	Tooltip: { template: '<span><slot /></span>' },
}))

import CourseCard from '@/components/CourseCard.vue'

;(globalThis as any).__ = (s: string) => s

const curso = (extra = {}) => ({
	title: 'Teoría del color',
	image: '/files/teoria-del-color.jpg',
	short_introduction: 'Intro',
	...extra,
})

const portada = (w: ReturnType<typeof mount>) =>
	w.find('img').exists() ? w.find('img') : null

describe('CourseCard: la portada', () => {
	it('pinta la foto en un <img> perezoso que aparece al cargar', async () => {
		const w = mount(CourseCard, { props: { course: curso() } })
		const img = portada(w)!
		expect(img.attributes('src')).toBe('/files/teoria-del-color.jpg')
		expect(img.attributes('loading')).toBe('lazy')
		expect(img.classes()).toContain('opacity-0')
		await img.trigger('load')
		expect(portada(w)!.classes()).toContain('opacity-100')
	})

	it('si la descarga falla, reintenta una vez con otra URL', async () => {
		const w = mount(CourseCard, { props: { course: curso() } })
		await portada(w)!.trigger('error')
		const src = portada(w)!.attributes('src')!
		expect(src).toMatch(/^\/files\/teoria-del-color\.jpg\?reintento=\d+$/)
	})

	it('si falla dos veces, queda el degradado y no un hueco blanco', async () => {
		const w = mount(CourseCard, { props: { course: curso() } })
		await portada(w)!.trigger('error')
		await portada(w)!.trigger('error')
		expect(portada(w)).toBeNull()
		const cubierta = w.find('.h-\\[168px\\]')
		expect(cubierta.attributes('style')).toContain('linear-gradient')
		// El título sigue debajo, una sola vez.
		expect(w.text().match(/Teoría del color/g)).toHaveLength(1)
	})

	it('al cambiar de curso vuelve a intentar desde cero', async () => {
		const w = mount(CourseCard, { props: { course: curso() } })
		await portada(w)!.trigger('error')
		await portada(w)!.trigger('error')
		await w.setProps({ course: curso({ image: '/files/mascotas.jpg' }) })
		expect(portada(w)!.attributes('src')).toBe('/files/mascotas.jpg')
	})

	it('sin foto, degradado con el título encima como siempre', () => {
		const w = mount(CourseCard, { props: { course: curso({ image: null }) } })
		expect(portada(w)).toBeNull()
		expect(w.find('.h-\\[168px\\]').text()).toContain('Teoría del color')
	})
})
