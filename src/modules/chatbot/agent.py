"""Agente inteligente con herramientas (function calling) sobre Azure AI Foundry.

A diferencia de una respuesta "de un tiro", el agente puede DECIDIR llamar a
herramientas para buscar información real en la base de datos o para registrar
datos, y luego razonar sobre los resultados. Esto lo hace verdaderamente
interactivo y basado en datos.

Flujo (bucle de razonamiento):
  usuario → modelo → (¿pide una herramienta?) → ejecuta en la BD → devuelve el
  resultado al modelo → ... → respuesta final en lenguaje natural.
"""
from __future__ import annotations

import difflib
import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src import models, schemas
from src.config import settings
from src.models import ESTADO_ACTIVO
from src.modules.chatbot import ai_service
from src.modules.pecuario import service

MAX_ITERACIONES = 5

SYSTEM_PROMPT = """Eres "TuFinca Bot", asistente agropecuario experto de la finca El Paraíso
(Anzoátegui, Tolima, Colombia). Ayudas al productor a gestionar y ANALIZAR su
información pecuaria: inventario animal, insumos, vacunación y costos.

Cómo trabajas:
- Tienes HERRAMIENTAS para consultar y registrar datos reales. Úsalas siempre que
  necesites cifras o listados concretos; NUNCA inventes datos.
- Usa cada herramienta SOLO para su propósito exacto. Si el usuario pide una
  acción para la que NO tienes herramienta, dilo con honestidad y sugiere cómo
  hacerlo; NUNCA uses una herramienta distinta para aparentar que lo hiciste.
- Puedes encadenar varias herramientas para responder (p. ej. buscar animales y
  luego analizarlos).
- Cuando el usuario pida registrar o actualizar algo, hazlo con la herramienta
  correcta y confirma el resultado real que devolvió.
- Da respuestas en español, claras y breves, útiles para un productor rural.
- Cuando sea útil, ofrece un análisis o recomendación corta basada en los datos.
"""

# ---------------------------------------------------------------------------
# Definición de herramientas (formato OpenAI / Azure)
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "resumen_finca",
            "description": "Resumen general de la finca: total de animales, por especie, por raza, avalúo/valor/costo totales y vacunaciones registradas.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_animales",
            "description": "Busca y filtra animales del inventario. Útil para responder '¿cuál es el más caro?', '¿qué bovinos tengo?', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "especie": {"type": "string", "description": "Filtrar por especie (ej: Bovino)"},
                    "raza": {"type": "string", "description": "Filtrar por raza"},
                    "ordenar_por": {"type": "string", "enum": ["valor", "avaluo", "costo"], "description": "Campo por el que ordenar"},
                    "descendente": {"type": "boolean", "description": "true = de mayor a menor"},
                    "limite": {"type": "integer", "description": "Máximo de resultados (por defecto 20)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_inventario",
            "description": "Lista los insumos (productos) con su valor y stock disponible. Útil para saber qué falta o qué hay.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_animal",
            "description": "Registra un nuevo animal en la base de datos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre o identificación del animal"},
                    "especie": {"type": "string", "description": "Especie (ej: Bovino)"},
                    "raza": {"type": "string", "description": "Raza (ej: Brahman)"},
                    "valor": {"type": "number", "description": "Valor comercial en pesos (opcional)"},
                    "codigo": {"type": "string", "description": "Código/arete (opcional)"},
                },
                "required": ["nombre", "especie", "raza"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_vacunacion",
            "description": "Registra una vacunación para un animal existente (por su código o nombre).",
            "parameters": {
                "type": "object",
                "properties": {
                    "animal": {"type": "string", "description": "Código o nombre del animal"},
                    "tipo_vacuna": {"type": "string", "description": "Tipo de vacuna (ej: Aftosa)"},
                    "costo": {"type": "number", "description": "Costo de la vacuna (opcional)"},
                },
                "required": ["animal", "tipo_vacuna"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_animal",
            "description": "Actualiza los datos de un animal existente: valor, avalúo, costo o estado (activo/inactivo). NO crea animales nuevos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "animal": {"type": "string", "description": "Código o nombre del animal a actualizar"},
                    "valor": {"type": "number", "description": "Nuevo valor comercial (opcional)"},
                    "avaluo": {"type": "number", "description": "Nuevo avalúo (opcional)"},
                    "costo": {"type": "number", "description": "Nuevo costo (opcional)"},
                    "estado": {"type": "string", "enum": ["activo", "inactivo"], "description": "Nuevo estado (opcional)"},
                },
                "required": ["animal"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_alimentacion",
            "description": "Registra un evento de alimentación para un animal (tipo de alimento, cantidad y costo). NO es una vacunación.",
            "parameters": {
                "type": "object",
                "properties": {
                    "animal": {"type": "string", "description": "Código o nombre del animal"},
                    "alimento": {"type": "string", "description": "Tipo de alimento (ej: concentrado, silo de maíz)"},
                    "cantidad_kg": {"type": "number", "description": "Cantidad en kilogramos (opcional)"},
                    "costo": {"type": "number", "description": "Costo en pesos (opcional)"},
                },
                "required": ["animal", "alimento"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "alertas_finca",
            "description": "Revisa las alertas pendientes de la finca: insumos agotados o con stock bajo y animales activos sin ninguna vacunación registrada.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "historial_animal",
            "description": "Historial de eventos de un animal (vacunaciones, alimentación, procesos) con fechas y costos. Busca por código o nombre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "animal": {"type": "string", "description": "Código o nombre del animal"},
                },
                "required": ["animal"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generar_grafico",
            "description": "Genera un gráfico de barras para mostrarle al usuario. Úsalo cuando pida estadísticas o distribuciones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["especie", "raza", "costos"], "description": "Qué graficar"},
                },
                "required": ["tipo"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Ejecución de herramientas contra la base de datos
# ---------------------------------------------------------------------------
def _get_or_create(db: Session, modelo, campo: str, valor: str):
    """Busca en el catálogo con tolerancia a errores de tipeo, o crea el registro.

    Ej.: si el usuario escribe "Durok" y existe "Duroc", usa "Duroc" en vez de
    crear una raza duplicada.
    """
    existentes = {getattr(f, campo).lower(): f for f in db.scalars(select(modelo)).all()}
    buscado = valor.strip().lower()
    if buscado in existentes:
        return existentes[buscado]
    parecido = difflib.get_close_matches(buscado, list(existentes), n=1, cutoff=0.75)
    if parecido:
        return existentes[parecido[0]]
    nuevo = modelo(**{campo: valor.strip(), "Estado": ESTADO_ACTIVO})
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def _buscar_animal_por_ref(db: Session, ref: str):
    """Busca un animal por código o nombre (insensible a mayúsculas)."""
    ref = str(ref).strip().lower()
    return db.scalars(
        select(models.Animal).where(
            (func.lower(models.Animal.Codigo) == ref) | (func.lower(models.Animal.Animal) == ref)
        )
    ).first()


def _ejecutar_tool(db: Session, nombre: str, args: dict):
    """Ejecuta una herramienta. Devuelve (resultado_dict, grafico_o_None)."""
    if nombre == "resumen_finca":
        d = service.construir_dashboard(db)
        return d.model_dump(), None

    if nombre == "buscar_animales":
        stmt = select(models.Animal)
        animales = list(db.scalars(stmt).all())
        if args.get("especie"):
            animales = [a for a in animales if a.especie and args["especie"].lower() in a.especie.Especie.lower()]
        if args.get("raza"):
            animales = [a for a in animales if a.raza and args["raza"].lower() in a.raza.Raza.lower()]
        campo = {"valor": "Valor", "avaluo": "Avaluo", "costo": "Costo"}.get(args.get("ordenar_por", ""))
        if campo:
            animales.sort(key=lambda a: getattr(a, campo) or 0, reverse=bool(args.get("descendente", True)))
        limite = int(args.get("limite", 20))
        datos = [
            {
                "codigo": a.Codigo, "nombre": a.Animal,
                "especie": a.especie.Especie if a.especie else None,
                "raza": a.raza.Raza if a.raza else None,
                "avaluo": a.Avaluo, "valor": a.Valor, "costo": a.Costo,
                "estado": "activo" if a.Estado == ESTADO_ACTIVO else "inactivo",
            }
            for a in animales[:limite]
        ]
        return {"cantidad": len(datos), "animales": datos}, None

    if nombre == "consultar_inventario":
        productos = service.listar_productos(db)
        datos = [
            {"producto": p.Producto, "marca": p.marca_nombre, "valor": p.Valor, "stock": p.stock}
            for p in productos
        ]
        return {"cantidad": len(datos), "insumos": datos}, None

    if nombre == "registrar_animal":
        especie = _get_or_create(db, models.Especie, "Especie", args["especie"])
        raza = _get_or_create(db, models.Raza, "Raza", args["raza"])
        nuevo = service.crear_animal(db, schemas.AnimalCreate(
            Animal=args["nombre"], Especie_Id=especie.Id_Especie, Raza_Id=raza.Id_Raza,
            Codigo=args.get("codigo"), Valor=args.get("valor"),
        ))
        return {"ok": True, "id": nuevo.Id_Animal, "mensaje": f"Animal '{nuevo.Animal}' registrado."}, None

    if nombre == "registrar_vacunacion":
        ref = str(args["animal"]).lower()
        animal = db.scalars(
            select(models.Animal).where(
                (func.lower(models.Animal.Codigo) == ref) | (func.lower(models.Animal.Animal) == ref)
            )
        ).first()
        if not animal:
            return {"ok": False, "error": f"No encontré un animal con código o nombre '{args['animal']}'."}, None
        tipo = _get_or_create(db, models.TipoVacunacion, "Tipo_Vacunacion", args["tipo_vacuna"])
        proceso = db.scalars(
            select(models.ProcesoPecuario).where(models.ProcesoPecuario.Proceso_Pecuario == "Vacunación")
        ).first()
        if not proceso:
            proceso = models.ProcesoPecuario(Proceso_Pecuario="Vacunación", Estado=ESTADO_ACTIVO)
            db.add(proceso); db.commit(); db.refresh(proceso)
        service.agregar_detalle(db, animal, schemas.DetalleAnimalCreate(
            Proceso_Pecuario_Id=proceso.Id_Proceso_Pecuario,
            Tipo_Vacunacion_Id=tipo.id_Tipo_Vacunacion,
            Costo=args.get("costo"), Observaciones="Registrado por el agente IA",
        ))
        return {"ok": True, "mensaje": f"Vacunación de {tipo.Tipo_Vacunacion} registrada para {animal.Codigo or animal.Animal}."}, None

    if nombre == "actualizar_animal":
        animal = _buscar_animal_por_ref(db, args["animal"])
        if not animal:
            return {"ok": False, "error": f"No encontré un animal con código o nombre '{args['animal']}'."}, None
        cambios = {}
        if args.get("valor") is not None:
            cambios["Valor"] = args["valor"]
        if args.get("avaluo") is not None:
            cambios["Avaluo"] = args["avaluo"]
        if args.get("costo") is not None:
            cambios["Costo"] = args["costo"]
        if args.get("estado"):
            cambios["Estado"] = "A" if args["estado"] == "activo" else "I"
        if not cambios:
            return {"ok": False, "error": "No indicaste qué campo actualizar (valor, avalúo, costo o estado)."}, None
        service.actualizar_animal(db, animal, schemas.AnimalUpdate(**cambios))
        return {"ok": True, "mensaje": f"Animal {animal.Codigo or animal.Animal} actualizado.", "cambios": cambios}, None

    if nombre == "registrar_alimentacion":
        animal = _buscar_animal_por_ref(db, args["animal"])
        if not animal:
            return {"ok": False, "error": f"No encontré un animal con código o nombre '{args['animal']}'."}, None
        proceso = _get_or_create(db, models.ProcesoPecuario, "Proceso_Pecuario", "Alimentación")
        detalle_obs = args["alimento"]
        if args.get("cantidad_kg"):
            detalle_obs += f" ({args['cantidad_kg']} kg)"
        service.agregar_detalle(db, animal, schemas.DetalleAnimalCreate(
            Proceso_Pecuario_Id=proceso.Id_Proceso_Pecuario,
            Costo=args.get("costo"),
            Observaciones=detalle_obs,
        ))
        return {"ok": True, "mensaje": f"Alimentación '{detalle_obs}' registrada para {animal.Codigo or animal.Animal}."}, None

    if nombre == "alertas_finca":
        alertas = []
        for p in service.listar_productos(db):
            if p.stock == 0:
                alertas.append({"tipo": "insumo_agotado", "detalle": f"{p.Producto}: sin stock"})
            elif p.stock <= 10:
                alertas.append({"tipo": "stock_bajo", "detalle": f"{p.Producto}: quedan {p.stock}"})
        activos = [a for a in db.scalars(select(models.Animal)).all() if a.Estado == ESTADO_ACTIVO]
        sin_vacuna = [
            a for a in activos
            if not any(d.Tipo_Vacunacion_Id for d in a.detalles)
        ]
        for a in sin_vacuna:
            alertas.append({"tipo": "sin_vacunas", "detalle": f"{a.Codigo or a.Animal} no tiene vacunaciones registradas"})
        return {"total_alertas": len(alertas), "alertas": alertas}, None

    if nombre == "historial_animal":
        animal = _buscar_animal_por_ref(db, args["animal"])
        if not animal:
            return {"ok": False, "error": f"No encontré un animal con código o nombre '{args['animal']}'."}, None
        eventos = [
            {
                "proceso": d.proceso.Proceso_Pecuario if d.proceso else None,
                "vacuna": d.tipo_vacunacion.Tipo_Vacunacion if d.tipo_vacunacion else None,
                "producto": d.producto.Producto if d.producto else None,
                "costo": d.Costo,
                "fecha": d.Fecha_Inicio.strftime("%Y-%m-%d") if d.Fecha_Inicio else None,
                "observaciones": d.Observaciones,
            }
            for d in animal.detalles
        ]
        return {
            "animal": animal.Codigo or animal.Animal,
            "especie": animal.especie.Especie if animal.especie else None,
            "raza": animal.raza.Raza if animal.raza else None,
            "valor": animal.Valor,
            "eventos": eventos,
            "costo_eventos": sum(d.Costo or 0 for d in animal.detalles),
        }, None

    if nombre == "generar_grafico":
        stats = service.estadisticas(db)
        grafico = stats.get(args.get("tipo", "especie"))
        if grafico and grafico.datos:
            return {"ok": True, "titulo": grafico.titulo}, grafico
        return {"ok": False, "error": "Sin datos para graficar."}, None

    return {"error": f"Herramienta desconocida: {nombre}"}, None


# ---------------------------------------------------------------------------
# Bucle del agente
# ---------------------------------------------------------------------------
def responder_agente(
    db: Session, mensaje: str, historial: list[dict]
) -> tuple[str, list[str], list[schemas.Grafico]]:
    """Devuelve (respuesta, herramientas_usadas, graficos)."""
    from openai import AzureOpenAI

    client = AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(historial)
    messages.append({"role": "user", "content": mensaje})

    herramientas_usadas: list[str] = []
    graficos: list[schemas.Grafico] = []

    for _ in range(MAX_ITERACIONES):
        resp = client.chat.completions.create(
            model=settings.azure_openai_deployment,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=600,
        )
        ai_service._registrar_uso(db, resp.usage)
        msg = resp.choices[0].message

        if not msg.tool_calls:
            return (msg.content or "No pude generar una respuesta.", herramientas_usadas, graficos)

        # Registrar la decisión del modelo (mensaje del asistente con tool_calls)
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ],
        })

        # Ejecutar cada herramienta y devolver su resultado al modelo
        for tc in msg.tool_calls:
            nombre = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            herramientas_usadas.append(nombre)
            try:
                resultado, grafico = _ejecutar_tool(db, nombre, args)
            except Exception as exc:  # pragma: no cover
                resultado, grafico = {"error": str(exc)}, None
            if grafico:
                graficos.append(grafico)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(resultado, ensure_ascii=False, default=str),
            })

    return ("Consulté varias veces pero no logré cerrar la respuesta. Reformula la pregunta, por favor.",
            herramientas_usadas, graficos)
