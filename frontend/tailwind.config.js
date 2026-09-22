import frappeUIPreset from 'frappe-ui/tailwind'

export default {
	presets: [frappeUIPreset],
	content: [
		'./index.html',
		'./src/**/*.{vue,js,ts,jsx,tsx}',
		'./node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
		'../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
		'./node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
		'../node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
	],
	theme: {
		extend: {
			strokeWidth: {
				1.5: '1.5',
			},
			/*
			 * La escala de TanArtistic: siete pasos con nombre, en rem, para que
			 * crezcan con el tamaño de letra del sistema (el de frappe-ui viene en
			 * px). Va en `extend` y no reemplaza la del preset: las pantallas de
			 * upstream siguen con `text-sm`, `text-base`... y se migra pantalla
			 * por pantalla. El estándar completo, con el rol de cada paso, está en
			 * docs/navegacion-y-tipografia.md.
			 *
			 * El peso NO va en el token: competiría con `font-medium` como utility
			 * hermana y ganaría la que el CSS generado ponga después, no la que se
			 * escriba al final del `class`. Sin peso, heredan el 420 del envoltorio
			 * (`text-p-base` en App.vue), igual que los tamaños del preset.
			 *
			 * El espaciado entre letras sigue el del preset en tamaños parecidos,
			 * para que el texto nuevo no se vea de otra familia junto al de siempre.
			 */
			fontSize: {
				display: ['1.625rem', { lineHeight: '2rem', letterSpacing: '0.01em' }], // 26/32
				title: ['1.25rem', { lineHeight: '1.75rem', letterSpacing: '0.005em' }], // 20/28
				heading: ['1rem', { lineHeight: '1.375rem', letterSpacing: '0.02em' }], // 16/22
				body: ['0.875rem', { lineHeight: '1.25rem', letterSpacing: '0.02em' }], // 14/20
				support: ['0.8125rem', { lineHeight: '1.125rem', letterSpacing: '0.02em' }], // 13/18
				label: ['0.75rem', { lineHeight: '1rem', letterSpacing: '0.02em' }], // 12/16
				micro: ['0.6875rem', { lineHeight: '0.875rem', letterSpacing: '0.01em' }], // 11/14
			},
			screens: {
				'2xl': '1600px',
				'3xl': '1920px',
			},
		},
	},
	plugins: [],
}
