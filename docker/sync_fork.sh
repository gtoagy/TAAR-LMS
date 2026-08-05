#!/bin/bash
# Copia el código de este repo al bench del contenedor, para poder probar los
# cambios en local sin tener que subirlos antes a GitHub.
#
# El contenedor clona el fork desde GitHub (ver init.sh), así que sin esto el
# LMS local solo refleja lo que ya está publicado y cualquier prueba obliga a
# hacer commit y push antes de poder verla.
#
# Uso, desde Git Bash en la raíz del repo:
#   bash docker/sync_fork.sh            # copia el código y reconstruye
#   bash docker/sync_fork.sh --rapido   # solo copia (sin build ni migrate)
#
# Reconstruir tarda ~1 minuto; con --rapido basta si solo tocaste Python.

set -e

CONTENEDOR="lms-frappe-1"
APP="/home/frappe/frappe-bench/apps/lms"
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTENEDOR}$"; then
    echo "El contenedor ${CONTENEDOR} no está levantado. Arranca con: docker compose -f docker/docker-compose.yml up -d"
    exit 1
fi

echo "Copiando el backend (lms/)..."
docker cp "${RAIZ}/lms" "${CONTENEDOR}:${APP}/"

echo "Copiando el frontend (frontend/src/)..."
docker cp "${RAIZ}/frontend/src" "${CONTENEDOR}:${APP}/frontend/"

# docker cp copia como root y el bench corre como frappe: sin esto, el build
# no puede escribir y falla con "permission denied".
# MSYS_NO_PATHCONV evita que Git Bash convierta /home/frappe/... en una ruta de
# Windows (C:/Program Files/Git/home/...) antes de pasarla al contenedor.
MSYS_NO_PATHCONV=1 docker exec -u 0 "${CONTENEDOR}" \
    chown -R frappe:frappe "${APP}/lms" "${APP}/frontend/src"

if [ "$1" = "--rapido" ]; then
    echo "Copiado. Reinicia el sitio si tocaste hooks o doctypes."
    exit 0
fi

echo "Aplicando cambios de doctypes (migrate)..."
docker exec "${CONTENEDOR}" bash -c "cd /home/frappe/frappe-bench && bench --site lms.localhost migrate" 2>&1 | tail -4

echo "Reconstruyendo el frontend..."
docker exec "${CONTENEDOR}" bash -c \
    'cd /home/frappe/frappe-bench && export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}" && bench build --app lms' 2>&1 | tail -4

docker exec "${CONTENEDOR}" bash -c "cd /home/frappe/frappe-bench && bench --site lms.localhost clear-cache" || true

echo ""
echo "Listo. Recarga el navegador con Ctrl+Shift+R."
