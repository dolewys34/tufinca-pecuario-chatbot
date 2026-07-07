"""API REST de TuFinca Pecuario + Chatbot (FastAPI).

Alineada con el esquema real Countryland (TuFinca).

Ejecutar en local:
    uvicorn src.app.api:app --reload
Docs interactivas:  http://localhost:8000/docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src import schemas
from src.config import settings
from src.database import get_db, init_db
from src.modules.chatbot import analitica, conversation
from src.modules.pecuario import service


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


# Inicializa también al importar (los tests no ejecutan el lifespan).
# Es idempotente: crea tablas/columnas solo si faltan.
init_db()

app = FastAPI(title=settings.api_title, version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "ia": "azure-ai-foundry" if settings.azure_enabled else "reglas"}


# ---------- Dashboard ----------
@app.get("/api/dashboard", response_model=schemas.DashboardOut)
def dashboard(db: Session = Depends(get_db)) -> schemas.DashboardOut:
    return service.construir_dashboard(db)


@app.get("/api/alertas", response_model=list[schemas.Alerta])
def alertas(db: Session = Depends(get_db)):
    return service.obtener_alertas(db)


@app.get("/api/indicadores", response_model=schemas.IndicadoresOut)
def indicadores(db: Session = Depends(get_db)):
    """Indicadores de trazabilidad del Objetivo Específico 4 (ACA 2, Tabla 16)."""
    return service.calcular_indicadores(db)


# ---------- CRUD de catálogos (RF-22, RF-23, RF-25, RF-26) ----------
@app.post("/api/catalogos/{clave}", response_model=schemas.CatalogoOut, status_code=201)
def crear_item_catalogo(clave: str, datos: schemas.CatalogoCreate, db: Session = Depends(get_db)):
    if clave not in service.CATALOGOS:
        raise HTTPException(404, "Catálogo desconocido")
    try:
        return service.crear_catalogo(db, clave, datos.nombre.strip())
    except ValueError as exc:
        raise HTTPException(409, str(exc))


@app.patch("/api/catalogos/{clave}/{item_id}", response_model=schemas.CatalogoOut)
def renombrar_item_catalogo(
    clave: str, item_id: int, datos: schemas.CatalogoCreate, db: Session = Depends(get_db)
):
    if clave not in service.CATALOGOS:
        raise HTTPException(404, "Catálogo desconocido")
    try:
        return service.renombrar_catalogo(db, clave, item_id, datos.nombre.strip())
    except LookupError:
        raise HTTPException(404, "Ítem no encontrado")


@app.delete("/api/catalogos/{clave}/{item_id}", status_code=204)
def eliminar_item_catalogo(clave: str, item_id: int, db: Session = Depends(get_db)):
    if clave not in service.CATALOGOS:
        raise HTTPException(404, "Catálogo desconocido")
    try:
        service.eliminar_catalogo(db, clave, item_id)
    except LookupError:
        raise HTTPException(404, "Ítem no encontrado")
    except Exception:
        raise HTTPException(
            409, "No se puede eliminar: hay registros que dependen de este ítem."
        )


# ---------- Catálogos ----------
@app.get("/api/especies", response_model=list[schemas.CatalogoOut])
def especies(db: Session = Depends(get_db)):
    return service.listar_especies(db)


@app.get("/api/razas", response_model=list[schemas.CatalogoOut])
def razas(db: Session = Depends(get_db)):
    return service.listar_razas(db)


@app.get("/api/procesos-pecuarios", response_model=list[schemas.CatalogoOut])
def procesos(db: Session = Depends(get_db)):
    return service.listar_procesos(db)


@app.get("/api/tipos-vacunacion", response_model=list[schemas.CatalogoOut])
def tipos_vacunacion(db: Session = Depends(get_db)):
    return service.listar_tipos_vacunacion(db)


@app.get("/api/lotes", response_model=list[schemas.LoteOut])
def lotes(db: Session = Depends(get_db)):
    return service.listar_lotes(db)


@app.get("/api/unidades", response_model=list[schemas.CatalogoOut])
def unidades(db: Session = Depends(get_db)):
    return service.listar_unidades(db)


@app.get("/api/marcas", response_model=list[schemas.CatalogoOut])
def marcas(db: Session = Depends(get_db)):
    return service.listar_marcas(db)


# ---------- Productos / insumos ----------
@app.get("/api/productos", response_model=list[schemas.ProductoOut])
def productos(db: Session = Depends(get_db)):
    return service.listar_productos(db)


@app.post("/api/productos", response_model=schemas.ProductoOut, status_code=201)
def crear_producto(datos: schemas.ProductoCreate, db: Session = Depends(get_db)):
    return service.crear_producto(db, datos)


# ---------- Animales ----------
@app.get("/api/animales", response_model=list[schemas.AnimalOut])
def listar(db: Session = Depends(get_db)):
    return service.listar_animales(db)


@app.post("/api/animales", response_model=schemas.AnimalOut, status_code=201)
def crear(datos: schemas.AnimalCreate, db: Session = Depends(get_db)):
    return service.crear_animal(db, datos)


@app.get("/api/animales/{animal_id}", response_model=schemas.AnimalOut)
def obtener(animal_id: int, db: Session = Depends(get_db)):
    animal = service.obtener_animal(db, animal_id)
    if not animal:
        raise HTTPException(404, "Animal no encontrado")
    return service._a_salida(animal)


@app.patch("/api/animales/{animal_id}", response_model=schemas.AnimalOut)
def actualizar(animal_id: int, datos: schemas.AnimalUpdate, db: Session = Depends(get_db)):
    animal = service.obtener_animal(db, animal_id)
    if not animal:
        raise HTTPException(404, "Animal no encontrado")
    return service.actualizar_animal(db, animal, datos)


@app.delete("/api/animales/{animal_id}", status_code=204)
def eliminar(animal_id: int, db: Session = Depends(get_db)):
    animal = service.obtener_animal(db, animal_id)
    if not animal:
        raise HTTPException(404, "Animal no encontrado")
    service.eliminar_animal(db, animal)


# ---------- Detalle de animal (vacunación, alimentación, procesos) ----------
@app.get("/api/animales/{animal_id}/detalle", response_model=list[schemas.DetalleAnimalOut])
def historial(animal_id: int, db: Session = Depends(get_db)):
    """Historial completo del animal (RF-27, Tabla 22 del ACA 2)."""
    animal = service.obtener_animal(db, animal_id)
    if not animal:
        raise HTTPException(404, "Animal no encontrado")
    return service.historial_animal(db, animal)


@app.post(
    "/api/animales/{animal_id}/detalle",
    response_model=schemas.DetalleAnimalOut,
    status_code=201,
)
def registrar_detalle(
    animal_id: int, datos: schemas.DetalleAnimalCreate, db: Session = Depends(get_db)
):
    animal = service.obtener_animal(db, animal_id)
    if not animal:
        raise HTTPException(404, "Animal no encontrado")
    return service.agregar_detalle(db, animal, datos)


# ---------- Chatbot ----------
@app.post("/api/chat", response_model=schemas.ChatResponse)
def chat(datos: schemas.ChatRequest, db: Session = Depends(get_db)):
    return conversation.procesar(db, datos.mensaje, datos.session_id, imagen=datos.imagen)


# ---------- Analítica de IA (Azure AI Foundry) ----------
@app.get("/api/ia/estadisticas", response_model=schemas.IAEstadisticas)
def ia_estadisticas(db: Session = Depends(get_db)):
    return analitica.estadisticas_ia(db)
