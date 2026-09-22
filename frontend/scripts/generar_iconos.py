"""
Iconos y pantallas de arranque de la app instalable de TanArtistic.

Salen del logo, no se dibujan: el pincel y el lápiz en negro sobre el amarillo del
favicon que ya conocen las alumnas (/files/taar-icon-v3.png, #FFFA75). Si cambia
el logo o el color, se vuelve a correr esto y listo.

    python frontend/scripts/generar_iconos.py --logo "G:/My Drive/1. TAAR/Logos/Pincel negro.png" --app ../taar-lms-app

Qué genera, y por qué cada variante va aparte (sus reglas se contradicen):

En este repo, frontend/public/manifest/ (los mismos nombres de siempre, para que
el diff sea solo de binarios):
- apple-icon-180.png: el de «Añadir a inicio» en iPhone. SIN transparencia,
  porque iOS rellena de negro lo transparente, y con aire alrededor: iOS le
  redondea las esquinas por su cuenta.
- manifest-icon-192.maskable.png y manifest-icon-512.maskable.png: los del
  manifest de upstream, por si alguna vez se sirve ese.
- apple-splash-*.jpg: las pantallas de arranque del iPhone y el iPad, blancas
  como el fondo de la app y con el icono al centro. Los tamaños salen de los
  nombres que ya existen, así que no hay lista que mantener.

En taar-lms-app, taar_lms/public/icons/ (con --app), que es de donde los sirve
nuestro manifest:
- icon-192.png e icon-512.png, propósito «any»: el cuadro redondeado del favicon,
  con las esquinas transparentes.
- icon-512-maskable.png: fondo a sangre y el logo dentro del círculo del 80%
  central, porque Android recorta todo lo demás con la forma que quiera.
- badge-96.png: la silueta en blanco sobre transparente, para la barra de estado
  de Android cuando llega un aviso. Android pinta solo el canal alfa.

Necesita Pillow (pip install pillow).
"""

import argparse
import re
from pathlib import Path

from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
MANIFEST = AQUI.parent / 'public' / 'manifest'

BLANCO = (255, 255, 255)


def color_hex(texto):
	texto = texto.lstrip('#')
	if not re.fullmatch(r'[0-9a-fA-F]{6}', texto):
		raise argparse.ArgumentTypeError(f'color no válido: {texto}')
	return tuple(int(texto[i : i + 2], 16) for i in (0, 2, 4))


def cargar_logo(ruta):
	logo = Image.open(ruta).convert('RGBA')
	# Solo lo que tiene tinta: el margen transparente del archivo no cuenta.
	return logo.crop(logo.getchannel('A').getbbox())


def logo_a_alto(logo, alto, color=None):
	"""El logo escalado a `alto` px. Con `color`, repintado de ese color."""
	ancho = round(logo.width * alto / logo.height)
	escalado = logo.resize((ancho, alto), Image.LANCZOS)
	if color is None:
		return escalado
	liso = Image.new('RGBA', escalado.size, color + (255,))
	liso.putalpha(escalado.getchannel('A'))
	return liso


def pegar_centrado(fondo, pieza):
	x = (fondo.width - pieza.width) // 2
	y = (fondo.height - pieza.height) // 2
	fondo.alpha_composite(pieza, (x, y))
	return fondo


def cuadro_redondeado(lado, color, radio):
	"""Cuadro de color con esquinas transparentes, dibujado a 4x para suavizarlas."""
	grande = lado * 4
	mascara = Image.new('L', (grande, grande), 0)
	ImageDraw.Draw(mascara).rounded_rectangle(
		(0, 0, grande - 1, grande - 1), radius=radio * 4, fill=255
	)
	cuadro = Image.new('RGBA', (lado, lado), color + (255,))
	cuadro.putalpha(mascara.resize((lado, lado), Image.LANCZOS))
	return cuadro


def icono_redondeado(logo, lado, amarillo):
	# Las proporciones del favicon: esquinas de un 14% y el trazo al 67% de alto.
	fondo = cuadro_redondeado(lado, amarillo, round(lado * 0.14))
	return pegar_centrado(fondo, logo_a_alto(logo, round(lado * 0.67)))


def icono_a_sangre(logo, lado, amarillo, alto_logo):
	fondo = Image.new('RGBA', (lado, lado), amarillo + (255,))
	return pegar_centrado(fondo, logo_a_alto(logo, round(lado * alto_logo)))


def guardar_png(imagen, ruta, sin_alfa=False):
	ruta.parent.mkdir(parents=True, exist_ok=True)
	if sin_alfa:
		imagen = imagen.convert('RGB')
	imagen.save(ruta, optimize=True)
	print(f'  {ruta}')


def main():
	p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
	p.add_argument('--logo', required=True, help='PNG del logo en negro sobre transparente')
	p.add_argument('--amarillo', type=color_hex, default=color_hex('FFFA75'))
	p.add_argument('--app', help='ruta de taar-lms-app, para los iconos del manifest')
	args = p.parse_args()

	logo = cargar_logo(args.logo)
	amarillo = args.amarillo

	print('frontend/public/manifest/')
	# El logo es alto y angosto: al 64% del lado queda con aire a los lados
	# y arriba, y así sigue viéndose como el favicon cuando iOS lo redondea.
	guardar_png(
		icono_a_sangre(logo, 180, amarillo, 0.64),
		MANIFEST / 'apple-icon-180.png',
		sin_alfa=True,
	)
	for lado in (192, 512):
		guardar_png(
			icono_a_sangre(logo, lado, amarillo, 0.56),
			MANIFEST / f'manifest-icon-{lado}.maskable.png',
		)

	# Las pantallas de arranque: el icono redondeado al centro, del 28% del
	# lado corto, sobre el blanco de la app. Así la transición a la primera
	# pantalla no destella.
	pantallas = sorted(MANIFEST.glob('apple-splash-*-*.jpg'))
	if not pantallas:
		raise SystemExit('No encontré las apple-splash-*.jpg de siempre en ' + str(MANIFEST))
	for ruta in pantallas:
		ancho, alto = map(int, re.findall(r'(\d+)-(\d+)\.jpg$', ruta.name)[0])
		lienzo = Image.new('RGBA', (ancho, alto), BLANCO + (255,))
		lado = round(min(ancho, alto) * 0.28)
		pegar_centrado(lienzo, icono_redondeado(logo, lado, amarillo))
		lienzo.convert('RGB').save(ruta, quality=90, optimize=True, progressive=True)
	print(f'  {len(pantallas)} pantallas de arranque apple-splash-*.jpg')

	if not args.app:
		print('Sin --app: no se tocan los iconos del manifest de taar-lms-app.')
		return

	iconos = Path(args.app).resolve() / 'taar_lms' / 'public' / 'icons'
	print(f'{iconos}/')
	for lado in (192, 512):
		guardar_png(icono_redondeado(logo, lado, amarillo), iconos / f'icon-{lado}.png')
	# El círculo seguro mide el 80% del lado. El logo al 58% de alto cabe
	# entero dentro con margen: su diagonal es un 7% mayor que su alto.
	guardar_png(icono_a_sangre(logo, 512, amarillo, 0.58), iconos / 'icon-512-maskable.png')
	# La insignia: silueta blanca, con 12px de aire para que no toque el borde.
	insignia = Image.new('RGBA', (96, 96), (0, 0, 0, 0))
	pegar_centrado(insignia, logo_a_alto(logo, 72, BLANCO))
	guardar_png(insignia, iconos / 'badge-96.png')


if __name__ == '__main__':
	main()
