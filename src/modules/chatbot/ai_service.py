"""Chatbot inteligente conectado a Azure AI Foundry.

Estrategia:
1. Construye un "contexto vivo" de la finca a partir de la base de datos
   (inventario, costos, vacunas próximas) y lo inyecta al modelo. Así el
   chatbot responde con datos REALES, no genéricos.
2. Si hay credenciales de Azure AI Foundry configuradas, usa el modelo de IA.
3. Si NO hay credenciales, cae automáticamente a un motor de reglas, para que
   el sistema funcione siempre (útil en desarrollo y demos).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src import models, schemas
from src.config import settings
from src.modules.chatbot.bot import Chatbot
from src.modules.pecuario import service as pecuario_service

# Límite de filas de detalle que se inyectan al modelo (control de tokens).
_MAX_FILAS = 40

SYSTEM_PROMPT = """Eres "TuFinca Bot", un asistente agropecuario experto para la finca
El Paraíso (Anzoátegui, Tolima, Colombia). Ayudas a productores rurales a gestionar
su inventario animal, salud/vacunación, alimentación y costos.

Reglas:
- Responde SIEMPRE en español, claro y breve, apto para un productor rural.
- Usa los DATOS ACTUALES DE LA FINCA que se te entregan para responder con cifras reales.
- Si te preguntan algo fuera de la finca o ganadería, redirige amablemente.
- Cuando no tengas el dato, dilo con honestidad; no inventes cifras.
"""


def _contexto_finca(db: Session) -> str:
    """Resumen + detalle del estado actual de la finca para inyectar al modelo.

    Incluye el listado real de animales e insumos (acotado a `_MAX_FILAS`) para
    que el agente pueda responder preguntas específicas ("¿cuánto vale la Vaca
    001?", "¿qué stock de vacuna tengo?") con datos reales.
    """
    d = pecuario_service.construir_dashboard(db)
    especies = ", ".join(f"{k}: {v}" for k, v in d.por_especie.items()) or "sin registros"
    razas = ", ".join(f"{k}: {v}" for k, v in d.por_raza.items()) or "sin registros"

    partes = [
        "DATOS ACTUALES DE LA FINCA:",
        f"- Total de animales: {d.total_animales} (activos: {d.total_activos})",
        f"- Por especie: {especies}",
        f"- Por raza: {razas}",
        f"- Avalúo total: ${d.avaluo_total:,.0f}",
        f"- Valor total: ${d.valor_total:,.0f}",
        f"- Costo total registrado: ${d.costo_total:,.0f}",
        f"- Vacunaciones registradas: {d.vacunaciones}",
        "",
        "LISTA DE ANIMALES (código | nombre | especie | raza | valor | estado):",
    ]

    animales = db.scalars(select(models.Animal).limit(_MAX_FILAS)).all()
    for a in animales:
        esp = a.especie.Especie if a.especie else "?"
        raza = a.raza.Raza if a.raza else "?"
        val = f"${a.Valor:,.0f}" if a.Valor else "sin valor"
        estado = "activo" if a.Estado == "A" else "inactivo"
        partes.append(f"  · {a.Codigo or '-'} | {a.Animal} | {esp} | {raza} | {val} | {estado}")

    productos = db.scalars(select(models.Producto).limit(_MAX_FILAS)).all()
    if productos:
        partes.append("")
        partes.append("INSUMOS EN INVENTARIO (producto | valor unitario | stock):")
        for p in productos:
            val = f"${p.Valor:,.0f}" if p.Valor else "sin valor"
            stock = sum(inv.Cantidad for inv in p.inventarios)
            partes.append(f"  · {p.Producto} | {val} | {stock}")

    return "\n".join(partes)


_PALABRAS_ESTADISTICA = (
    "estadistic", "estadístic", "grafic", "gráfic", "reporte", "resumen",
    "cuant", "cuánt", "distribu", "gast", "costo", "especie", "raza", "porcentaje",
)


def _detectar_graficos(db: Session, mensaje: str) -> list[schemas.Grafico]:
    """Devuelve gráficos relevantes según la intención del mensaje."""
    m = mensaje.lower()
    if not any(p in m for p in _PALABRAS_ESTADISTICA):
        return []
    stats = pecuario_service.estadisticas(db)
    seleccion: list[schemas.Grafico] = []
    if any(p in m for p in ("gast", "costo", "$", "dinero", "plata", "proceso")):
        seleccion.append(stats["costos"])
    if "raza" in m:
        seleccion.append(stats["raza"])
    if "especie" in m or "animal" in m:
        seleccion.append(stats["especie"])
    # Si pidió "estadística/gráfica/reporte" en general, mostramos el panorama.
    if not seleccion:
        seleccion = [stats["especie"], stats["raza"], stats["costos"]]
    # Filtramos gráficos vacíos.
    return [g for g in seleccion if g.datos]


def responder(db: Session, mensaje: str) -> tuple[str, str, list[schemas.Grafico]]:
    """Devuelve (respuesta, motor_usado, graficos)."""
    graficos = _detectar_graficos(db, mensaje)
    if settings.azure_enabled:
        try:
            return _responder_azure(db, mensaje), "azure-ai-foundry", graficos
        except Exception as exc:  # pragma: no cover - depende de red/credenciales
            # Si Azure falla, no dejamos al usuario sin respuesta.
            respaldo = Chatbot().responder(mensaje)
            return (
                f"{respaldo}\n\n(Nota: el motor de IA no está disponible: {exc})",
                "reglas",
                graficos,
            )
    return Chatbot().responder(mensaje), "reglas", graficos


def _responder_azure(db: Session, mensaje: str) -> str:
    from openai import AzureOpenAI

    client = AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    respuesta = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": _contexto_finca(db)},
            {"role": "user", "content": mensaje},
        ],
        temperature=0.3,
        max_tokens=500,
    )
    _registrar_uso(db, respuesta.usage)
    return respuesta.choices[0].message.content or "No pude generar una respuesta."


def _registrar_uso(db: Session, usage) -> None:
    """Guarda los tokens consumidos por la consulta (para la analítica en la app)."""
    if usage is None:
        return
    try:
        db.add(models.UsoIA(
            modelo=settings.azure_openai_deployment,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            total_tokens=getattr(usage, "total_tokens", 0) or 0,
        ))
        db.commit()
    except Exception:  # pragma: no cover - no debe romper la respuesta al usuario
        db.rollback()
