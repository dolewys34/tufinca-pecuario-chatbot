#!/usr/bin/env bash
#
# Arranca TODO el sistema TuFinca con un solo comando:
#   - Prepara el entorno de Python (si hace falta)
#   - Siembra la base de datos si está vacía
#   - Levanta el backend (FastAPI, puerto 8000)
#   - Levanta el frontend (React/Vite, puerto 5173)
#
# Uso:   bash start.sh
# Parar: bash stop.sh   (o Ctrl+C si lo dejas en primer plano)

set -euo pipefail
cd "$(dirname "$0")"

LOG_DIR=".logs"
mkdir -p "$LOG_DIR"

echo "🌾 TuFinca — iniciando sistema..."

# --- 1. Entorno Python ---
if [ ! -d ".venv" ]; then
  echo "==> Creando entorno virtual (.venv)..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Verificando dependencias del backend..."
python -c "import fastapi" 2>/dev/null || pip install -q -r requirements.txt

# --- 2. Base de datos (siembra si está vacía) ---
echo "==> Preparando base de datos..."
python -m src.seed || true

# --- 3. Liberar puertos por si quedó algo corriendo ---
pkill -f "uvicorn src.app.api" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1

# --- 4. Backend ---
echo "==> Levantando backend en http://localhost:8000 ..."
nohup uvicorn src.app.api:app --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
echo $! > "$LOG_DIR/backend.pid"

# --- 5. Frontend (instala dependencias la primera vez) ---
if [ ! -d "frontend/node_modules" ]; then
  echo "==> Instalando dependencias del frontend (solo la primera vez)..."
  (cd frontend && npm install)
fi
echo "==> Levantando frontend en http://localhost:5173 ..."
nohup bash -c "cd frontend && npm run dev" > "$LOG_DIR/frontend.log" 2>&1 &
echo $! > "$LOG_DIR/frontend.pid"

# --- 6. Bot de Telegram (solo si hay token configurado en .env) ---
if grep -q "^TELEGRAM_BOT_TOKEN=.\+" .env 2>/dev/null; then
  pkill -f "src.modules.chatbot.telegram_bot" 2>/dev/null || true
  echo "==> Levantando bot de Telegram..."
  nohup python -m src.modules.chatbot.telegram_bot > "$LOG_DIR/telegram.log" 2>&1 &
  echo $! > "$LOG_DIR/telegram.pid"
fi

sleep 4
IA=$(curl -s localhost:8000/api/health 2>/dev/null || echo "")

echo ""
echo "✅ Sistema arriba:"
echo "   🖥️  Aplicación:  http://localhost:5173"
echo "   📚 API/Docs:    http://localhost:8000/docs"
echo "   🤖 Motor IA:    ${IA:-(iniciando...)}"
echo ""
echo "Para detener todo:  bash stop.sh"
