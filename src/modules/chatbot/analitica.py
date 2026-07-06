"""Analítica de uso del modelo de IA (Azure AI Foundry), leída de la propia app.

Se calcula a partir de la tabla `Uso_IA`, que registra los tokens de cada
consulta al modelo. Así la analítica es en tiempo real (sin la demora de las
métricas de Azure).
"""
from __future__ import annotations

from collections import defaultdict
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src import models, schemas
from src.config import settings

# Precios aproximados de gpt-4.1-mini (USD por 1 millón de tokens). Solo estimación.
PRECIO_ENTRADA = 0.40 / 1_000_000
PRECIO_SALIDA = 1.60 / 1_000_000


def estadisticas_ia(db: Session) -> schemas.IAEstadisticas:
    filas = list(db.scalars(select(models.UsoIA)).all())

    total_llamadas = len(filas)
    prompt = sum(f.prompt_tokens for f in filas)
    completion = sum(f.completion_tokens for f in filas)
    total = sum(f.total_tokens for f in filas)
    costo = round(prompt * PRECIO_ENTRADA + completion * PRECIO_SALIDA, 4)

    # Agregado por día (para el gráfico)
    por_dia: dict[str, dict[str, int]] = defaultdict(lambda: {"tokens": 0, "llamadas": 0})
    for f in filas:
        dia = f.Fecha.strftime("%Y-%m-%d") if f.Fecha else "—"
        por_dia[dia]["tokens"] += f.total_tokens
        por_dia[dia]["llamadas"] += 1
    serie = [
        schemas.PuntoUsoDia(fecha=d, tokens=v["tokens"], llamadas=v["llamadas"])
        for d, v in sorted(por_dia.items())
    ]

    host = urlparse(settings.azure_openai_endpoint).netloc if settings.azure_openai_endpoint else ""

    return schemas.IAEstadisticas(
        conectado=settings.azure_enabled,
        modelo=settings.azure_openai_deployment or "—",
        endpoint=host,
        total_llamadas=total_llamadas,
        total_tokens=total,
        prompt_tokens=prompt,
        completion_tokens=completion,
        costo_estimado_usd=costo,
        por_dia=serie[-14:],  # últimas 2 semanas
    )
