"""Modelos ORM del módulo pecuario.

Mapean fielmente el esquema real de la base de datos **Countryland** (TuFinca),
manteniendo los nombres de tabla y columna originales (SQL Server) para que el
sistema quede alineado con la base productiva.

Convenciones del esquema original:
- Estado: nchar(1) → 'A' (activo) / 'I' (inactivo).
- Valores contables: numeric(18,0) → Float.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

ESTADO_ACTIVO = "A"
ESTADO_INACTIVO = "I"


# ---------- Catálogos ----------
class Especie(Base):
    __tablename__ = "Especies"

    Id_Especie: Mapped[int] = mapped_column(primary_key=True)
    Especie: Mapped[str] = mapped_column(String(50))
    Estado: Mapped[str] = mapped_column(String(1), default=ESTADO_ACTIVO)
    Observaciones: Mapped[str | None] = mapped_column(String, default=None)

    animales: Mapped[list[Animal]] = relationship(back_populates="especie")


class Raza(Base):
    __tablename__ = "Razas"

    Id_Raza: Mapped[int] = mapped_column(primary_key=True)
    Raza: Mapped[str] = mapped_column(String(50))
    Estado: Mapped[str] = mapped_column(String(1), default=ESTADO_ACTIVO)
    Observaciones: Mapped[str | None] = mapped_column(String, default=None)

    animales: Mapped[list[Animal]] = relationship(back_populates="raza")


class Lote(Base):
    __tablename__ = "Lotes"

    Id_Lote: Mapped[int] = mapped_column(primary_key=True)
    Lote: Mapped[str] = mapped_column(String(50))
    Empresa_Id: Mapped[int | None] = mapped_column(default=None)
    Area: Mapped[float | None] = mapped_column(Float, default=None)
    Sica: Mapped[str | None] = mapped_column(String(50), default=None)  # tipo de suelo
    Observaciones: Mapped[str | None] = mapped_column(String, default=None)
    Avaluo: Mapped[float | None] = mapped_column(Float, default=None)
    Cuenta_Debito_Id: Mapped[int | None] = mapped_column(default=None)
    Cuenta_Credito_Id: Mapped[int | None] = mapped_column(default=None)
    Estado: Mapped[str] = mapped_column(String(1), default=ESTADO_ACTIVO)
    Fecha: Mapped[datetime | None] = mapped_column(DateTime, default=None)


class ProcesoPecuario(Base):
    __tablename__ = "Procesos_Pecuarios"

    Id_Proceso_Pecuario: Mapped[int] = mapped_column(primary_key=True)
    Proceso_Pecuario: Mapped[str] = mapped_column(String(50))
    Estado: Mapped[str] = mapped_column(String(1), default=ESTADO_ACTIVO)
    Observaciones: Mapped[str | None] = mapped_column(String, default=None)
    Valor: Mapped[float | None] = mapped_column(Float, default=None)
    Avaluo: Mapped[float | None] = mapped_column(Float, default=None)
    Tiempo_Estimado: Mapped[float | None] = mapped_column(Float, default=None)
    Cuenta_Debito_Id: Mapped[int | None] = mapped_column(default=None)
    Cuenta_Credito_Id: Mapped[int | None] = mapped_column(default=None)

    detalles: Mapped[list[DetalleAnimal]] = relationship(back_populates="proceso")


class TipoVacunacion(Base):
    __tablename__ = "Tipo_Vacunacion"

    id_Tipo_Vacunacion: Mapped[int] = mapped_column(primary_key=True)
    Tipo_Vacunacion: Mapped[str] = mapped_column(String(50))
    Estado: Mapped[str] = mapped_column(String(1), default=ESTADO_ACTIVO)
    Observaciones: Mapped[str | None] = mapped_column(String, default=None)

    detalles: Mapped[list[DetalleAnimal]] = relationship(back_populates="tipo_vacunacion")


# ---------- Entidades principales ----------
class Animal(Base):
    __tablename__ = "Animales"

    Id_Animal: Mapped[int] = mapped_column(primary_key=True)
    Animal: Mapped[str] = mapped_column(String(50))                       # nombre/identificación
    Raza_Id: Mapped[int] = mapped_column(ForeignKey("Razas.Id_Raza"))
    Especie_Id: Mapped[int] = mapped_column(ForeignKey("Especies.Id_Especie"))
    Avaluo: Mapped[float | None] = mapped_column(Float, default=None)
    Valor: Mapped[float | None] = mapped_column(Float, default=None)
    Costo: Mapped[float | None] = mapped_column(Float, default=None)
    Fecha_Inicio: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    Fecha_Fin: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    Estado: Mapped[str] = mapped_column(String(1), default=ESTADO_ACTIVO)
    Observaciones: Mapped[str | None] = mapped_column(String, default=None)
    Codigo: Mapped[str | None] = mapped_column(String(50), default=None, index=True)
    Cuenta_Debito_Id: Mapped[int | None] = mapped_column(default=None)
    Cuenta_Credito_Id: Mapped[int | None] = mapped_column(default=None)

    especie: Mapped[Especie] = relationship(back_populates="animales")
    raza: Mapped[Raza] = relationship(back_populates="animales")
    detalles: Mapped[list[DetalleAnimal]] = relationship(
        back_populates="animal", cascade="all, delete-orphan"
    )


class DetalleAnimal(Base):
    """Eventos/procesos aplicados a un animal (vacunación, alimentación, etc.)."""

    __tablename__ = "Detalle_Animal"

    Id_Detalle_Animal: Mapped[int] = mapped_column(primary_key=True)
    Animal_Id: Mapped[int] = mapped_column(ForeignKey("Animales.Id_Animal"))
    Proceso_Pecuario_Id: Mapped[int] = mapped_column(
        ForeignKey("Procesos_Pecuarios.Id_Proceso_Pecuario")
    )
    Producto_Id: Mapped[int | None] = mapped_column(
        ForeignKey("Productos.Id_Producto"), default=None
    )
    Mano_Obra_Id: Mapped[int | None] = mapped_column(
        ForeignKey("Mano_Obra.Id_Mano_Obra"), default=None
    )
    Tipo_Vacunacion_Id: Mapped[int | None] = mapped_column(
        ForeignKey("Tipo_Vacunacion.id_Tipo_Vacunacion"), default=None
    )
    Avaluo: Mapped[float | None] = mapped_column(Float, default=None)
    Valor: Mapped[float | None] = mapped_column(Float, default=None)
    Costo: Mapped[float | None] = mapped_column(Float, default=None)
    Cuenta_Debito_Id: Mapped[int | None] = mapped_column(default=None)
    Cuenta_Credito_Id: Mapped[int | None] = mapped_column(default=None)
    Estado: Mapped[str] = mapped_column(String(1), default=ESTADO_ACTIVO)
    Observaciones: Mapped[str | None] = mapped_column(String, default=None)
    Usuario_Id: Mapped[int | None] = mapped_column(default=None)
    Fecha_Inicio: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())
    Fecha_Fin: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    animal: Mapped[Animal] = relationship(back_populates="detalles")
    proceso: Mapped[ProcesoPecuario] = relationship(back_populates="detalles")
    tipo_vacunacion: Mapped[TipoVacunacion | None] = relationship(back_populates="detalles")
    producto: Mapped[Producto | None] = relationship(back_populates="detalles")
    mano_obra: Mapped[ManoObra | None] = relationship()


# ---------- Insumos y recursos ----------
class Unidad(Base):
    """Unidad de medida de los productos (kg, litro, dosis...)."""

    __tablename__ = "Unidades"

    Id_Unidad: Mapped[int] = mapped_column(primary_key=True)
    Unidad: Mapped[str] = mapped_column(String)
    Estado: Mapped[str] = mapped_column(String(1), default=ESTADO_ACTIVO)
    Observaciones: Mapped[str | None] = mapped_column(String, default=None)

    productos: Mapped[list[Producto]] = relationship(back_populates="unidad")


class Marca(Base):
    __tablename__ = "Marca"

    Id_Marca: Mapped[int] = mapped_column(primary_key=True)
    Marca: Mapped[str] = mapped_column(String)
    Estado: Mapped[str] = mapped_column(String(1), default=ESTADO_ACTIVO)
    Calificacion: Mapped[float | None] = mapped_column(Float, default=None)
    Observaciones: Mapped[str | None] = mapped_column(String, default=None)

    productos: Mapped[list[Producto]] = relationship(back_populates="marca")


class Producto(Base):
    """Insumos: vacunas, alimentos, medicinas, etc."""

    __tablename__ = "Productos"

    Id_Producto: Mapped[int] = mapped_column(primary_key=True)
    Producto: Mapped[str] = mapped_column(String)
    Unidad_Id: Mapped[int | None] = mapped_column(ForeignKey("Unidades.Id_Unidad"), default=None)
    Marca_Id: Mapped[int | None] = mapped_column(ForeignKey("Marca.Id_Marca"), default=None)
    Estado: Mapped[str] = mapped_column(String(1), default=ESTADO_ACTIVO)
    Observaciones: Mapped[str | None] = mapped_column(String, default=None)
    Valor: Mapped[float | None] = mapped_column(Float, default=None)
    Avaluo: Mapped[float | None] = mapped_column(Float, default=None)
    Cuenta_Debito_Id: Mapped[int | None] = mapped_column(default=None)
    Cuenta_Credito_Id: Mapped[int | None] = mapped_column(default=None)
    Codigo: Mapped[str | None] = mapped_column(String(50), default=None, index=True)

    unidad: Mapped[Unidad | None] = relationship(back_populates="productos")
    marca: Mapped[Marca | None] = relationship(back_populates="productos")
    detalles: Mapped[list[DetalleAnimal]] = relationship(back_populates="producto")
    inventarios: Mapped[list[Inventario]] = relationship(back_populates="producto")


class ManoObra(Base):
    """Jornales / labor asociada a procesos (costo)."""

    __tablename__ = "Mano_Obra"

    Id_Mano_Obra: Mapped[int] = mapped_column(primary_key=True)
    Usuario_Id: Mapped[int | None] = mapped_column(default=None)
    Maquinaria_Id: Mapped[int | None] = mapped_column(default=None)
    Valor: Mapped[float | None] = mapped_column(Float, default=None)
    Cantidad: Mapped[float | None] = mapped_column(Float, default=None)
    Fecha_Inicio: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    Fecha_Fin: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    Cuenta_Debito_Id: Mapped[int | None] = mapped_column(default=None)
    Cuenta_Credito_Id: Mapped[int | None] = mapped_column(default=None)


class UsoIA(Base):
    """Registro del consumo del modelo de IA (Azure AI Foundry).

    Tabla de apoyo de la aplicación (no pertenece al esquema Countryland). Se
    inserta una fila por cada consulta al modelo, con los tokens consumidos.
    Permite mostrar la analítica de uso dentro de la app en tiempo real.
    """

    __tablename__ = "Uso_IA"

    Id_Uso: Mapped[int] = mapped_column(primary_key=True)
    Fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    modelo: Mapped[str] = mapped_column(String(60), default="")
    prompt_tokens: Mapped[int] = mapped_column(default=0)
    completion_tokens: Mapped[int] = mapped_column(default=0)
    total_tokens: Mapped[int] = mapped_column(default=0)


class Inventario(Base):
    """Stock de un producto."""

    __tablename__ = "Inventarios"

    Id_Inventario: Mapped[int] = mapped_column(primary_key=True)
    Producto_Id: Mapped[int] = mapped_column(ForeignKey("Productos.Id_Producto"))
    Cantidad: Mapped[int] = mapped_column(default=0)
    Estado: Mapped[str] = mapped_column(String(10), default=ESTADO_ACTIVO)
    Observaciones: Mapped[str | None] = mapped_column(String, default=None)

    producto: Mapped[Producto] = relationship(back_populates="inventarios")
