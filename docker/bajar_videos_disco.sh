#!/bin/bash
# Descarga de Mux (donde Disco aloja los videos) los que no tenemos en el disco
# duro, para poder subirlos a Vimeo.
#
# Mux tiene desactivada la descarga en MP4, así que se baja el HLS y se
# reempaqueta sin recodificar (-c copy): mismo archivo, sin pérdida de calidad.
#
# Se ejecuta dentro del contenedor, que es donde está ffmpeg:
#   docker exec lms-frappe-1 bash /workspace/bajar_videos_disco.sh

set -e
DESTINO="/workspace/materiales/videos"
mkdir -p "$DESTINO"

# nombre de salida|playback id de Mux. Se puede pasar un fichero con esa misma
# forma como primer argumento (uno por línea), útil para tandas grandes.
VIDEOS=(
  "workshop-pelaje|oSxeUkHOE00TeDwp8200j00NmZ59ZiNCDaZRWEes15VsEQ"
  "nenufares-parte-1|V00TnxtO7cUXrGNumQeTD4JBT5hDguvS76lyQvBVTJgc"
  "nenufares-parte-2|r6lJ00wltZ01XtzZZL4axpaYgX3fLc01MJP00hRSY8QPQvc"
)

if [ -n "$1" ] && [ -f "$1" ]; then
    VIDEOS=()
    while IFS= read -r linea; do
        # La lista se genera desde Windows: sin quitar el \r final, el playback
        # id queda corrupto y la URL del stream da 404.
        linea="${linea%$'\r'}"
        [ -n "$linea" ] && VIDEOS+=("$linea")
    done < "$1"
    echo "${#VIDEOS[@]} videos en la lista $1"
fi

for entrada in "${VIDEOS[@]}"; do
  nombre="${entrada%%|*}"
  pid="${entrada##*|}"
  salida="$DESTINO/$nombre.mp4"

  if [ -s "$salida" ]; then
    echo "$nombre: ya descargado ($(du -h "$salida" | cut -f1)), se omite"
    continue
  fi

  master="https://stream.mux.com/$pid.m3u8"
  # El master lista varias calidades; nos quedamos con la de mayor ancho de
  # banda, que es la de 1080p.
  variante=$(curl -s "$master" | awk '
    /^#EXT-X-STREAM-INF/ {
      match($0, /BANDWIDTH=[0-9]+/);
      bw = substr($0, RSTART+10, RLENGTH-10) + 0;
      getline url;
      if (bw > max) { max = bw; mejor = url }
    }
    END { print mejor }')

  if [ -z "$variante" ]; then
    echo "$nombre: no pude leer las calidades del stream"
    continue
  fi
  case "$variante" in
    http*) url="$variante" ;;
    *)     url="https://stream.mux.com/$variante" ;;
  esac

  echo "$nombre: descargando..."
  ffmpeg -loglevel error -stats -i "$url" -c copy -bsf:a aac_adtstoasc "$salida"
  echo "$nombre: listo ($(du -h "$salida" | cut -f1))"
done

echo ""
ls -lh "$DESTINO"
