import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'

/*
 * Los tamaños de letra, en rem. TanArtistic.
 *
 * El preset de frappe-ui declara toda su escala en px (`text-base` es 14px,
 * `text-p-sm` 13px...), y un px no crece cuando alguien sube el tamaño de letra
 * de su teléfono. En el iPhone es aún peor: el script de index.html escala la
 * raíz con ese ajuste, así que crecerían los márgenes y los botones (que sí van
 * en rem) y el texto de dentro se quedaría igual.
 *
 * Aquí se pasa a rem cada `font-size` en px de toda la hoja, la del preset y la
 * de los componentes de frappe-ui incluidas. Con la raíz a 16px se ven idénticos:
 * 14px = 0.875rem. Solo toca `font-size`: los tamaños de iconos, bordes y cajas
 * se quedan como están.
 *
 * Corre al final (OnceExit), después de que Tailwind haya generado sus clases.
 */
const tamanosDeLetraEnRem = () => ({
	postcssPlugin: 'taar-tamanos-de-letra-en-rem',
	OnceExit(root) {
		root.walkDecls('font-size', (decl) => {
			decl.value = decl.value.replace(
				/(^|[\s(,])(\d*\.?\d+)px\b/g,
				(_, antes, px) => `${antes}${parseFloat(px) / 16}rem`
			)
		})
	},
})
tamanosDeLetraEnRem.postcss = true

export default {
	plugins: [tailwindcss, autoprefixer, tamanosDeLetraEnRem()],
}
