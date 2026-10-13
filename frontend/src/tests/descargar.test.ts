import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { entregarArchivo, traerArchivo } from '@/utils/descargar'

const IPHONE =
	'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15'
const ESCRITORIO = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/140'

/** Un navegador de mentira: quién dice ser y si sabe compartir archivos. */
function navegador(agente: string, share?: any) {
	vi.stubGlobal('navigator', {
		userAgent: agente,
		platform: '',
		maxTouchPoints: 0,
		...(share ? { share, canShare: () => true } : {}),
	})
}

const error = (nombre: string) =>
	Object.assign(new Error(nombre), { name: nombre })

const archivo = () =>
	new File(['%PDF'], 'Workbook.pdf', { type: 'application/pdf' })

describe('descarga de materiales', () => {
	let clics: HTMLAnchorElement[]

	beforeEach(() => {
		clics = []
		vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(
			function (this: HTMLAnchorElement) {
				clics.push(this)
			}
		)
		URL.createObjectURL = vi.fn(() => 'blob:workbook')
		URL.revokeObjectURL = vi.fn()
	})

	afterEach(() => {
		vi.unstubAllGlobals()
		vi.restoreAllMocks()
	})

	it('trae el fichero con la sesión y le pone nombre y tipo de PDF', async () => {
		const fetch = vi.fn(async () => ({
			ok: true,
			blob: async () => new Blob(['%PDF'], { type: '' }),
		}))
		vi.stubGlobal('fetch', fetch)

		const traido = await traerArchivo('/private/files/Workbook.pdf', 'Workbook.pdf')

		expect(fetch).toHaveBeenCalledWith('/private/files/Workbook.pdf', {
			credentials: 'same-origin',
		})
		expect(traido.name).toBe('Workbook.pdf')
		expect(traido.type).toBe('application/pdf')
	})

	it('falla si el servidor no entrega el fichero', async () => {
		vi.stubGlobal(
			'fetch',
			vi.fn(async () => ({ ok: false, status: 403 }))
		)

		await expect(traerArchivo('/private/files/x.pdf', 'x.pdf')).rejects.toThrow()
	})

	it('fuera de iOS lo descarga con su nombre, sin navegar al PDF', async () => {
		const share = vi.fn()
		navegador(ESCRITORIO, share)

		expect(await entregarArchivo(archivo())).toBe('hecho')

		expect(share).not.toHaveBeenCalled()
		expect(clics).toHaveLength(1)
		expect(clics[0].download).toBe('Workbook.pdf')
		expect(clics[0].getAttribute('href')).toBe('blob:workbook')
		expect(clics[0].target).toBe('')
	})

	it('en iOS abre la hoja de compartir con el archivo', async () => {
		const share = vi.fn(async () => undefined)
		navegador(IPHONE, share)
		const pdf = archivo()

		expect(await entregarArchivo(pdf)).toBe('hecho')

		expect(share).toHaveBeenCalledWith({ files: [pdf] })
		expect(clics).toHaveLength(0)
	})

	it('cerrar la hoja sin elegir nada no descarga por otro lado', async () => {
		navegador(
			IPHONE,
			vi.fn(async () => {
				throw error('AbortError')
			})
		)

		expect(await entregarArchivo(archivo())).toBe('cancelado')
		expect(clics).toHaveLength(0)
	})

	it('si iOS exige un toque nuevo, lo deja pendiente', async () => {
		navegador(
			IPHONE,
			vi.fn(async () => {
				throw error('NotAllowedError')
			})
		)

		expect(await entregarArchivo(archivo())).toBe('pendiente')
		expect(clics).toHaveLength(0)
	})

	it('en iOS sin hoja de compartir cae a la descarga directa', async () => {
		navegador(IPHONE)

		expect(await entregarArchivo(archivo())).toBe('hecho')
		expect(clics).toHaveLength(1)
	})
})
