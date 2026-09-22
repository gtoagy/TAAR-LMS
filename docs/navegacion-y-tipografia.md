# Navegación y tipografía: el estándar en TanArtistic

Es el mismo estándar que se armó en Wapido en septiembre de 2026 y ya está
probado en iPhone y Android (`design-system/navegacion-y-tipografia.md` en
`gtoagy/wapido-front`). Aquí está lo que aplica a este fork, con una diferencia
deliberada: **la barra inferior es una píldora flotante**. Lo demás son las mismas
reglas, escritas con los nombres de este código.

Todo lo de móvil depende de `useScreenSize().isMobile` (`utils/composables.js`):
un teléfono aunque esté girado (dedo y lado corto de la pantalla menor a 640 px),
o una ventana de menos de 640 px en el ordenador. Por eso lo que cambia con la
barra superior se decide con `titulo` y no con `sm:`: en un teléfono girado la
ventana mide más de 640 y los prefijos de Tailwind se equivocarían.

---

## 1. La barra inferior: una píldora

```
( Inicio · Cursos · En vivo · Membresía · Más )
```

### Cuatro destinos y «Más». Nunca una sexta

Con más de cinco columnas cada una baja de los 44 px que pide el dedo. Si hace
falta un destino nuevo, entra en la hoja de «Más». Nada de desplazamiento
horizontal: una barra que se arrastra esconde la mitad de la navegación.

El orden: la pantalla casa primero y después por uso real. Membresía va en la
barra por dinero y no por frecuencia: es donde se paga y se renueva.

«En vivo» solo existe si hay sesiones (o para quien modera). Sin ella la píldora
queda en cuatro columnas y todo sigue cuadrando, porque se divide entre las que
haya.

### Una sola lista

Los destinos viven en `getSidebarLinks` (`frontend/src/utils/index.js`) y la
misma lista alimenta el panel lateral del ordenador y la navegación del móvil
(`frontend/src/utils/navegacionMovil.js`). Los campos que usa el móvil:

| Campo | Qué hace |
|---|---|
| `pestana: n` | va en la píldora, en la posición `n` (de la 1 a la 4) |
| `etiquetaCorta` | la etiqueta de la pestaña cuando la larga no cabe («Live») |
| `onlyMobile` | solo en el móvil (Mi perfil, Cerrar sesión, Iniciar sesión) |
| `barraSuperior` | en el móvil vive en la barra superior, no en «Más» |
| `activeFor` | las rutas que marcan ese destino; mira también las rutas hijas |

Lo demás va a la hoja de «Más», agrupado como en la lista. Hoy, para una alumna:
Soporte, Comunidad y Cerrar sesión. Los WhatsApp de soporte y comunidad salen de
`utils/ayuda.js`, que se pide con `pedirEnlacesDeAyuda()`: un recurso que
arranca al importarse sale antes de que `main.js` registre el fetcher de Frappe y
recibe el HTML de la página en vez del JSON.

La barra se arma con `computed`: lo que llega tarde (sesiones, programas, las
banderas de LMS Settings, los enlaces de ayuda) la redibuja sola. Hasta que se
sabe qué destinos apagó LMS Settings no se pinta nada, para que no salgan un
instante los que están apagados.

### Qué se marca

- La pestaña de la ruta actual.
- «Más» si la hoja está abierta o si la ruta actual vive dentro de ella.
- Nada en Mi perfil: ahí se marca el avatar de la barra superior.

### Las medidas de la píldora

Viven en `:root` de `frontend/src/index.css`, porque el área de scroll y los
avisos tienen que librarla con el mismo número:

```css
--nav-h: 3.5rem;                                       /* 56 px de píldora */
--nav-borde: max(0.75rem, env(safe-area-inset-bottom)); /* aire de abajo */
--nav-safe: calc(var(--nav-h) + var(--nav-borde) + 0.75rem);
--topbar-h: 3.25rem;                                   /* 52 px de barra superior */
```

- Flota a 12 px de los lados, con un ancho máximo de 28 rem.
- 56 px de alto menos 6 px de relleno: cada pestaña mide 44.
- El borde va como sombra (`0 0 0 1px`) para no comerse esos 44 px.
- Fondo translúcido con desenfoque; sin soporte, fondo sólido.
- El área de scroll (`#scrollContainer`) lleva `pb-[var(--nav-safe)]` y los
  avisos de vue-sonner suben con `--mobile-offset-bottom`, así que nada queda
  tapado.
- Se esconde cuando Plyr entra en su pantalla completa de respaldo
  (`.taar-barra-movil` en `index.css`).

### Color y contraste

- Pestaña inactiva en `ink-gray-6` (#525252). `ink-gray-5` da 4.2:1 y no llega al
  mínimo para letra de 12 px.
- Pestaña activa: el icono en #605fd8 (`--taar-nav-icono-activo`) y la etiqueta en
  la tinta de la marca. #807fec sobre el selector no llega al 3:1 que pide un
  icono.
- «Membresía» mide 63 px a 12 px: la etiqueta de la pestaña va sin el espaciado
  extra del preset para que quepa en un teléfono de 375 px. Si alguien sube mucho
  la letra, se corta con puntos suspensivos.

---

## 2. El margen del gesto de iOS

`viewport-fit=cover` va en el viewport de `frontend/index.html`. **Sin él,
`env(safe-area-inset-*)` vale 0 en iOS**, sin error ni aviso, y en el simulador
del escritorio se ve bien.

`MobileLayout.vue` libra la muesca con `pt-[env(safe-area-inset-top)]`, la
píldora libra el indicador de inicio con `--nav-borde`, y el panel de avisos, que
en el móvil ocupa la pantalla entera, lleva su propio relleno arriba.

### Capas

| Capa | Qué |
|---|---|
| `z-30` | Barra superior; panel de avisos (fijo, pantalla entera) |
| `z-20` | Píldora y hoja de «Más» |
| `z-10` | Fondo oscuro de la hoja de «Más» |

La píldora queda por encima del fondo de la hoja: tocar otra pestaña con la hoja
abierta navega directo.

---

## 3. El selector se mueve

Se mueve el selector y no el icono, para que el ojo siga de dónde a dónde fue:

```css
transition: transform 0.34s cubic-bezier(0.32, 1.14, 0.44, 1);
```

El selector mide exactamente una columna y se desplaza en múltiplos de su propio
ancho (`translateX(indice * 100%)`): con columnas iguales es un salto exacto sin
medir nada.

`prefers-reduced-motion` está en `index.css`, que es un archivo que se importa, y
deja todas las transiciones y animaciones en nada.

---

## 4. La barra superior

```
[avatar]        Título de la pantalla        [campana]
```

`BarraSuperiorMovil.vue`. Solo en el móvil y solo en las pantallas de
`PANTALLAS_CON_BARRA` (`navegacionMovil.js`): Inicio, Cursos, En vivo, Membresía,
Mi perfil, Opinión y Soporte. Lección, Detalle del curso y las pantallas de
administración conservan su cabecera de upstream, que trae controles que hacen
falta (el índice del curso, guardar, crear).

### El título sale de la ruta

`useTituloMovil()` lo saca de la ruta y de la misma lista de destinos. Las
pantallas no tienen que alimentarlo y nunca queda en blanco mientras cargan. Las
que no salen en la navegación lo toman de `TITULOS_EXTRA`.

### El único `<h1>`

Con la barra puesta, las pantallas no repiten su título. Su `<h1>` lleva
`v-if="!titulo"`, y los encabezados que hacían de título pasan a `<h2>` con
`etiquetaTitulo`. En el ordenador todo sigue como estaba.

### Los lados: su perfil y sus avisos

- **Izquierda, el avatar.** Lleva a Mi perfil; ahí se marca con un aro del color
  de la pestaña activa, porque es el sitio donde está.
- **Derecha, la campana.** Con el contador de avisos sin leer (de 9 en adelante,
  «9+») y abre el panel de avisos. El contador usa el recurso y la clave de caché
  del panel lateral, así que al marcar uno como leído baja solo, y se recarga con
  el socket `publish_lms_notifications`. El botón lleva
  `data-notifications-trigger`: sin él, el clic que abre el panel cuenta como clic
  fuera y lo vuelve a cerrar.
- Las dos columnas miden 44 px aunque estén vacías (sin sesión), para que el
  título quede siempre centrado.

Diferencia con Wapido: allá el avatar abre el menú de la cuenta. Aquí va directo a
Mi perfil y «Cerrar sesión» se queda en «Más».

### Deslizar hacia abajo recarga, solo con la app instalada

En una pestaña, Safari y Chrome ya traen el gesto. Al instalar la app desaparece
junto con la barra del navegador, y una pantalla atorada se queda sin salida.
`DeslizarParaRecargar.vue` envuelve a `#scrollContainer` en `MobileLayout.vue`
y lo repone con cuatro reglas:

- **Solo instalada** (`esInstalada()`). En la pestaña saldrían dos indicadores y
  dos recargas.
- **Recarga la página entera**, como el navegador. Refrescar solo los datos no
  saca a la app de un error ni trae la versión nueva, que son justo los casos en
  que alguien la jala.
- **El indicador flota; el contenido no se mueve.** Un `transform` sobre el
  contenido lo haría el contenedor de todo lo `position: fixed` de adentro.
  Arranca escondido debajo de la barra superior, que lo tapa.
- **Se decide en el primer movimiento del dedo.** Si va hacia arriba o de lado, o
  si empieza dentro de algo con scroll que no está hasta arriba, es scroll normal:
  iOS no deja cancelar un scroll que ya empezó. Aquí el scroll de la escuela vive
  en `#scrollContainer` y no en `window`, y como queda dentro del componente, esa
  misma revisión cubre el «está hasta arriba».

No hay botón de «Recargar» en ningún menú: el gesto basta.

---

## 5. Tipografía

### Siete pasos con nombre

En `theme.extend.fontSize` de `frontend/tailwind.config.js`, en rem:

| Token | px / interlineado | Peso habitual | Para qué |
|---|---|---|---|
| `display` | 26 / 32 | 700 | Cifras clave en pantallas anchas |
| `title` | 20 / 28 | 700 | Cifras clave en el teléfono; título de pantalla sin barra superior |
| `heading` | 16 / 22 | 600 | Barra superior, sección, tarjeta |
| `body` | 14 / 20 | 400 | Cuerpo, filas, campos, botones, y el tamaño de `<body>` |
| `support` | 13 / 18 | 400 | Descripciones y ayudas |
| `label` | 12 / 16 | 500 | Rótulos de grupo, navegación, fechas y horas |
| `micro` | 11 / 14 | 600 | Contadores y etiquetas pequeñas: el piso |

### Cada rol tiene su clase

| Rol | Clase |
|---|---|
| Título de la pantalla | la barra superior, el único `<h1>` |
| Título de pantalla sin barra (ordenador) | `text-title font-semibold` |
| Título de sección | `<h2 class="text-heading font-semibold text-ink-gray-9">` |
| Título de tarjeta propia | `text-heading font-semibold` |
| Título de diálogo de frappe-ui | el del componente, sin tocar |
| Subtítulo dentro de una tarjeta | `text-body font-semibold` |
| Nombre de un elemento en una lista | `text-body font-medium` |
| Texto, valores, campos, botones | `text-body`, o sin clase (lo hereda) |
| Descripción o ayuda | `text-support text-ink-gray-6` |
| Rótulo de grupo o de columna | `text-label font-medium text-ink-gray-6` |
| Fecha, hora, contador | `text-label` (o `text-micro`) con `tabular-nums` |
| Cifra clave (el precio de un plan) | `text-title md:text-display font-bold tabular-nums` |
| Cifra suelta destacada | `text-heading font-semibold tabular-nums` |
| Estado vacío | título `text-heading font-semibold`, texto `text-support` |

**Nada dentro de la pantalla usa `title` como encabezado mientras está la barra
superior:** le ganaría al título de la pantalla, que es `heading`. La jerarquía la
dan el peso, el color y el espacio, no solo el tamaño.

**Texto en `ink-gray-6` o más oscuro.** `ink-gray-5` da 4.2:1 sobre blanco y no
llega al 4.5 que pide la letra de 12 a 14 px. Sirve para iconos, no para texto.

### `<body>` declara su tamaño

`body { @apply text-body; }` en `index.css`. Sin esto, todo texto sin clase
hereda los 16 px del navegador y sale más grande que los títulos. Ningún `grep`
lo encuentra, porque el problema es la ausencia de clase.

### Los tamaños del preset de frappe-ui, en rem

El preset reemplaza la escala de Tailwind con la suya, en px (`text-sm` son 13,
`text-base` 14...), y sus componentes la usan por dentro. Un tamaño en px no
crece cuando alguien sube la letra del sistema. En vez de tocar cada componente,
`postcss.config.js` pasa a rem todo `font-size` en px del CSS compilado, al final
de la cadena. Los mismos números con 16 px de raíz; crecen con la raíz.

### iPhone: el tamaño del sistema y el zoom de los campos

Un script en línea en el `<head>` de `frontend/index.html`, el mismo de Wapido:

- **iOS no aplica «Tamaño del texto» al contenido web.** El script mide la fuente
  `-apple-system-body` (17 px por omisión) y escala la raíz en proporción. Con el
  ajuste por omisión queda al 100%, y vuelve a medir al regresar a la app. En la
  Mac no se aplica: ahí esa fuente mide 13 px y encogería todo.
- **`maximum-scale=1` solo en iOS**, para que enfocar un campo de 14 px no agrande
  la página. En iOS no quita el pellizco para ampliar; en Android sí lo quitaría,
  y Android no hace ese zoom.
- El archivo pasa por Jinja al servirse (`lms/www/_lms.html`): el script no puede
  llevar llaves dobles, ni llave con porcentaje o almohadilla. Después de cada
  build hay que comprobar que llega al HTML de `/lms`.

### Nunca un tamaño en píxeles

`text-[11px]` y compañía no crecen con la letra del sistema. Si hace falta un
tamaño que no está en la escala, se discute el token; no se parcha el componente.
Tampoco se fija `html { font-size }` en px: rompería el script de iOS y el ajuste
de Android.

### El peso no va en el token

Si el token trajera `font-weight`, competiría con `font-medium` y ganaría el que
el CSS generado ponga después, no el que se escriba al final. El peso va aparte.

### Cifras con `tabular-nums`

Contadores, fechas, precios y porcentajes: sin esto los dígitos tienen anchos
distintos y el texto de alrededor salta cuando cambian.

### Migrar sin romper

Los tokens van en `extend.fontSize`, así la escala del preset sigue existiendo y
las pantallas de upstream compilan igual. **Renombrar clases no es migrar**:
`text-sm` por `text-support` deja todo igual de desordenado. La migración es
pantalla por pantalla, decidiendo el rol de cada elemento. Hoy están migradas las
pantallas de TanArtistic (Inicio, Cursos y su tarjeta, En vivo, Membresía,
Soporte, Opinión y el estado vacío); las de upstream se van migrando cuando se
tocan.

---

## Checklist

- [ ] `viewport-fit=cover` en el viewport
- [ ] `--nav-h`, `--nav-borde`, `--nav-safe` y `--topbar-h` en `:root`
- [ ] Los 7 tokens en `extend.fontSize`, en rem
- [ ] `body` con `text-body`
- [ ] Los tamaños del preset pasados a rem en `postcss.config.js`: en el CSS
      compilado no queda ningún `font-size` en px
- [ ] El mapa de roles aplicado pantalla por pantalla
- [ ] El script de iOS en el `<head>`, y comprobado en el HTML de `/lms`
- [ ] `prefers-reduced-motion` en `index.css`
- [ ] Una sola lista de destinos (`getSidebarLinks`)
- [ ] Cuatro destinos y «Más» en la píldora; nunca una sexta columna
- [ ] Barra superior con el único `<h1>`, el avatar y la campana
- [ ] Deslizar hacia abajo para recargar, solo con la app instalada
- [ ] Cero tamaños en píxeles: `grep -rnE 'text-\[[0-9.]+px\]' frontend/src`
- [ ] Texto en `ink-gray-6` o más oscuro
- [ ] `tabular-nums` en las cifras
