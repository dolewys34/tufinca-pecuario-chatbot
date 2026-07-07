"""Motor conversacional interactivo del chatbot TuFinca.

Aporta la "inteligencia" de interacción:
- Menús con **botones de opciones** (respuestas rápidas).
- **Flujos guiados** que registran datos reales en la base de datos:
  · Registrar un animal (nombre → especie → raza → valor → confirmar).
  · Registrar una vacunación (animal → tipo → costo → confirmar).
- Delega las preguntas en lenguaje libre al motor de IA / reglas.

El estado de cada conversación se guarda en memoria por `session_id`.
Para producción se recomienda moverlo a Redis o a la base de datos.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src import models, schemas
from src.config import settings
from src.models import ESTADO_ACTIVO
from src.modules.chatbot import agent, ai_service, analitica
from src.modules.pecuario import service

# Estado en memoria por sesión:
#   {"flujo": str, "paso": str, "datos": dict, "historial": list[dict]}
_SESIONES: dict[str, dict] = {}

# Turnos de conversación que se recuerdan (para dar contexto al agente).
_MAX_HISTORIAL = 8

Opcion = schemas.OpcionChat


def _historial(session_id: str) -> list[dict]:
    return _SESIONES.setdefault(session_id, {}).get("historial", [])


def _recordar(session_id: str, rol: str, contenido: str) -> None:
    # Evita crecimiento sin límite: si hay demasiadas sesiones, purgamos las
    # más antiguas (dict conserva orden de inserción).
    if len(_SESIONES) > 500 and session_id not in _SESIONES:
        for viejo in list(_SESIONES)[:100]:
            _SESIONES.pop(viejo, None)
    s = _SESIONES.setdefault(session_id, {})
    hist = s.setdefault("historial", [])
    hist.append({"role": rol, "content": contenido})
    # Conservamos solo los últimos turnos.
    del hist[:-_MAX_HISTORIAL]


def _menu_opciones() -> list[Opcion]:
    return [
        Opcion(texto="📊 Ver estadísticas", valor="__stats"),
        Opcion(texto="🐄 Registrar animal", valor="__nuevo_animal"),
        Opcion(texto="💉 Registrar vacunación", valor="__nueva_vacuna"),
        Opcion(texto="📋 Consultar inventario", valor="__inventario"),
    ]


def _respuesta(
    texto: str,
    *,
    opciones: list[Opcion] | None = None,
    graficos: list[schemas.Grafico] | None = None,
    motor: str = "asistente",
    herramientas: list[str] | None = None,
) -> schemas.ChatResponse:
    return schemas.ChatResponse(
        respuesta=texto,
        motor=motor,
        graficos=graficos or [],
        opciones=opciones or [],
        herramientas=herramientas or [],
    )


def _num(texto: str) -> float | None:
    limpio = texto.replace("$", "").replace(".", "").replace(",", "").strip()
    try:
        return float(limpio)
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Punto de entrada
# --------------------------------------------------------------------------
def procesar(
    db: Session, mensaje: str, session_id: str, imagen: str | None = None
) -> schemas.ChatResponse:
    texto = mensaje.strip()
    sesion = _SESIONES.get(session_id)

    # Foto adjunta → directo al agente con visión (requiere Azure activo).
    if imagen:
        if not settings.azure_enabled:
            return _respuesta(
                "Para analizar fotos necesito el motor de IA (Azure AI Foundry) activo.",
                opciones=_menu_opciones(),
            )
        try:
            historial = list(_historial(session_id))
            respuesta, herramientas, graficos = agent.responder_agente(
                db, texto or "Analiza esta imagen", historial, imagen=imagen
            )
            _recordar(session_id, "user", f"{texto} [envió una foto]")
            _recordar(session_id, "assistant", respuesta)
            return _respuesta(
                respuesta, motor="azure-ai-foundry", graficos=graficos,
                herramientas=herramientas, opciones=_menu_opciones(),
            )
        except Exception:
            return _respuesta(
                "No pude analizar la imagen en este momento. Intenta de nuevo.",
                opciones=_menu_opciones(),
            )

    # 1) ¿Hay un flujo guiado activo? Tiene prioridad.
    if sesion and sesion.get("flujo"):
        return _continuar_flujo(db, texto, session_id, sesion)

    # 2) Comandos exactos de los BOTONES del menú (los inicia el usuario al pulsar).
    bajo = texto.lower()
    if texto in ("__menu", "__cancelar") or bajo in ("menu", "menú", "inicio"):
        return _menu(db)
    if texto == "__stats":
        return _mostrar_stats(db)
    if texto == "__inventario":
        return _mostrar_inventario(db)
    if texto == "__nuevo_animal":
        return _iniciar_registro_animal(db, session_id)
    if texto == "__nueva_vacuna":
        return _iniciar_registro_vacuna(db, session_id)

    # 3) Saludo simple → menú de bienvenida.
    if bajo in ("hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "hey"):
        return _menu(db)

    # 4) Todo lo demás (texto libre) → AGENTE con herramientas (si Azure está activo).
    if settings.azure_enabled and analitica.limite_diario_alcanzado(db):
        # Tope diario de tokens alcanzado: respondemos con reglas (sin costo).
        respuesta = ai_service.Chatbot().responder(texto)
        graficos = ai_service._detectar_graficos(db, texto)
        return _respuesta(
            f"{respuesta}\n\n⚠️ Nota: se alcanzó el límite diario de consultas de IA "
            "(control de costos). El asistente inteligente vuelve mañana.",
            motor="reglas", graficos=graficos, opciones=_menu_opciones(),
        )
    if settings.azure_enabled:
        try:
            historial = list(_historial(session_id))
            respuesta, herramientas, graficos = agent.responder_agente(db, texto, historial)
            _recordar(session_id, "user", texto)
            _recordar(session_id, "assistant", respuesta)
            return _respuesta(
                respuesta, motor="azure-ai-foundry", graficos=graficos,
                herramientas=herramientas, opciones=_menu_opciones(),
            )
        except Exception:
            # Si Azure falla (red, cuota, servicio), degradamos al motor de
            # reglas en vez de devolver un error 500 al usuario.
            pass

    # 5) Sin Azure → motor de reglas de respaldo.
    respuesta, motor, graficos = ai_service.responder(db, texto)
    return _respuesta(respuesta, motor=motor, graficos=graficos, opciones=_menu_opciones())


# --------------------------------------------------------------------------
# Menú e informativos
# --------------------------------------------------------------------------
def _menu(db: Session) -> schemas.ChatResponse:
    d = service.construir_dashboard(db)
    texto = (
        "¡Hola! Soy **TuFinca Bot** 🐄. ¿En qué te ayudo hoy?\n\n"
        f"Tu finca tiene **{d.total_animales} animales** registrados. "
        "Elige una opción o escríbeme tu pregunta."
    )
    return _respuesta(texto, opciones=_menu_opciones())


def _mostrar_stats(db: Session) -> schemas.ChatResponse:
    stats = service.estadisticas(db)
    graficos = [g for g in (stats["especie"], stats["raza"], stats["costos"]) if g.datos]
    return _respuesta(
        "Aquí tienes el resumen gráfico de tu finca 👇",
        graficos=graficos,
        opciones=_menu_opciones(),
    )


def _mostrar_inventario(db: Session) -> schemas.ChatResponse:
    d = service.construir_dashboard(db)
    especies = ", ".join(f"{k} ({v})" for k, v in d.por_especie.items()) or "sin registros"
    texto = (
        f"📋 **Inventario actual**\n"
        f"• Total: {d.total_animales} animales ({d.total_activos} activos)\n"
        f"• Por especie: {especies}\n"
        f"• Valor total del hato: ${d.valor_total:,.0f}\n"
        f"• Vacunaciones registradas: {d.vacunaciones}"
    )
    return _respuesta(
        texto,
        opciones=[Opcion(texto="📊 Ver gráficos", valor="__stats"), *_menu_opciones()],
    )


# --------------------------------------------------------------------------
# Flujo: registrar animal
# --------------------------------------------------------------------------
def _iniciar_registro_animal(db: Session, session_id: str) -> schemas.ChatResponse:
    _SESIONES[session_id] = {"flujo": "animal", "paso": "nombre", "datos": {}}
    return _respuesta(
        "Vamos a registrar un nuevo animal 🐄.\n¿Cuál es su **nombre o identificación**? (ej: Vaca 007)",
        opciones=[Opcion(texto="❌ Cancelar", valor="__cancelar")],
    )


def _iniciar_registro_vacuna(db: Session, session_id: str) -> schemas.ChatResponse:
    animales = list(db.scalars(select(models.Animal)).all())
    if not animales:
        return _respuesta(
            "Aún no tienes animales registrados. Primero registra uno.",
            opciones=[Opcion(texto="🐄 Registrar animal", valor="__nuevo_animal")],
        )
    _SESIONES[session_id] = {"flujo": "vacuna", "paso": "animal", "datos": {}}
    opciones = [
        Opcion(texto=f"{a.Codigo or a.Animal}", valor=f"__animal:{a.Id_Animal}")
        for a in animales[:8]
    ]
    opciones.append(Opcion(texto="❌ Cancelar", valor="__cancelar"))
    return _respuesta("💉 ¿A cuál animal deseas registrarle la vacunación?", opciones=opciones)


def _continuar_flujo(
    db: Session, texto: str, session_id: str, sesion: dict
) -> schemas.ChatResponse:
    if texto == "__cancelar":
        _SESIONES.pop(session_id, None)
        return _respuesta("Operación cancelada. ¿Algo más?", opciones=_menu_opciones())

    if sesion["flujo"] == "animal":
        return _flujo_animal(db, texto, session_id, sesion)
    if sesion["flujo"] == "vacuna":
        return _flujo_vacuna(db, texto, session_id, sesion)
    _SESIONES.pop(session_id, None)
    return _menu(db)


def _flujo_animal(db, texto, session_id, sesion) -> schemas.ChatResponse:
    paso, datos = sesion["paso"], sesion["datos"]

    if paso == "nombre":
        datos["Animal"] = texto
        sesion["paso"] = "especie"
        especies = service.listar_especies(db)
        opciones = [Opcion(texto=e.nombre, valor=f"__esp:{e.id}") for e in especies]
        opciones.append(Opcion(texto="❌ Cancelar", valor="__cancelar"))
        return _respuesta(f"Perfecto, **{texto}**. ¿Qué **especie** es?", opciones=opciones)

    if paso == "especie":
        if not texto.startswith("__esp:"):
            return _respuesta("Por favor elige una especie de la lista 👇",
                              opciones=[Opcion(texto=e.nombre, valor=f"__esp:{e.id}")
                                        for e in service.listar_especies(db)])
        datos["Especie_Id"] = int(texto.split(":")[1])
        sesion["paso"] = "raza"
        razas = service.listar_razas(db)
        opciones = [Opcion(texto=r.nombre, valor=f"__raza:{r.id}") for r in razas]
        opciones.append(Opcion(texto="❌ Cancelar", valor="__cancelar"))
        return _respuesta("¿Y de qué **raza**?", opciones=opciones)

    if paso == "raza":
        if not texto.startswith("__raza:"):
            return _respuesta("Elige una raza de la lista 👇",
                              opciones=[Opcion(texto=r.nombre, valor=f"__raza:{r.id}")
                                        for r in service.listar_razas(db)])
        datos["Raza_Id"] = int(texto.split(":")[1])
        sesion["paso"] = "valor"
        return _respuesta(
            "¿Cuál es su **valor comercial** aproximado en pesos? (ej: 2500000)",
            opciones=[Opcion(texto="Omitir", valor="__omitir"),
                      Opcion(texto="❌ Cancelar", valor="__cancelar")],
        )

    if paso == "valor":
        datos["Valor"] = None if texto == "__omitir" else _num(texto)
        sesion["paso"] = "confirmar"
        esp = next((e.nombre for e in service.listar_especies(db) if e.id == datos["Especie_Id"]), "?")
        raza = next((r.nombre for r in service.listar_razas(db) if r.id == datos["Raza_Id"]), "?")
        val = f"${datos['Valor']:,.0f}" if datos.get("Valor") else "sin valor"
        return _respuesta(
            f"Voy a registrar:\n• **{datos['Animal']}**\n• Especie: {esp}\n• Raza: {raza}\n• Valor: {val}\n\n¿Confirmas?",
            opciones=[Opcion(texto="✅ Guardar", valor="__confirmar"),
                      Opcion(texto="❌ Cancelar", valor="__cancelar")],
        )

    if paso == "confirmar" and texto == "__confirmar":
        nuevo = service.crear_animal(db, schemas.AnimalCreate(
            Animal=datos["Animal"],
            Especie_Id=datos["Especie_Id"],
            Raza_Id=datos["Raza_Id"],
            Valor=datos.get("Valor"),
        ))
        _SESIONES.pop(session_id, None)
        return _respuesta(
            f"✅ ¡Listo! **{nuevo.Animal}** quedó registrado (código interno #{nuevo.Id_Animal}). ¿Algo más?",
            opciones=_menu_opciones(),
        )

    # fallback
    _SESIONES.pop(session_id, None)
    return _menu(db)


def _flujo_vacuna(db, texto, session_id, sesion) -> schemas.ChatResponse:
    paso, datos = sesion["paso"], sesion["datos"]

    if paso == "animal":
        if not texto.startswith("__animal:"):
            return _respuesta("Elige el animal de la lista 👇")
        datos["Animal_Id"] = int(texto.split(":")[1])
        sesion["paso"] = "tipo"
        tipos = service.listar_tipos_vacunacion(db)
        opciones = [Opcion(texto=t.nombre, valor=f"__tipovac:{t.id}") for t in tipos]
        opciones.append(Opcion(texto="❌ Cancelar", valor="__cancelar"))
        return _respuesta("¿Qué **tipo de vacuna** se aplicó?", opciones=opciones)

    if paso == "tipo":
        if not texto.startswith("__tipovac:"):
            return _respuesta("Elige el tipo de vacuna 👇")
        datos["Tipo_Vacunacion_Id"] = int(texto.split(":")[1])
        sesion["paso"] = "responsable"
        return _respuesta(
            "¿Quién fue el **responsable** de aplicar la vacuna? (escribe el nombre)",
            opciones=[Opcion(texto="Omitir", valor="__omitir"),
                      Opcion(texto="❌ Cancelar", valor="__cancelar")],
        )

    if paso == "responsable":
        datos["Responsable"] = None if texto == "__omitir" else texto.strip()
        sesion["paso"] = "costo"
        return _respuesta(
            "¿Cuál fue el **costo** de la vacuna? (ej: 15000)",
            opciones=[Opcion(texto="Omitir", valor="__omitir"),
                      Opcion(texto="❌ Cancelar", valor="__cancelar")],
        )

    if paso == "costo":
        datos["Costo"] = None if texto == "__omitir" else _num(texto)
        proceso = _proceso_vacunacion(db)
        animal = service.obtener_animal(db, datos["Animal_Id"])
        service.agregar_detalle(db, animal, schemas.DetalleAnimalCreate(
            Proceso_Pecuario_Id=proceso.Id_Proceso_Pecuario,
            Tipo_Vacunacion_Id=datos["Tipo_Vacunacion_Id"],
            Costo=datos.get("Costo"),
            Responsable=datos.get("Responsable"),
            Observaciones="Registrado por el chatbot",
        ))
        _SESIONES.pop(session_id, None)
        tipo = next((t.nombre for t in service.listar_tipos_vacunacion(db)
                     if t.id == datos["Tipo_Vacunacion_Id"]), "vacuna")
        return _respuesta(
            f"✅ Vacunación de **{tipo}** registrada para {animal.Codigo or animal.Animal}. ¿Algo más?",
            opciones=_menu_opciones(),
        )

    _SESIONES.pop(session_id, None)
    return _menu(db)


def _proceso_vacunacion(db: Session) -> models.ProcesoPecuario:
    """Busca (o crea) el proceso pecuario 'Vacunación'."""
    proceso = db.scalar(
        select(models.ProcesoPecuario).where(
            models.ProcesoPecuario.Proceso_Pecuario == "Vacunación"
        )
    )
    if not proceso:
        proceso = models.ProcesoPecuario(Proceso_Pecuario="Vacunación", Estado=ESTADO_ACTIVO)
        db.add(proceso)
        db.commit()
        db.refresh(proceso)
    return proceso
