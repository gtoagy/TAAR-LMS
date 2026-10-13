// Descarga de los materiales de una lección sin salir de ella.
//
// Un enlace con `download` no basta: los ficheros privados se sirven como
// `inline`, y en un iPhone —sobre todo con la escuela instalada como app— el
// PDF se abre a pantalla completa, sin barra del navegador ni forma de volver.
// Aquí el fichero se baja en segundo plano y se entrega ya como archivo: en
// iOS por la hoja de compartir (Guardar en Archivos, Imprimir…), que es lo
// único que funciona igual en Safari y en la app instalada; en el resto, como
// descarga directa.

export const esIOS = () => {
	const agente = navigator.userAgent || ''
	return (
		/iPad|iPhone|iPod/.test(agente) ||
		// El iPad se presenta como Mac; lo delata la pantalla táctil.
		(navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
	)
}

export const traerArchivo = async (url, nombre) => {
	const respuesta = await fetch(url, { credentials: 'same-origin' })
	if (!respuesta.ok) {
		throw new Error(`No se pudo traer ${url}: ${respuesta.status}`)
	}
	const contenido = await respuesta.blob()
	// Sin un tipo reconocible, iOS no deja compartir el archivo.
	const tipo = /\.pdf$/i.test(nombre)
		? 'application/pdf'
		: contenido.type || 'application/octet-stream'
	return new File([contenido], nombre, { type: tipo })
}

export const sePuedeCompartir = (archivo) =>
	esIOS() &&
	typeof navigator.share === 'function' &&
	typeof navigator.canShare === 'function' &&
	navigator.canShare({ files: [archivo] })

const guardarConEnlace = (archivo) => {
	const direccion = URL.createObjectURL(archivo)
	const enlace = document.createElement('a')
	enlace.href = direccion
	enlace.download = archivo.name
	enlace.style.display = 'none'
	document.body.appendChild(enlace)
	enlace.click()
	enlace.remove()
	// Se suelta con margen: revocarla en el acto corta la descarga en Safari.
	setTimeout(() => URL.revokeObjectURL(direccion), 60000)
}

// Devuelve 'hecho', 'cancelado' (cerró la hoja de compartir sin elegir nada) o
// 'pendiente': Safari solo abre la hoja como respuesta directa a un toque, y si
// la descarga tardó ya no cuenta como tal. El archivo queda listo y hay que
// volver a llamar a esta función desde un toque nuevo.
export const entregarArchivo = async (archivo) => {
	if (!sePuedeCompartir(archivo)) {
		guardarConEnlace(archivo)
		return 'hecho'
	}
	try {
		await navigator.share({ files: [archivo] })
		return 'hecho'
	} catch (error) {
		if (error?.name === 'AbortError') return 'cancelado'
		if (error?.name === 'NotAllowedError') return 'pendiente'
		guardarConEnlace(archivo)
		return 'hecho'
	}
}
