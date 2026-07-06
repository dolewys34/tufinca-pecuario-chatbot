"""Pruebas del bot de Telegram (funciones puras) y del catálogo del agente."""
from src import schemas
from src.modules.chatbot.telegram_bot import _a_html, _grafico_a_texto


def test_markdown_a_html_telegram() -> None:
    assert _a_html("Hola **mundo**") == "Hola <b>mundo</b>"
    # Escapa HTML peligroso
    assert "&lt;script&gt;" in _a_html("<script>")


def test_grafico_a_texto() -> None:
    g = schemas.Grafico(
        titulo="Animales por especie",
        unidad="animales",
        datos=[
            schemas.PuntoGrafico(etiqueta="Bovino", valor=6),
            schemas.PuntoGrafico(etiqueta="Porcino", valor=3),
        ],
    )
    texto = _grafico_a_texto(g)
    assert "Animales por especie" in texto
    assert "Bovino" in texto and "▉" in texto


def test_catalogo_coincidencia_aproximada() -> None:
    # "brahmann" (mal escrito) debe resolver a la raza existente "Brahman",
    # no crear una nueva.
    from src.database import SessionLocal
    from src.modules.chatbot.agent import _get_or_create
    from src import models

    db = SessionLocal()
    try:
        antes = db.query(models.Raza).count()
        raza = _get_or_create(db, models.Raza, "Raza", "brahmann")
        despues = db.query(models.Raza).count()
        assert raza.Raza == "Brahman"
        assert antes == despues  # no creó duplicado
    finally:
        db.close()
