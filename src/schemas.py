"""Esquemas Pydantic para validar entradas/salidas de la API.

Reflejan los campos reales del esquema Countryland (TuFinca).
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Catálogos ----------
class CatalogoOut(BaseModel):
    """Salida genérica id + nombre para catálogos (especies, razas, etc.)."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str


class LoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    Id_Lote: int
    Lote: str
    Area: float | None = None
    Sica: str | None = None
    Estado: str


# ---------- Insumos / productos ----------
class ProductoCreate(BaseModel):
    Producto: str = Field(..., min_length=1)
    Unidad_Id: int | None = None
    Marca_Id: int | None = None
    Valor: float | None = Field(default=None, ge=0)
    Codigo: str | None = None
    Observaciones: str | None = None


class ProductoOut(ProductoCreate):
    model_config = ConfigDict(from_attributes=True)
    Id_Producto: int
    Estado: str
    unidad_nombre: str | None = None
    marca_nombre: str | None = None
    stock: int = 0


# ---------- Animales ----------
class AnimalBase(BaseModel):
    Animal: str = Field(..., min_length=1, max_length=50)
    Especie_Id: int
    Raza_Id: int
    Codigo: str | None = Field(default=None, max_length=50)
    Avaluo: float | None = Field(default=None, ge=0)
    Valor: float | None = Field(default=None, ge=0)
    Costo: float | None = Field(default=None, ge=0)
    Observaciones: str | None = None


class AnimalCreate(AnimalBase):
    pass


class AnimalUpdate(BaseModel):
    Avaluo: float | None = Field(default=None, ge=0)
    Valor: float | None = Field(default=None, ge=0)
    Costo: float | None = Field(default=None, ge=0)
    Estado: str | None = Field(default=None, max_length=1)
    Observaciones: str | None = None


class AnimalOut(AnimalBase):
    model_config = ConfigDict(from_attributes=True)
    Id_Animal: int
    Estado: str
    Fecha_Inicio: datetime
    Fecha_Fin: datetime | None = None
    # Nombres resueltos desde los catálogos (para mostrar en la interfaz)
    especie_nombre: str | None = None
    raza_nombre: str | None = None


# ---------- Detalle de animal (eventos: vacunación, alimentación...) ----------
class DetalleAnimalCreate(BaseModel):
    Proceso_Pecuario_Id: int
    Tipo_Vacunacion_Id: int | None = None
    Producto_Id: int | None = None
    Mano_Obra_Id: int | None = None
    Valor: float | None = Field(default=None, ge=0)
    Costo: float | None = Field(default=None, ge=0)
    Observaciones: str | None = None


class DetalleAnimalOut(DetalleAnimalCreate):
    model_config = ConfigDict(from_attributes=True)
    Id_Detalle_Animal: int
    Animal_Id: int
    Estado: str
    Fecha_Inicio: datetime | None = None
    proceso_nombre: str | None = None
    tipo_vacunacion_nombre: str | None = None
    producto_nombre: str | None = None


# ---------- Dashboard ----------
class DashboardOut(BaseModel):
    total_animales: int
    total_activos: int
    por_especie: dict[str, int]
    por_raza: dict[str, int]
    avaluo_total: float
    valor_total: float
    costo_total: float
    vacunaciones: int


# ---------- Estadísticas / gráficos ----------
class PuntoGrafico(BaseModel):
    etiqueta: str
    valor: float


class Grafico(BaseModel):
    titulo: str
    tipo: str = "barras"          # barras | dona
    unidad: str = ""              # "animales", "$"...
    datos: list[PuntoGrafico]


# ---------- Alertas ----------
class Alerta(BaseModel):
    tipo: str      # insumo_agotado | stock_bajo | sin_vacunas
    detalle: str


# ---------- Analítica de IA (Azure AI Foundry) ----------
class PuntoUsoDia(BaseModel):
    fecha: str
    tokens: int
    llamadas: int


class IAEstadisticas(BaseModel):
    conectado: bool
    modelo: str
    endpoint: str                 # solo el host, sin la clave
    total_llamadas: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    costo_estimado_usd: float
    por_dia: list[PuntoUsoDia]


# ---------- Chatbot ----------
class OpcionChat(BaseModel):
    """Botón de respuesta rápida que el usuario puede pulsar."""
    texto: str          # lo que ve el usuario
    valor: str          # lo que se envía al pulsarlo


class ChatRequest(BaseModel):
    mensaje: str = Field(..., min_length=1)
    session_id: str = "default"
    # Foto opcional (data URL base64, ej. "data:image/jpeg;base64,..."). El
    # agente la analiza con la visión de gpt-4.1-mini.
    imagen: str | None = None


class ChatResponse(BaseModel):
    respuesta: str
    motor: str  # "azure-ai-foundry" | "reglas" | "asistente"
    graficos: list[Grafico] = []
    opciones: list[OpcionChat] = []
    herramientas: list[str] = []   # herramientas que usó el agente (transparencia)
