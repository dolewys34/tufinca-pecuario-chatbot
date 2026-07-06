# 📋 Avance del proyecto — TuFinca Pecuario + Chatbot IA

> Bitácora viva del desarrollo. Se actualiza en cada iteración para poder **retomar el trabajo** en cualquier momento.

**Última actualización:** 2026-07-06

---

## 1. Estado general

| Componente | Estado | Tecnología |
|------------|--------|------------|
| Base de datos | ✅ Funcional | SQLite + SQLAlchemy (migrable a PostgreSQL) |
| API backend | ✅ Funcional | FastAPI |
| Módulo pecuario | ✅ Ampliado | Animales, salud/vacunación, alimentación, costos |
| Chatbot | ✅ Funcional | Azure AI Foundry + motor de reglas de respaldo |
| Estadísticas gráficas en chat | ✅ Funcional | Gráficos de barras dentro del chat |
| Interfaz web | ✅ Funcional | React + Vite + TypeScript |
| Pruebas | ✅ 6/6 pasan | pytest |
| Integración WhatsApp | ⏳ Pendiente | (siguiente fase) |
| Despliegue producción | ⏳ Pendiente | (siguiente fase) |

---

## 2. Cómo ejecutar el proyecto

### Requisitos
- Python 3.13 (el `.venv` ya está creado con esta versión)
- Node.js 18+ (probado con Node 24)

### A) Backend (API + IA)

```bash
cd "DESARROLLO UNIVERSIDAD"
source .venv/bin/activate
pip install -r requirements.txt      # solo la primera vez
python -m src.seed                   # carga datos de demostración (opcional)
uvicorn src.app.api:app --reload     # arranca la API en http://localhost:8000
```

- API: http://localhost:8000
- Documentación interactiva (Swagger): http://localhost:8000/docs

### B) Frontend (interfaz web)

```bash
cd frontend
npm install        # solo la primera vez
npm run dev        # arranca en http://localhost:5173
```

Abre **http://localhost:5173** en el navegador. El frontend habla con el backend
mediante un proxy (`/api` → puerto 8000).

### C) Pruebas

```bash
source .venv/bin/activate
python -m pytest -q
```

---

## 3. Estructura del proyecto

```text
DESARROLLO UNIVERSIDAD/
├── src/                          # Backend Python
│   ├── config.py                 # Configuración (lee .env, credenciales Azure)
│   ├── database.py               # Conexión SQLAlchemy
│   ├── models.py                 # Tablas reales Countryland: Especie, Raza, Lote, Animal, ProcesoPecuario, TipoVacunacion, DetalleAnimal
│   ├── schemas.py                # Validación Pydantic (incluye gráficos)
│   ├── seed.py                   # Datos de demostración
│   ├── app/
│   │   ├── api.py                # ★ API FastAPI (endpoints REST)
│   │   └── main.py               # Demo por consola (versión original)
│   └── modules/
│       ├── pecuario/
│       │   ├── animales.py       # Clase original (compatibilidad)
│       │   └── service.py        # ★ Lógica de negocio + estadísticas
│       └── chatbot/
│           ├── bot.py            # Motor de reglas (respaldo)
│           └── ai_service.py     # ★ Integración Azure AI Foundry + gráficos
├── frontend/                     # Interfaz React
│   └── src/
│       ├── App.tsx               # Layout + navegación
│       ├── api.ts                # Cliente HTTP
│       ├── types.ts              # Tipos TypeScript
│       ├── index.css             # Sistema de diseño (paleta agropecuaria)
│       └── components/
│           ├── DashboardView.tsx # Panel con KPIs y gráficos
│           ├── InventarioView.tsx# Tabla + formulario de animales
│           ├── ChatWidget.tsx    # Chat flotante
│           └── MiniGrafico.tsx   # Gráfico de barras del chat
├── tests/                        # Pruebas pytest
├── .env.example                  # Plantilla de configuración
├── requirements.txt
├── README.md
└── AVANCE.md                     # (este archivo)
```

---

## 4. Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Estado + motor de IA activo |
| GET | `/api/dashboard` | Indicadores de la finca |
| GET | `/api/animales` | Listar animales (filtro `?lote=`) |
| POST | `/api/animales` | Crear animal |
| GET | `/api/animales/{id}` | Detalle |
| PATCH | `/api/animales/{id}` | Actualizar (peso, lote, estado) |
| DELETE | `/api/animales/{id}` | Eliminar |
| POST | `/api/animales/{id}/salud` | Registrar vacuna/evento de salud |
| POST | `/api/animales/{id}/alimentacion` | Registrar alimentación |
| POST | `/api/chat` | Chatbot (devuelve texto + gráficos) |

---

## 5. Conectar la IA (Azure AI Foundry)

El chatbot funciona **sin credenciales** usando un motor de reglas. Para activar
la IA real:

1. En [Azure AI Foundry](https://ai.azure.com) crea un recurso y **despliega un
   modelo** (por ejemplo `gpt-4o-mini`).
2. Copia `.env.example` a `.env` y completa:
   ```
   AZURE_OPENAI_ENDPOINT=https://TU-RECURSO.openai.azure.com
   AZURE_OPENAI_API_KEY=tu-clave
   AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
   ```
3. Reinicia el backend. En la interfaz el indicador pasa de
   "⚙️ IA en modo reglas" a "⚡ IA activa".

> El chatbot recibe automáticamente un **resumen en vivo de la finca** (inventario,
> costos, vacunas próximas), por lo que responde con datos reales, no genéricos.
> Ver `src/modules/chatbot/ai_service.py`.

---

## 6. Historial de cambios

### Iteración 6 — 2026-07-06 (Panel de IA / analítica de Foundry en la app)
- **Nueva vista "🤖 Panel de IA"**: muestra el consumo del modelo de Azure AI
  Foundry en tiempo real (consultas, tokens de entrada/salida, costo estimado y
  gráfico de tokens por día). Se actualiza cada 10 s.
- **Tabla de apoyo `Uso_IA`**: registra los tokens de cada consulta al modelo
  (capturados de `response.usage`). La analítica es inmediata, sin la demora de
  las métricas de Azure Monitor.
- Endpoint nuevo: `/api/ia/estadisticas`.
- Nota: la analítica *oficial* de facturación sigue en el portal de Azure
  (Cost Management / Metrics del recurso `tufinca-foundry-19888`).

### Iteración 5 — 2026-07-06 (IA de Azure conectada + integración final)
- **Azure AI Foundry conectado y funcional**: recurso `tufinca-foundry-19888`,
  modelo **gpt-4.1-mini** (GlobalStandard). El agente responde con datos reales
  (`motor: azure-ai-foundry`).
- **Contexto de datos enriquecido** (`ai_service.py`): ahora se inyecta al modelo
  el listado real de animales e insumos (acotado), para responder preguntas
  específicas ("¿cuál es mi animal más valioso?", "¿qué insumo tiene menos stock?").
- **Script `scripts/azure_setup.sh`**: automatiza por Azure CLI la creación del
  recurso, el despliegue del modelo y la generación del `.env`.
- **Arranque con un comando**: `start.sh` (levanta backend + frontend + siembra BD)
  y `stop.sh` (detiene todo).
- El agente queda integrado: menús con botones + flujos que escriben en la BD +
  IA de Azure para texto libre + estadísticas gráficas.

### Iteración 4 — 2026-07-06 (módulo pecuario completo + validación de la BD)
Tras **validar campo por campo el dump real** (`Tufinca.sql` = base `Countryland`,
**45 tablas**), se completó el módulo pecuario al 100%:

- **Nuevas tablas mapeadas**: `Productos`, `Mano_Obra`, `Unidades`, `Marca`, `Inventarios`.
- **Campos contables añadidos** (`Cuenta_Debito_Id`, `Cuenta_Credito_Id`) a
  `Animales`, `Detalle_Animal`, `Lotes`, `Procesos_Pecuarios`.
- `Detalle_Animal` ahora enlaza por FK real a `Productos` y `Mano_Obra`.
- Nuevos endpoints: `/api/productos` (GET/POST), `/api/unidades`, `/api/marcas`.
- **Nueva vista "📦 Insumos"** en el frontend: productos + stock + registro,
  con KPIs (total productos, unidades en inventario, stock bajo).
- Seed ampliado con unidades, marcas, 5 productos e inventario.

> **Módulos aún NO implementados** (existen en la base real): contabilidad
> (Cuentas, Movimientos), usuarios/roles (Usuarios, Roles, AspNet*), empresa
> (Empresas, Certificaciones), agrícola (Cultivo, Variedad, Procesos_Agricolas…),
> maquinaria y turismo (Actividades, Reservas, Encuestas). Ver validación completa.

### Iteración 3 — 2026-07-06 (chatbot conversacional e interactivo)
- **Chatbot interactivo con botones de opciones** (`src/modules/chatbot/conversation.py`):
  menú principal + respuestas rápidas. El estado se guarda por `session_id`.
- **Flujos guiados que escriben en la base de datos**:
  · *Registrar animal* (nombre → especie → raza → valor → confirmar).
  · *Registrar vacunación* (animal → tipo → costo → confirmar).
- El chat combina: menús deterministas + IA/reglas para lenguaje libre + gráficos.
- Nuevos campos en el chat: `opciones` (botones) y `session_id`.
- Datos de demostración ampliados: 12 animales, 6 especies, 8 razas, 5 procesos, 5 tipos de vacuna.

### Iteración 2 — 2026-07-06 (alineación con la base real Countryland)
Se recibió el dump real de SQL Server **`Tufinca.sql`** (base `Countryland`) y se
**remapearon todos los modelos** a su esquema real:

- **Nuevas tablas/campos reales** (nombres originales del esquema): `Especies`,
  `Razas`, `Lotes`, `Animales`, `Procesos_Pecuarios`, `Tipo_Vacunacion`, `Detalle_Animal`.
- `Animales`: `Id_Animal`, `Animal`, `Especie_Id` (FK), `Raza_Id` (FK), `Avaluo`,
  `Valor`, `Costo`, `Fecha_Inicio/Fin`, `Estado` ('A'/'I'), `Codigo`, `Observaciones`.
- `Detalle_Animal`: eventos por animal (proceso pecuario, vacunación, producto,
  mano de obra) con `Costo`, `Valor`, etc.
- **Diferencias frente a la v1**: el esquema real **no guarda peso, sexo ni lote**
  en el animal; usa **catálogos** (Especie/Raza) y **valores contables**
  (avalúo/valor/costo).
- Nuevos endpoints de catálogo: `/api/especies`, `/api/razas`,
  `/api/procesos-pecuarios`, `/api/tipos-vacunacion`, `/api/lotes`.
- Dashboard actualizado: por especie, por raza, avalúo/valor/costo totales,
  vacunaciones. El formulario de inventario ahora usa selectores de especie y raza.
- Chatbot y sus gráficos actualizados (por especie, por raza, costos por proceso).
- `python -m src.seed` carga catálogos + 6 animales de ejemplo con los campos reales.

> El dump original está en `~/Downloads/Tufinca.sql` (no se incluye en el repo).

### Iteración 1 — 2026-07-06 (base funcional)
- ✅ Reparado el entorno virtual (estaba corrupto: pip 3.13 / python 3.9). Recreado con Python 3.13.
- ✅ Capa de base de datos con SQLAlchemy (SQLite).
- ✅ Modelo pecuario ampliado: animales, salud/vacunación, alimentación y costos.
- ✅ API REST con FastAPI (CRUD de animales, dashboard, chat, salud, alimentación).
- ✅ Servicio de chatbot conectado a Azure AI Foundry con respaldo por reglas.
- ✅ Interfaz web profesional en React (dashboard con KPIs, inventario, chat flotante).
- ✅ **Chatbot con estadísticas gráficas**: responde preguntas mostrando gráficos de
  barras (por especie, por lote, por costos) dentro del chat.
- ✅ 6 pruebas automatizadas (pytest) en verde.
- ✅ Datos de demostración (`python -m src.seed`).

---

## 7. Próximos pasos sugeridos (roadmap)

- [ ] **Fichas de animal**: vista detalle con su historial de salud y alimentación.
- [ ] **Reportes exportables** (PDF/Excel) de inventario y costos.
- [ ] **Alertas de vacunación**: notificaciones de las vacunas próximas.
- [ ] **Autenticación** de usuarios (productor / administrador).
- [ ] **Integración con WhatsApp** (objetivo del proyecto) vía WhatsApp Cloud API,
      reutilizando el mismo endpoint `/api/chat`.
- [ ] **Despliegue en producción**: contenedores Docker + PostgreSQL + Azure App Service.
- [ ] Migraciones de base de datos con Alembic.
```
