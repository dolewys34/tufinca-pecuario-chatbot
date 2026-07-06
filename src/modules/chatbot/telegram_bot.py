"""Bot de Telegram para TuFinca.

Conecta el MISMO agente del sistema (menús con botones, flujos guiados que
escriben en la BD, IA de Azure con herramientas y estadísticas) al canal de
Telegram, para que el productor lo use desde el celular.

Usa *long polling* (getUpdates), por lo que funciona en local sin necesidad de
una URL pública ni webhooks.

Puesta en marcha:
  1. En Telegram, habla con @BotFather → /newbot → sigue los pasos.
  2. Copia el token en el archivo .env:  TELEGRAM_BOT_TOKEN=123456:ABC...
  3. Ejecuta:  python -m src.modules.chatbot.telegram_bot
     (o simplemente `bash start.sh`, que lo levanta si hay token).
"""
from __future__ import annotations

import html
import re
import time

import httpx

from src import schemas
from src.config import settings
from src.database import SessionLocal, init_db
from src.modules.chatbot import conversation

# Nombres amigables de las herramientas del agente (transparencia).
NOMBRE_HERRAMIENTA = {
    "resumen_finca": "resumen de la finca",
    "buscar_animales": "inventario de animales",
    "consultar_inventario": "insumos y stock",
    "registrar_animal": "registro de animal",
    "registrar_vacunacion": "registro de vacunación",
    "historial_animal": "historial del animal",
    "generar_grafico": "estadísticas",
}


def _api(metodo: str) -> str:
    return f"https://api.telegram.org/bot{settings.telegram_bot_token}/{metodo}"


def _a_html(texto: str) -> str:
    """Convierte el **markdown** simple del bot a HTML de Telegram."""
    t = html.escape(texto)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.S)


def _grafico_a_texto(g: schemas.Grafico) -> str:
    """Convierte un gráfico de barras a barras de texto (se ven bien en el chat)."""
    lineas = [f"📊 <b>{html.escape(g.titulo)}</b>"]
    maximo = max((p.valor for p in g.datos), default=1) or 1
    for p in g.datos:
        n = max(1, round(p.valor / maximo * 10))
        valor = f"${p.valor:,.0f}" if g.unidad == "$" else f"{p.valor:,.0f}"
        lineas.append(f"{'▉' * n}  {html.escape(p.etiqueta)}: {valor}")
    return "\n".join(lineas)


def _enviar(client: httpx.Client, chat_id: int, resp: schemas.ChatResponse) -> None:
    partes = []
    if resp.herramientas:
        usadas = ", ".join(
            NOMBRE_HERRAMIENTA.get(h, h) for h in dict.fromkeys(resp.herramientas)
        )
        partes.append(f"🔎 <i>La IA consultó: {html.escape(usadas)}</i>")
    partes.append(_a_html(resp.respuesta))
    for g in resp.graficos:
        partes.append(_grafico_a_texto(g))

    payload: dict = {
        "chat_id": chat_id,
        "text": "\n\n".join(partes),
        "parse_mode": "HTML",
    }
    if resp.opciones:
        payload["reply_markup"] = {
            "inline_keyboard": [
                [{"text": o.texto, "callback_data": o.valor[:64]}] for o in resp.opciones
            ]
        }
    client.post(_api("sendMessage"), json=payload, timeout=30)


def _procesar_update(client: httpx.Client, update: dict) -> None:
    # Mensaje de texto normal o pulsación de un botón (callback_query).
    if "callback_query" in update:
        cq = update["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        texto = cq.get("data", "")
        # Confirma la pulsación para que Telegram quite el "relojito".
        client.post(_api("answerCallbackQuery"), json={"callback_query_id": cq["id"]}, timeout=30)
    elif "message" in update and update["message"].get("text"):
        chat_id = update["message"]["chat"]["id"]
        texto = update["message"]["text"].strip()
        if texto == "/start":
            texto = "hola"
    else:
        return

    db = SessionLocal()
    try:
        respuesta = conversation.procesar(db, texto, f"tg-{chat_id}")
    except Exception as exc:  # nunca dejamos morir el bot
        respuesta = schemas.ChatResponse(
            respuesta=f"Ups, tuve un problema procesando tu mensaje. Intenta de nuevo.\n({exc})",
            motor="asistente",
        )
    finally:
        db.close()
    _enviar(client, chat_id, respuesta)


def main() -> None:
    if not settings.telegram_bot_token:
        print("⚠️  Falta TELEGRAM_BOT_TOKEN en el .env")
        print("    1. En Telegram habla con @BotFather → /newbot")
        print("    2. Copia el token en .env:  TELEGRAM_BOT_TOKEN=123456:ABC...")
        return

    init_db()
    with httpx.Client() as client:
        yo = client.get(_api("getMe"), timeout=30).json()
        nombre = yo.get("result", {}).get("username", "?")
        print(f"🤖 Bot de Telegram activo: @{nombre}  (Ctrl+C para detener)")

        offset = 0
        while True:
            try:
                r = client.get(
                    _api("getUpdates"),
                    params={"offset": offset, "timeout": 50},
                    timeout=60,
                ).json()
                for update in r.get("result", []):
                    offset = update["update_id"] + 1
                    _procesar_update(client, update)
            except KeyboardInterrupt:
                print("\n👋 Bot detenido.")
                return
            except Exception as exc:
                print(f"(reintentando tras error: {exc})")
                time.sleep(3)


if __name__ == "__main__":
    main()
