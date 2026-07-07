# 🌾 TuFinca Pecuario + Chatbot IA

> 🌐 **Demo en la nube:** https://tufinca-paraiso-19888.azurewebsites.net

Sistema de información agropecuario para la finca **El Paraíso** (Anzoátegui, Tolima).
Gestiona el inventario animal, salud, alimentación y costos, e incluye un **chatbot
inteligente** conectado a **Azure AI Foundry** que responde con datos reales y
**estadísticas gráficas**.

![stack](https://img.shields.io/badge/backend-FastAPI-009688) ![stack](https://img.shields.io/badge/frontend-React-61dafb) ![stack](https://img.shields.io/badge/IA-Azure_AI_Foundry-0078d4)

## ✨ Funcionalidades

- 📊 **Panel de indicadores**: inventario, peso promedio, costos y alertas de vacunación.
- 🐄 **Inventario animal**: registro y consulta con especie, raza, lote, peso y estado.
- 💉 **Salud y alimentación**: eventos de vacunación y alimentación con costos.
- 💬 **Chatbot inteligente**: entiende lenguaje natural y responde con **gráficos** de
  la información real de la finca (por especie, lote y costos).
- ⚡ **IA con Azure AI Foundry** (con motor de respaldo por reglas si no hay credenciales).

## 🚀 Ejecución rápida (un solo comando)

```bash
bash start.sh     # levanta backend + frontend y siembra la BD
bash stop.sh      # detiene todo
```
Luego abre **http://localhost:5173**.

<details>
<summary>Arranque manual (paso a paso)</summary>

**Backend**
```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m src.seed                # datos de demostración
uvicorn src.app.api:app --reload  # http://localhost:8000
```
**Frontend**
```bash
cd frontend && npm install && npm run dev   # http://localhost:5173
```
</details>

## 🤖 Activar la IA (Azure AI Foundry)

```bash
az login                          # autenticación (con MFA)
bash scripts/azure_setup.sh       # crea el recurso, despliega el modelo y genera .env
```
El script crea el recurso de Azure AI Foundry, despliega **gpt-4.1-mini**, obtiene
el endpoint + la clave y los guarda en `.env`. Sin esto, el chatbot funciona en
modo reglas. El indicador de la app muestra "⚡ IA activa" cuando queda conectado.

## 📚 Documentación

- **[AVANCE.md](AVANCE.md)** — bitácora de desarrollo, estructura, endpoints y roadmap.
- **[.env.example](.env.example)** — cómo configurar Azure AI Foundry.
- Documentación interactiva de la API: http://localhost:8000/docs

## 🧪 Pruebas

```bash
source .venv/bin/activate
python -m pytest -q
```
