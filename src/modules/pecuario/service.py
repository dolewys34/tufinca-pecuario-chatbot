"""Lógica de negocio del módulo pecuario sobre el esquema real Countryland."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from src import models, schemas
from src.models import ESTADO_ACTIVO

# Catálogos genéricos (RF-22/23/25/26): modelo, columna PK y columna nombre.
CATALOGOS = {
    "especies": (models.Especie, "Id_Especie", "Especie"),
    "razas": (models.Raza, "Id_Raza", "Raza"),
    "tipos-vacunacion": (models.TipoVacunacion, "id_Tipo_Vacunacion", "Tipo_Vacunacion"),
    "procesos-pecuarios": (models.ProcesoPecuario, "Id_Proceso_Pecuario", "Proceso_Pecuario"),
}


def crear_catalogo(db: Session, clave: str, nombre: str) -> schemas.CatalogoOut:
    modelo, pk, campo = CATALOGOS[clave]
    existente = db.scalars(select(modelo).where(getattr(modelo, campo) == nombre)).first()
    if existente:
        raise ValueError(f"'{nombre}' ya existe.")
    fila = modelo(**{campo: nombre, "Estado": ESTADO_ACTIVO})
    db.add(fila)
    db.commit()
    db.refresh(fila)
    return schemas.CatalogoOut(id=getattr(fila, pk), nombre=getattr(fila, campo))


def renombrar_catalogo(db: Session, clave: str, item_id: int, nombre: str) -> schemas.CatalogoOut:
    modelo, pk, campo = CATALOGOS[clave]
    fila = db.get(modelo, item_id)
    if not fila:
        raise LookupError("No existe.")
    setattr(fila, campo, nombre)
    db.commit()
    return schemas.CatalogoOut(id=getattr(fila, pk), nombre=nombre)


def eliminar_catalogo(db: Session, clave: str, item_id: int) -> None:
    modelo, _, _ = CATALOGOS[clave]
    fila = db.get(modelo, item_id)
    if not fila:
        raise LookupError("No existe.")
    db.delete(fila)
    db.commit()


# ---------- Catálogos ----------
def listar_especies(db: Session) -> list[schemas.CatalogoOut]:
    filas = db.scalars(select(models.Especie).order_by(models.Especie.Especie)).all()
    return [schemas.CatalogoOut(id=e.Id_Especie, nombre=e.Especie) for e in filas]


def listar_razas(db: Session) -> list[schemas.CatalogoOut]:
    filas = db.scalars(select(models.Raza).order_by(models.Raza.Raza)).all()
    return [schemas.CatalogoOut(id=r.Id_Raza, nombre=r.Raza) for r in filas]


def listar_procesos(db: Session) -> list[schemas.CatalogoOut]:
    filas = db.scalars(
        select(models.ProcesoPecuario).order_by(models.ProcesoPecuario.Proceso_Pecuario)
    ).all()
    return [schemas.CatalogoOut(id=p.Id_Proceso_Pecuario, nombre=p.Proceso_Pecuario) for p in filas]


def listar_tipos_vacunacion(db: Session) -> list[schemas.CatalogoOut]:
    filas = db.scalars(
        select(models.TipoVacunacion).order_by(models.TipoVacunacion.Tipo_Vacunacion)
    ).all()
    return [schemas.CatalogoOut(id=t.id_Tipo_Vacunacion, nombre=t.Tipo_Vacunacion) for t in filas]


def listar_lotes(db: Session) -> list[models.Lote]:
    return list(db.scalars(select(models.Lote).order_by(models.Lote.Lote)).all())


def listar_unidades(db: Session) -> list[schemas.CatalogoOut]:
    filas = db.scalars(select(models.Unidad).order_by(models.Unidad.Unidad)).all()
    return [schemas.CatalogoOut(id=u.Id_Unidad, nombre=u.Unidad) for u in filas]


def listar_marcas(db: Session) -> list[schemas.CatalogoOut]:
    filas = db.scalars(select(models.Marca).order_by(models.Marca.Marca)).all()
    return [schemas.CatalogoOut(id=m.Id_Marca, nombre=m.Marca) for m in filas]


# ---------- Productos / insumos ----------
def _producto_salida(p: models.Producto) -> schemas.ProductoOut:
    salida = schemas.ProductoOut.model_validate(p)
    salida.unidad_nombre = p.unidad.Unidad if p.unidad else None
    salida.marca_nombre = p.marca.Marca if p.marca else None
    salida.stock = sum(inv.Cantidad for inv in p.inventarios)
    return salida


def listar_productos(db: Session) -> list[schemas.ProductoOut]:
    productos = db.scalars(select(models.Producto).order_by(models.Producto.Producto)).all()
    return [_producto_salida(p) for p in productos]


def crear_producto(db: Session, datos: schemas.ProductoCreate) -> schemas.ProductoOut:
    producto = models.Producto(**datos.model_dump(), Estado=ESTADO_ACTIVO)
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return _producto_salida(producto)


# ---------- Animales ----------
def _a_salida(animal: models.Animal) -> schemas.AnimalOut:
    salida = schemas.AnimalOut.model_validate(animal)
    salida.especie_nombre = animal.especie.Especie if animal.especie else None
    salida.raza_nombre = animal.raza.Raza if animal.raza else None
    return salida


def crear_animal(db: Session, datos: schemas.AnimalCreate) -> schemas.AnimalOut:
    animal = models.Animal(**datos.model_dump(), Estado=ESTADO_ACTIVO)
    db.add(animal)
    db.commit()
    db.refresh(animal)
    return _a_salida(animal)


def listar_animales(db: Session) -> list[schemas.AnimalOut]:
    animales = db.scalars(
        select(models.Animal).order_by(models.Animal.Fecha_Inicio.desc())
    ).all()
    return [_a_salida(a) for a in animales]


def obtener_animal(db: Session, animal_id: int) -> models.Animal | None:
    return db.get(models.Animal, animal_id)


def actualizar_animal(
    db: Session, animal: models.Animal, datos: schemas.AnimalUpdate
) -> schemas.AnimalOut:
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(animal, campo, valor)
    db.commit()
    db.refresh(animal)
    return _a_salida(animal)


def eliminar_animal(db: Session, animal: models.Animal) -> None:
    db.delete(animal)
    db.commit()


# ---------- Detalle de animal (eventos) ----------
def _detalle_salida(detalle: models.DetalleAnimal) -> schemas.DetalleAnimalOut:
    salida = schemas.DetalleAnimalOut.model_validate(detalle)
    salida.proceso_nombre = detalle.proceso.Proceso_Pecuario if detalle.proceso else None
    salida.tipo_vacunacion_nombre = (
        detalle.tipo_vacunacion.Tipo_Vacunacion if detalle.tipo_vacunacion else None
    )
    salida.producto_nombre = detalle.producto.Producto if detalle.producto else None
    return salida


def historial_animal(db: Session, animal: models.Animal) -> list[schemas.DetalleAnimalOut]:
    """Historial completo de eventos de un animal (RF-27, Tabla 22)."""
    return [_detalle_salida(d) for d in animal.detalles]


def agregar_detalle(
    db: Session, animal: models.Animal, datos: schemas.DetalleAnimalCreate
) -> schemas.DetalleAnimalOut:
    detalle = models.DetalleAnimal(
        Animal_Id=animal.Id_Animal, Estado=ESTADO_ACTIVO, **datos.model_dump()
    )
    db.add(detalle)
    db.commit()
    db.refresh(detalle)
    return _detalle_salida(detalle)


# ---------- Dashboard / indicadores ----------
def construir_dashboard(db: Session) -> schemas.DashboardOut:
    animales = list(db.scalars(select(models.Animal)).all())
    activos = [a for a in animales if a.Estado == ESTADO_ACTIVO]

    por_especie = Counter(a.especie.Especie if a.especie else "Sin especie" for a in animales)
    por_raza = Counter(a.raza.Raza if a.raza else "Sin raza" for a in animales)

    avaluo_total = round(sum(a.Avaluo or 0 for a in animales), 2)
    valor_total = round(sum(a.Valor or 0 for a in animales), 2)
    costo_total = round(sum(a.Costo or 0 for a in animales), 2)

    total_vacunaciones = len(
        db.scalars(
            select(models.DetalleAnimal).where(
                models.DetalleAnimal.Tipo_Vacunacion_Id.is_not(None)
            )
        ).all()
    )

    return schemas.DashboardOut(
        total_animales=len(animales),
        total_activos=len(activos),
        por_especie=dict(por_especie),
        por_raza=dict(por_raza),
        avaluo_total=avaluo_total,
        valor_total=valor_total,
        costo_total=costo_total,
        vacunaciones=total_vacunaciones,
    )


def obtener_alertas(db: Session) -> list[schemas.Alerta]:
    """Alertas operativas: insumos, vacunas próximas/vencidas y animales sin vacunas."""
    alertas: list[schemas.Alerta] = []
    ahora = datetime.now()
    limite = ahora + timedelta(days=30)

    # Vacunas con próxima aplicación (Fecha_Fin) vencida o dentro de 30 días.
    vacunaciones = db.scalars(
        select(models.DetalleAnimal).where(
            models.DetalleAnimal.Tipo_Vacunacion_Id.is_not(None),
            models.DetalleAnimal.Fecha_Fin.is_not(None),
        )
    ).all()
    for d in vacunaciones:
        nombre = d.animal.Codigo or d.animal.Animal if d.animal else f"animal {d.Animal_Id}"
        vacuna = d.tipo_vacunacion.Tipo_Vacunacion if d.tipo_vacunacion else "vacuna"
        if d.Fecha_Fin < ahora:
            alertas.append(schemas.Alerta(
                tipo="vacuna_vencida",
                detalle=f"{nombre}: {vacuna} vencida desde {d.Fecha_Fin:%Y-%m-%d}",
            ))
        elif d.Fecha_Fin <= limite:
            alertas.append(schemas.Alerta(
                tipo="vacuna_proxima",
                detalle=f"{nombre}: {vacuna} programada para {d.Fecha_Fin:%Y-%m-%d}",
            ))

    for p in listar_productos(db):
        if p.stock == 0:
            alertas.append(schemas.Alerta(tipo="insumo_agotado", detalle=f"{p.Producto}: sin stock"))
        elif p.stock <= 10:
            alertas.append(schemas.Alerta(tipo="stock_bajo", detalle=f"{p.Producto}: quedan {p.stock}"))
    activos = [a for a in db.scalars(select(models.Animal)).all() if a.Estado == ESTADO_ACTIVO]
    for a in activos:
        if not any(d.Tipo_Vacunacion_Id for d in a.detalles):
            alertas.append(
                schemas.Alerta(tipo="sin_vacunas", detalle=f"{a.Codigo or a.Animal} no tiene vacunaciones registradas")
            )
    return alertas


# ---------- Indicadores del Objetivo 4 (ACA 2, Tabla 16) ----------
def calcular_indicadores(db: Session) -> schemas.IndicadoresOut:
    """Indicadores de trazabilidad para la evaluación comparativa (antes/después)."""
    animales = list(db.scalars(select(models.Animal)).all())
    eventos = list(db.scalars(select(models.DetalleAnimal)).all())
    ahora = datetime.now()
    limite = ahora + timedelta(days=30)

    def completo(a: models.Animal) -> bool:
        # Datos indispensables según Figura 17: código, sexo, peso, nacimiento, especie y raza.
        return all([a.Codigo, a.Sexo, a.Peso, a.Fecha_Nacimiento, a.Especie_Id, a.Raza_Id])

    con_historial = [a for a in animales if a.detalles]
    con_responsable = [e for e in eventos if e.Responsable]

    vacunas = [e for e in eventos if e.Tipo_Vacunacion_Id]
    vencidas = [e for e in vacunas if e.Fecha_Fin and e.Fecha_Fin < ahora]
    proximas = [e for e in vacunas if e.Fecha_Fin and ahora <= e.Fecha_Fin <= limite]
    al_dia = [e for e in vacunas if not e.Fecha_Fin or e.Fecha_Fin > limite]

    pct = lambda parte, todo: round(100 * len(parte) / len(todo), 1) if todo else 0.0

    return schemas.IndicadoresOut(
        total_animales=len(animales),
        total_eventos=len(eventos),
        registros_completos_pct=pct([a for a in animales if completo(a)], animales),
        animales_con_historial_pct=pct(con_historial, animales),
        eventos_con_responsable_pct=pct(con_responsable, eventos),
        vacunas_al_dia=len(al_dia),
        vacunas_proximas=len(proximas),
        vacunas_vencidas=len(vencidas),
    )


def estadisticas(db: Session) -> dict[str, schemas.Grafico]:
    """Series listas para graficar, indexadas por clave temática."""
    animales = list(db.scalars(select(models.Animal)).all())

    por_especie = Counter(a.especie.Especie if a.especie else "Sin especie" for a in animales)
    por_raza = Counter(a.raza.Raza if a.raza else "Sin raza" for a in animales)

    # Costos por proceso pecuario (desde Detalle_Animal)
    detalles = list(db.scalars(select(models.DetalleAnimal)).all())
    por_proceso: Counter[str] = Counter()
    for d in detalles:
        nombre = d.proceso.Proceso_Pecuario if d.proceso else "Otro"
        por_proceso[nombre] += d.Costo or 0

    def serie(pares) -> list[schemas.PuntoGrafico]:
        return [schemas.PuntoGrafico(etiqueta=str(k), valor=float(v)) for k, v in pares]

    return {
        "especie": schemas.Grafico(
            titulo="Animales por especie", tipo="barras", unidad="animales",
            datos=serie(por_especie.items()),
        ),
        "raza": schemas.Grafico(
            titulo="Animales por raza", tipo="barras", unidad="animales",
            datos=serie(por_raza.items()),
        ),
        "costos": schemas.Grafico(
            titulo="Costos por proceso pecuario", tipo="barras", unidad="$",
            datos=serie(por_proceso.items()),
        ),
    }
