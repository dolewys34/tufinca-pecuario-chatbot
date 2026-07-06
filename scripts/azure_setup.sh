#!/usr/bin/env bash
#
# Crea un recurso de Azure AI Foundry (Azure OpenAI), despliega un modelo,
# obtiene el endpoint + la clave y los escribe en el archivo .env del proyecto.
#
# Requisitos:
#   - Azure CLI instalado (az) y sesión iniciada:  az login
#   - Una suscripción de Azure activa.
#
# Uso:
#   bash scripts/azure_setup.sh
#
# Nota: crear el recurso y el despliegue NO tiene costo; solo se cobra por el
# uso (tokens) cuando el chatbot consulta el modelo.

set -euo pipefail

# ----------------------- Parámetros (puedes editarlos) -----------------------
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-tufinca}"
LOCATION="${LOCATION:-eastus2}"
ACCOUNT_NAME="${ACCOUNT_NAME:-tufinca-foundry-$RANDOM}"   # debe ser único
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-gpt-4.1-mini}"
MODEL_NAME="${MODEL_NAME:-gpt-4.1-mini}"
MODEL_VERSION="${MODEL_VERSION:-2025-04-14}"
SKU_CAPACITY="${SKU_CAPACITY:-20}"    # miles de tokens/min

# Ruta al .env del proyecto (un nivel arriba de scripts/)
ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"

echo "==> Suscripción activa:"
az account show --query "{nombre:name, id:id}" -o table

echo ""
echo "==> 1/5 Creando grupo de recursos '$RESOURCE_GROUP' en '$LOCATION'..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" -o none

echo "==> 2/5 Creando recurso de Azure OpenAI (Foundry) '$ACCOUNT_NAME'..."
az cognitiveservices account create \
  --name "$ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --kind OpenAI \
  --sku S0 \
  --custom-domain "$ACCOUNT_NAME" \
  --yes -o none

echo "==> 3/5 Desplegando el modelo '$MODEL_NAME' (deployment '$DEPLOYMENT_NAME')..."
az cognitiveservices account deployment create \
  --name "$ACCOUNT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --deployment-name "$DEPLOYMENT_NAME" \
  --model-name "$MODEL_NAME" \
  --model-version "$MODEL_VERSION" \
  --model-format OpenAI \
  --sku-name "GlobalStandard" \
  --sku-capacity "$SKU_CAPACITY" -o none

echo "==> 4/5 Obteniendo endpoint y clave..."
ENDPOINT=$(az cognitiveservices account show \
  --name "$ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" \
  --query "properties.endpoint" -o tsv)
KEY=$(az cognitiveservices account keys list \
  --name "$ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" \
  --query "key1" -o tsv)

echo "==> 5/5 Escribiendo credenciales en $ENV_FILE ..."
cat > "$ENV_FILE" <<EOF
# Generado por scripts/azure_setup.sh
AZURE_OPENAI_ENDPOINT=$ENDPOINT
AZURE_OPENAI_API_KEY=$KEY
AZURE_OPENAI_DEPLOYMENT=$DEPLOYMENT_NAME
AZURE_OPENAI_API_VERSION=2024-10-21
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
EOF

echo ""
echo "✅ Listo. Recurso: $ACCOUNT_NAME"
echo "   Endpoint: $ENDPOINT"
echo "   Deployment: $DEPLOYMENT_NAME"
echo ""
echo "Reinicia el backend para activar la IA:"
echo "   uvicorn src.app.api:app --reload"
