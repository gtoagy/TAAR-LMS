# La app instalable

Lo que hace falta para que TanArtistic se instale en el teléfono como una app más,
portado de Wapido (gtoagy/wapido-front#51 y #53). Vive repartido en dos repos, y
el fork se toca lo mínimo:

| Pieza | Dónde |
|---|---|
| Iconos de iPhone y pantallas de arranque | `frontend/public/manifest/` (este repo) |
| Script que genera todos los iconos | `frontend/scripts/generar_iconos.py` (este repo) |
| Registro del service worker, aviso de versión nueva | `frontend/src/utils/appInstalable.js` |
| Invitación a instalar | `frontend/src/components/InvitacionInstalar.vue` |
| Deslizar para recargar | `frontend/src/components/Layouts/DeslizarParaRecargar.vue` |
| Manifest | `taar_lms/app_instalable.py` en `taar-lms-app` |
| Service worker, en `/sw.js` | `taar_lms/templates/sw.js` en `taar-lms-app` |
| Iconos del manifest | `taar_lms/public/icons/` en `taar-lms-app` |

---

## 1. El service worker: lo que había y lo que se decidió

### Lo que había (medido el 22-sep-2026)

- VitePWA generaba `/assets/lms/frontend/sw.js` y lo registraba con un
  `registerSW.js` inyectado en el HTML, con scope `/assets/lms/frontend/`.
- **Con ese scope no controlaba ninguna página**: un service worker solo manda en
  las direcciones que cuelgan de su carpeta, y la escuela vive en `/lms/*`. Lo único
  que hacía era precachear el build, que tampoco se usaba para nada.
- Publicar con una alumna a media lección no recargaba nada. El riesgo real era
  otro: el código viejo, ya cargado, pide un chunk del build anterior al abrir una
  pantalla que todavía no había visitado. El servidor ya no lo tiene y la
  navegación falla con «Failed to fetch dynamically imported module».

Cabeceras en producción, pedidas con `GET` (`curl -s -D - -o /dev/null <url>`):

| Dirección | Respuesta | `Cache-Control` |
|---|---|---|
| `/assets/lms/frontend/sw.js` | 200, `application/javascript` | `max-age=31536000, immutable` |
| `/assets/lms/frontend/registerSW.js` | 200 | `max-age=31536000, immutable` |
| `/api/method/lms.lms.api.get_pwa_manifest` | 200, `application/manifest+json` | `no-store,no-cache,must-revalidate,max-age=0` |
| `/sw.js` | 404 (la página de «no existe» de Frappe) | `private,max-age=300,stale-while-revalidate=10800` |

**Trampa:** `curl -sI` manda `HEAD`, y los métodos de la API de Frappe le
contestan **403**. Al manifest hay que medirlo con `GET`.

### Lo que se decidió

El service worker de Wapido, **que no cachea nada**, servido en la raíz:

- `taar-lms-app` lo sirve en `/sw.js` con un `page_renderer`. En la raíz porque
  los avisos con la app cerrada necesitan un service worker que controle las
  páginas de la escuela.
- No intercepta ninguna petición: la escuela carga siempre lo publicado y no hay
  precache que se pueda quedar viejo en una app que no tiene botón de recargar.
- Al activarse borra todas las cachés del origen, incluidas las que dejó VitePWA.
- En el fork, VitePWA queda con `disable: true` y el registro lo hace
  `utils/appInstalable.js`, que además da de baja el registro viejo de
  `/assets/lms/frontend/`.
- Se revisa si hay un `sw.js` nuevo al volver al frente y cada 30 minutos.

---

## 2. El manifest

`get_pwa_manifest` de upstream se sobreescribe desde `taar-lms-app` con
`override_whitelisted_methods`, así que la dirección no cambia:

- `id` fijo, `/lms`: es el que ya tenían por omisión las instalaciones de antes
  (el `start_url`), así que siguen siendo la misma app, y un cambio futuro de
  `start_url` no crea una segunda.
- `name` y `short_name` «TanArtistic», descripción en español, `lang: es-MX`.
- `start_url` sale de `get_lms_route()`. `scope: "/"` y no `/lms`: entrar
  (`/login`) y las landings viven fuera de `/lms`, y con un scope más corto se
  abrirían en una pestaña del navegador metida dentro de la app.
- `display: standalone`, y `theme_color` y `background_color` en blanco, el fondo
  de la app.
- Tres iconos: `icon-192.png` e `icon-512.png` con propósito `any`, e
  `icon-512-maskable.png` con propósito `maskable`.
- Atajos para Android: Mis cursos y Sesiones en vivo.

Los iconos salen de `/assets/taar_lms/icons/`, que Frappe Cloud sirve con caché de
un año. Si se regeneran, hay que subir `VERSION_ICONOS` en `app_instalable.py`
para que la dirección cambie.

---

## 3. Iconos y pantallas de arranque

Salen del logo con un script, no se dibujan:

    python frontend/scripts/generar_iconos.py --logo "G:/My Drive/1. TAAR/Logos/Pincel negro.png" --app ../taar-lms-app

El pincel y el lápiz en negro sobre el amarillo del favicon que ya conocen las
alumnas (`/files/taar-icon-v3.png`, #FFFA75; se cambia con `--amarillo`). Cada
variante va aparte porque sus reglas se contradicen:

- `apple-icon-180.png`: **sin transparencia** (iOS rellena de negro lo
  transparente) y con aire alrededor, porque iOS le redondea las esquinas.
- Maskable: fondo a sangre y el logo dentro del círculo del 80% central, porque
  Android recorta todo lo demás.
- `any`: el cuadro redondeado del favicon, con las esquinas transparentes.
- `badge-96.png`: la silueta en blanco sobre transparente, para la barra de estado
  de Android cuando llegue un aviso.
- Las 38 pantallas de arranque del iPhone y el iPad conservan sus nombres (el diff
  es solo de binarios): blancas como la app, con el icono al centro.

Safari busca el icono de «Agregar a inicio» primero en el `apple-touch-icon`
declarado (lo está, en `frontend/index.html`) y nunca usa un SVG. El favicon sale
de Website Settings y ya es el de TanArtistic.

---

## 4. La invitación a instalar

`InvitacionInstalar.vue`, en lugar del `InstallPrompt.vue` de upstream (que sigue
en el repo, sin usarse). Va en el flujo, arriba del contenido, como la barra de la
reseña.

- **Android:** Chrome manda `beforeinstallprompt` casi al cargar y una sola vez.
  Se guarda desde `main.js` (si se esperara al componente, ya habría pasado), y el
  botón «Instalar» llama a `prompt()` sobre ese evento original.
- **iPhone y iPad:** no existe ese evento, así que «Ver cómo» abre la guía con los
  pasos. En Safari, Compartir está en la barra de abajo o dentro del botón de tres
  puntos (según la versión); en el iPad, arriba a la derecha; en otros navegadores,
  en su menú.
- La guía avisa **antes** de que habrá que iniciar sesión otra vez: la app
  instalada guarda su sesión aparte de Safari, y quien no lo sabe cree que se
  instaló mal. Recuerda también dónde está «¿Se te olvidó tu contraseña?».
- Solo con sesión iniciada, solo en el móvil, nunca con la app ya instalada, y
  respeta `disable_pwa`.
- La X la calla **una semana**, no para siempre.
- **Uno a la vez** con los demás avisos de arriba (`utils/avisosDeArriba.js`):
  primero la reseña, después instalar. Cuando lleguen los avisos push, su permiso
  va detrás de instalar, porque en iPhone sin instalar no llegan.
- Todavía no promete avisos. Cuando la parte de los avisos push esté publicada, el
  texto cambia: en iPhone, sin instalar no llegan los recordatorios de las sesiones.

---

## 5. El aviso de versión nueva

Una app instalada no tiene botón de recargar, y la pantalla que se queda abierta
corre el código con el que arrancó.

- La versión es el nombre del script principal del build (`index-<hash>.js`): el
  que corre se lee del `<script>` de la página; el publicado, del HTML que sirve
  ahora `/lms`, pedido con `no-store`.
- Se revisa al volver al frente y cada 30 minutos, solo con la pestaña visible.
- **Nunca recarga solo.** Sale «Hay una versión nueva de TanArtistic» con un botón
  de Actualizar. Si lo cierran, no insiste con esa misma versión.
- Con un video en pantalla completa (la del navegador o la de respaldo de Plyr)
  espera, y sale al salir de ella.
- **Chunk perdido:** si la navegación falla porque el chunk ya no existe, la
  pantalla se queda donde estaba (nunca en blanco), sale el mismo aviso, y
  Actualizar la lleva adonde iba.

---

## 6. Deslizar para recargar

Solo con la app instalada; las reglas, en
[navegacion-y-tipografia.md](navegacion-y-tipografia.md#deslizar-hacia-abajo-recarga-solo-con-la-app-instalada).

---

## Después del deploy

1. `curl -s -D - -o /dev/null https://cursos.tanartistic.com/sw.js`: 200,
   `text/javascript` y un `Cache-Control` que no sea de un año. Si sigue en 404,
   es la caché de 404 de Frappe (`website_404`): `bench --site <sitio>
   clear-website-cache`.
2. Lo mismo con `/api/method/lms.lms.api.get_pwa_manifest` (con `GET`):
   `application/manifest+json` y el nombre TanArtistic.
3. En Chrome, DevTools > Application: el manifest sin errores, con los tres
   iconos, y un solo service worker, `/sw.js` con scope `/`, controlando la
   página. El de `/assets/lms/frontend/` ya no debe aparecer después de una visita.
4. En el iPhone: instalar desde la guía, abrir desde el icono (sale la pantalla de
   arranque amarilla sobre blanco), iniciar sesión y deslizar hacia abajo en
   Cursos para ver el indicador.
5. En Android: el banner con «Instalar», la instalación en el acto, y el icono
   recortado sin comerse el logo.
