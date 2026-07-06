#!/usr/bin/env bash
#
# Detiene el backend y el frontend de TuFinca.
# Uso:  bash stop.sh

cd "$(dirname "$0")"

echo "🛑 Deteniendo TuFinca..."
pkill -f "uvicorn src.app.api" 2>/dev/null && echo "   backend detenido" || echo "   backend no estaba corriendo"
pkill -f "vite" 2>/dev/null && echo "   frontend detenido" || echo "   frontend no estaba corriendo"
pkill -f "src.modules.chatbot.telegram_bot" 2>/dev/null && echo "   bot de Telegram detenido" || true
rm -f .logs/backend.pid .logs/frontend.pid .logs/telegram.pid
echo "✅ Listo."
