"""Configuración de la base de datos con SQLAlchemy.

Usa SQLite en local (cero configuración). Para producción basta con cambiar
`DATABASE_URL` a PostgreSQL sin tocar el resto del código.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM."""


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: entrega una sesión y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea las tablas si no existen y aplica migraciones ligeras."""
    from src import models  # noqa: F401  (registra los modelos)

    Base.metadata.create_all(bind=engine)
    _migrar_columnas()


def _migrar_columnas() -> None:
    """Agrega columnas nuevas a tablas existentes (SQLite, sin perder datos).

    Extensiones de la Fase II (documento ACA 2): sexo/peso/fecha de nacimiento
    del animal y responsable del evento.
    """
    from sqlalchemy import inspect, text

    pendientes = {
        "Animales": [
            ("Sexo", "VARCHAR(10)"),
            ("Peso", "FLOAT"),
            ("Fecha_Nacimiento", "DATETIME"),
        ],
        "Detalle_Animal": [("Responsable", "VARCHAR(100)")],
    }
    inspector = inspect(engine)
    with engine.begin() as conn:
        for tabla, columnas in pendientes.items():
            if tabla not in inspector.get_table_names():
                continue
            existentes = {c["name"] for c in inspector.get_columns(tabla)}
            for nombre, tipo in columnas:
                if nombre not in existentes:
                    conn.execute(text(f'ALTER TABLE "{tabla}" ADD COLUMN "{nombre}" {tipo}'))
