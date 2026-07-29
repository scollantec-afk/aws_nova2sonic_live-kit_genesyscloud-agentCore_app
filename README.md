# AgentCore App — Asistente de voz de aerolínea

Contenedor de agentes para **Amazon Bedrock AgentCore Runtime**. Implementa un
asistente conversacional de aerolínea orientado a voz, con un **agente supervisor**
que entiende la intención del usuario mediante comprensión semántica (no por
palabras clave) y delega en agentes de dominio especializados.

Forma parte de una arquitectura mayor **Nova Sonic + LiveKit + Genesys Cloud**,
donde este componente es el cerebro de orquestación de agentes.

## Arquitectura

```
                 ┌────────────────────────┐
   prompt  ─────▶│    Supervisor Agent     │  (comprensión semántica de intención)
                 └───────────┬─────────────┘
                             │ delega (tools)
              ┌──────────────┴───────────────┐
              ▼                               ▼
     ┌─────────────────┐             ┌──────────────────┐
     │  Flight Agent   │             │ Knowledge Agent  │
     │ vuelos/reservas │             │ políticas/FAQ    │
     └────────┬────────┘             └────────┬─────────┘
              │ tools                          │ tool
    get_flight_status                    search_manual
    get_reservation                     (manual aerolínea)
    (datos mock)
```

- **Supervisor**: único punto de entrada conversacional. No aplica reglas ni
  `if/else` de intención; decide semánticamente a qué agente delegar.
- **Flight Agent**: estado de vuelos y reservas. Identifica siempre por
  **código** (código de vuelo o código de reserva).
- **Knowledge Agent**: preguntas abiertas sobre políticas de la aerolínea
  (equipaje, mascotas, check-in, cambios, cancelaciones, protocolos).

### Contrato de salida (orientado a voz)

```json
{
  "type": "flight | knowledge | unknown",
  "speech": "texto listo para sintetizar por voz",
  "data": {}
}
```

El campo `speech` se **sanea** antes de devolverse: se eliminan saltos de línea,
barras invertidas, barras `/` y símbolos de formato para evitar que el motor de
voz los lea de forma literal. Las fechas se entregan en formato hablado en
español (por ejemplo, `12 de agosto de 2026`).

## Estructura

```
agentcore-app/
├── app.py                     # Entrypoint del AgentCore Runtime + sesiones (memoria multi-turno)
├── agents/
│   ├── supervisor_agent.py    # Supervisor: delega semánticamente
│   ├── flight_agent.py        # Agente de vuelos y reservas
│   └── knowledge_agent.py     # Agente de conocimiento (políticas/FAQ)
├── tools/
│   ├── __init__.py            # Estado del turno (type/speech/data) vía contextvars
│   ├── flight_tool.py         # get_flight_status, get_reservation (datos mock)
│   └── knowledge_tool.py      # search_manual (búsqueda en el manual)
├── data/
│   ├── mock_flights.json      # Vuelos de ejemplo
│   └── mock_reservations.json # Reservas de ejemplo
├── knowledge/
│   └── airline_manual.txt     # Base de conocimiento (mock)
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.12+
- Credenciales de AWS con acceso a Amazon Bedrock
- Acceso habilitado al modelo (inference profile) en tu región

## Configuración

El modelo se toma de la variable de entorno `BEDROCK_MODEL_ID` (con un valor por
defecto en `app.py`). Para pruebas locales puedes crear un archivo `.env`:

```env
BEDROCK_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0
```

> Nota: se usa el **inference profile** (`us.anthropic...`), no el model ID base.
> Invocar el ID base con throughput on-demand no está soportado.

## Instalación y ejecución local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python app.py
```

## Despliegue en Amazon Bedrock AgentCore

```powershell
agentcore configure --entrypoint app.py
agentcore launch
```

Invocación de prueba:

```powershell
agentcore invoke '{"prompt":"quiero ayuda con mi vuelo"}' --session-id "test-001"
```

Memoria multi-turno (misma sesión mantiene contexto):

```powershell
agentcore invoke '{"prompt":"quiero saber mi vuelo"}' --session-id "test-002"   # pide el código
agentcore invoke '{"prompt":"IB1234"}'               --session-id "test-002"   # continúa y consulta el estado
```

## Datos de ejemplo (mock)

| Tipo     | Códigos disponibles                     |
| -------- | --------------------------------------- |
| Vuelos   | `IB1234`, `IB5678`, `LA800`, `LA755`    |
| Reservas | `ABC123`, `XYZ789`, `LAT456`            |

## Notas

- Los datos de vuelos, reservas y el manual son **mock** para POC.
- La configuración local de despliegue (`.bedrock_agentcore.yaml`) y el `.env`
  no se versionan; se regeneran con `agentcore configure`.
