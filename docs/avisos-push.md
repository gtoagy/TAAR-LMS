# Los avisos push

Lo que suena en el teléfono con TanArtistic cerrada. Portado de Wapido
(gtoagy/wapido-front#51 y #52, gtoagy/wapido-back#167): de allá vienen las
decisiones; el servidor aquí es Frappe, no Supabase. Vive repartido en dos repos:

| Pieza | Dónde |
|---|---|
| Qué suena, la cola y el envío | `taar_lms/avisos_push.py` en `taar-lms-app` |
| Los dispositivos | doctype «TAAR Dispositivo Push» en `taar-lms-app` |
| Silenciar y la bitácora | campos en User y en Notification Log (`taar_lms/setup.py`) |
| «Falta una hora» en la campana | `taar_lms/envivo.py`, `_avisar_en_la_campana` |
| Los handlers `push`, `notificationclick` y `pushsubscriptionchange` | `taar_lms/templates/sw.js` en `taar-lms-app` |
| Permiso, suscripción, estados y mensajes del service worker | `frontend/src/utils/avisosPush.js` (este repo) |
| «¿Te aviso una hora antes?» | `frontend/src/components/AvisoUnaHoraAntes.vue` |
| La pantalla de dispositivos | `frontend/src/pages/ProfileAvisos.vue` (Perfil > Notificaciones) |
| Tocar un aviso del panel | `navigateToPage` en `NotificationPanel.vue` |

El service worker es el de la app instalable, en `/sw.js` y con scope `/`
([app-instalable.md](app-instalable.md)): un service worker solo recibe avisos
para las páginas que controla, y el viejo de VitePWA no controlaba ninguna.

---

## 1. Una sola puerta: el Notification Log

    Notification Log ─(after_insert)─> al_crear_aviso ─(cola short)─> enviar_aviso ─> Apple / Google ─> teléfono
                                            │
                                            └─ nunca sube un error: el aviso del panel se guarda igual

- Todo lo que crea un Notification Log para una alumna, y es de un tipo que
  suena, sale también a su teléfono. Lo que el LMS ya avisa suena sin tocar el
  fork, y el panel de la campana sigue siendo la única bandeja.
- El hook solo encola (`enqueue_after_commit`), dentro de un `try/except` con
  `frappe.log_error`. Ese guardado va dentro de otro (la respuesta de una alumna
  en una discusión): un error aquí la dejaría sin publicar. Es el
  `EXCEPTION WHEN OTHERS THEN RETURN NEW` de Wapido.
- «Falta una hora» también crea su Notification Log, solo para las apuntadas, de
  tipo `Alert` sobre «LMS Live Class», con enlace a `/lms/en-vivo`. Frappe no
  manda por correo los `Alert`, así que el correo sigue siendo el nuestro y no
  sale dos veces. No depende de que el correo salga, y no se repite: la ventana
  de la última hora cabe dos veces en el job de cada diez minutos.

### Qué suena y qué no

| Aviso | ¿Suena? | Por qué |
|---|---|---|
| Te mencionan (`Mention`) | Sí | Es para ella |
| Respuesta en la discusión de una lección (`Alert` + `Course Lesson`) | Sí | Es para ella |
| Comentario en un grupo (`Alert` + `LMS Batch` con enlace a `#discussions`) | Sí | Es para ella |
| La maestra comenta su entrega («LMS Assignment Submission») | Sí | Es para ella |
| Falta una hora para la sesión en vivo («LMS Live Class») | Sí | Solo a las apuntadas |
| Calificación de un cuestionario | No, solo panel | Se la da ella misma al terminarlo |
| Curso publicado, grupo publicado | **No, solo panel** | El LMS los manda a TODAS las usuarias activas: serían cientos de teléfonos sonando a la vez |
| Avisos del sistema de Frappe | No | No son para una alumna |

El grupo publicado y el comentario en un grupo son los dos `Alert` sobre
«LMS Batch»: se distinguen solo por el `#discussions` del enlace.

---

## 2. Configuración (en `site_config.json`, nunca en git)

| Clave | Qué es |
|---|---|
| `taar_vapid_private_key` | La llave privada VAPID en base64url. **Se genera UNA sola vez.** Sin ella no hay avisos y la app ni siquiera los ofrece |
| `taar_push_solo_para` | Lista de correos. Si existe, solo esas cuentas ven la opción y reciben avisos: el interruptor para probar en producción con una sola cuenta. Vacía o sin poner, todas |
| `taar_vapid_sub` | Opcional. A quién le escriben Apple o Google si algo va mal. Tiene que ser `mailto:` o `https://`; sin él, la dirección del sitio |

La llave se genera así, en cualquier bench con `taar_lms` (el local sirve), y la
privada se copia al `site_config` del sitio:

    bench --site <sitio> execute taar_lms.avisos_push.generar_llave

La pública no se guarda en ningún lado: `configuracion()` la saca de la privada,
así que las dos no pueden quedar de pares distintos.

🚨 **Si la privada cambia, todas las suscripciones mueren** con un 403 que nadie
relaciona. La app lo detecta en el siguiente arranque (compara la llave de la
suscripción con la del servidor) y se vuelve a suscribir, pero solo en los
teléfonos que se abran.

---

## 3. Los dispositivos

- **El endpoint es único a secas**, no por alumna. El nombre de la fila es su
  huella (sha256). Si un teléfono cambia de cuenta, la fila se mueve a la cuenta
  nueva, en vez de quedar una huérfana recibiendo los avisos de la anterior.
- Métodos (`@frappe.whitelist()`, nunca para Guest, siempre sobre la sesión):
  `configuracion`, `guardar_suscripcion` (upsert), `mis_dispositivos`,
  `renombrar`, `quitar`, `probar` y `silenciar`. Nadie ve ni toca los de otra.
- **Quitar es borrar**, no apagar. Si solo se apagara, el navegador seguiría
  suscrito y la app lo reactivaría al abrirse.
- **Silenciar no borra**: un campo en User (`taar_push_silenciado`). Sin valor,
  suena. Para las vacaciones, o para la maestra el día que no quiere enterarse
  de cada respuesta.
- **Limpieza:** un 404 o 410 de Apple o Google borra la fila (la app se
  desinstaló). Cualquier otro error suma un fallo; a los 5 seguidos se deja de
  intentar, sin borrar, y al volver a abrir la app el contador regresa a 0.
- **La bitácora** es el campo «Aviso en el teléfono» de cada Notification Log que
  debía sonar: `enviado`, `parcial`, `fallido`, `sin dispositivos` o
  `silenciada`. «Silenciada» lo decidió ella; «sin dispositivos» es que no tiene
  la app, y eso se arregla hablando con ella.

### El payload

El formato declarativo de Apple (Declarative Web Push): `web_push: 8030` y un
objeto `notification` con `title`, `body`, `navigate` (absoluta), `tag`, `lang`.

- En iPhone, Safari lo muestra solo, sin despertar al service worker, y el
  sistema garantiza que aparezca: así WebKit no castiga la suscripción por push
  silencioso.
- Chrome y Firefox lo reciben como datos, y `sw.js` lee los mismos campos.
- `tag` por documento (`envivo:<sesión>`, `leccion:<lección>`, `grupo:<grupo>`,
  `entrega:<entrega>`): una respuesta nueva en la misma lección reemplaza a la
  anterior en vez de apilarse, y vuelve a sonar (`renotify`).
- El asunto y el cuerpo vienen en HTML: se limpian y se cortan a 110 y 180
  caracteres. El límite duro del payload cifrado es de unos 4 KB.
- TTL: 12 horas; «falta una hora», 1 hora.

---

## 4. En el navegador

- **Los estados** (`estadoPush`): `activos`, `con-permiso` (dio permiso pero el
  aparato no quedó registrado: **no** se pinta como activo), `negado`,
  `falta-instalar`, `no-soportado`, `sin-configurar` y `sin-preguntar`.
- **En iPhone**, `PushManager` solo existe con la app instalada (iOS 16.4 o
  más). Ese estado es «falta instalar» y abre la guía de instalar; no es «tu
  teléfono no puede».
- **El permiso se pide solo desde un toque**, y lo primero: Safari solo lo
  muestra dentro del gesto, y un viaje al servidor de por medio lo gasta. Por
  eso la configuración se pide antes de pintar el botón.
- **Dónde se pide:** «¿Te aviso una hora antes?», justo después de «Voy a
  asistir». No hay banner de permiso sin contexto. Si algún día lo hay, va en
  `avisosDeArriba.js` DESPUÉS de instalar: en iPhone, sin instalar no llega nada.
- **Una sola suscripción a la vez** (`asegurarSuscripcion`): la promesa en vuelo
  se comparte. En Wapido tres componentes suscribían juntos y registraron tres
  dispositivos en 470 ms. El guardia va en la función, no en los componentes.
- **En cada arranque vuelve a suscribir** si ya hay permiso (el upsert lo hace
  inofensivo), y si cambió la llave del servidor se da de baja y se suscribe de
  nuevo.
- **Con la app abierta**, el service worker le avisa a la página y esta
  refresca el contador de la campana que ya existe. No hay otro.
- **Tocar el aviso** enfoca la ventana abierta y navega por dentro
  (`navegarDentro`); si no hay, abre una. El mismo `navegarDentro` arregla
  `navigateToPage` del panel: la respuesta en una lección abre la lección (antes
  la ficha del curso) y el comentario en un grupo deja de romperse con el
  `#discussions`.
- `pushsubscriptionchange` vuelve a suscribir pero no guarda: el service worker
  no tiene sesión. La app corrige al arrancar.
- `new Notification()` no existe en Chrome de Android ni en iOS: siempre
  `registration.showNotification()`.

---

## 5. Trampas que ya costaron

- **`Vapid02`, no `Vapid01`.** La 01 de `py_vapid` firma con el esquema viejo
  (`WebPush` y `Crypto-Key`); la 02, con el de la RFC 8292 (`vapid t=..., k=...`),
  el único que acepta Apple. `pywebpush` usa tal cual la instancia que recibe. Con
  la 01, los iPhone dejarían de recibir sin ningún error.
- **`aes128gcm` explícito.** Apple rechaza `aesgcm` sin error visible.
- **Un diccionario de claims nuevo en cada envío.** `webpush()` escribe dentro el
  `aud` del servidor del primer dispositivo; reutilizado, el segundo (Apple
  después de Google) iría firmado para el servidor equivocado.
- **`pywebpush` trae `ttl=0`**: «ahora o nunca». Un teléfono dormido no recibiría
  nada. Va explícito.
- **El `sub` tiene que ser `mailto:` o `https://`.** En local el sitio va por
  http y la librería lo rechaza; se usa `https://<host>`.
- **Un error de configuración no es culpa del teléfono**: si la firma no se puede
  armar, se anota una vez y no se le suma un fallo a cada dispositivo.
- **`push` SIEMPRE muestra la notificación.** Chrome castiga el push silencioso
  con su propio aviso de «este sitio se actualizó en segundo plano».
- **`renotify` exige `tag`**: sin él, Chrome lanza un error y no muestra nada.
- **`navigator.serviceWorker.ready` no termina nunca** si no hay service worker:
  va con tope de 10 segundos.
- **El push se prueba con la app cerrada y la pantalla bloqueada.** Es el
  escenario que importa.

---

## 6. Probar

- **En local** (`lms.localhost`, que cuenta como contexto seguro): una llave
  VAPID solo local en su `site_config`, y `taar_push_solo_para` con la usuaria de
  prueba. Nunca a alumnas reales, y nunca con un tipo que avise a todas.
- **El emisor sin navegador:** un servidor HTTP local que haga de Apple o Google
  y un par de llaves de «teléfono» falso. Se descifra lo que llega con `http_ece`
  y se comprueba el esquema `vapid`, el `aud` de cada servidor, el TTL, que un
  410 borra la fila y que un 500 suma un fallo. Así se encontraron las trampas
  de `Vapid01` y del `sub`.
- **El handler del service worker:** DevTools > Application > Service workers >
  Push, con un JSON como el payload de arriba.
- `vitest`: `src/tests/avisosPush.test.ts` (el guardia de la promesa en vuelo, el
  cambio de llave, los estados y `navegarDentro`).

---

## 7. Adopción: quién los recibe de verdad

El número que importa no es cuántas los tienen «activados», sino cuántas tienen
al menos un dispositivo. En Wapido todo funcionaba y el cliente con más pedidos
tenía cero: sin instalar, en iPhone no llega nada. Desde el escritorio, como
System Manager, `taar_lms.avisos_push.adopcion` lo resume. En SQL:

```sql
-- Alumnas con al menos un dispositivo, por plataforma
select plataforma, count(*) as dispositivos, count(distinct alumna) as alumnas
from `tabTAAR Dispositivo Push`
group by plataforma;

-- Qué pasó con los avisos que debían sonar, últimos 30 días
select taar_push_estado as estado, count(*) as avisos, count(distinct for_user) as alumnas
from `tabNotification Log`
where creation > now() - interval 30 day and ifnull(taar_push_estado, '') != ''
group by taar_push_estado;

-- A quién invitar a instalar: se apuntaron a una sesión y no tienen dispositivo
select distinct i.alumna
from `tabTAAR Inscripcion Sesion` i
left join `tabTAAR Dispositivo Push` d on d.alumna = i.alumna
where d.name is null and i.creation > now() - interval 60 day;
```

---

## Después del deploy

1. `curl -s https://cursos.tanartistic.com/sw.js | head -3`: la `@version` nueva.
2. Poner en el `site_config` de producción `taar_vapid_private_key` (generada una
   vez) y `taar_push_solo_para` con **una sola cuenta**, la de la dueña.
3. Con esa cuenta: Perfil > Notificaciones > «Activarlos aquí», y «Enviar un
   aviso de prueba» con la app cerrada y la pantalla bloqueada, en iPhone
   (instalada) y en Android.
4. Tocar el aviso: abre la escuela. Probar también «Voy a asistir» en una sesión
   de prueba y el «falta una hora».
5. Silenciar, mandar la prueba (tiene que llegar: la prueba ignora el silencio a
   propósito), crear un aviso real y ver en su Notification Log «silenciada».
6. Quitar un dispositivo desde la lista.
7. Cuando todo esté bien, quitar `taar_push_solo_para` para abrirlo a todas.
