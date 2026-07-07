#!/usr/bin/env bash
#
# Despliega TuFinca en Azure App Service (URL pública).
# Requiere: az login previo y la webapp ya creada (ver AVANCE.md).
#
# Uso:  bash scripts/azure_deploy.sh

set -euo pipefail
cd "$(dirname "$0")/.."

APP="${APP:-tufinca-paraiso-19888}"
RG="${RG:-rg-tufinca}"

echo "==> 1/3 Compilando el frontend..."
(cd frontend && npm run build)

echo "==> 2/3 Empacando el código..."
ZIP=$(mktemp -t tufinca-deploy).zip
zip -qr "$ZIP" src frontend/dist requirements.txt -x "*__pycache__*" -x "*.pyc"

echo "==> 3/3 Desplegando en Azure ($APP)..."
az webapp deploy --name "$APP" --resource-group "$RG" --src-path "$ZIP" --type zip
rm -f "$ZIP"

echo ""
echo "✅ Listo: https://$APP.azurewebsites.net"
