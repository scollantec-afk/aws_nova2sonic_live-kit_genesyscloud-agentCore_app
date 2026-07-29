import os
import re

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands.models import BedrockModel

import tools
from agents.supervisor_agent import build_session


app = BedrockAgentCoreApp()


def _sanitize_speech(text: str) -> str:
    """Limpia el texto para sintesis de voz.

    Elimina saltos de linea, barras invertidas, barras "/" y caracteres de
    formato (markdown) que un TTS leeria de forma literal ("antibarra", etc.),
    y colapsa espacios para dejar una unica frase continua.
    """

    if not text:
        return text

    # Secuencias de escape que a veces llegan como texto literal ("\n", "\t").
    text = text.replace("\\n", " ").replace("\\t", " ").replace("\\r", " ")
    # Saltos de linea y tabulaciones reales.
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    # Barras invertidas ("antibarra") y barras normales.
    text = text.replace("\\", " ").replace("/", " ")
    # Simbolos de formato markdown u otros caracteres que no se leen bien.
    text = re.sub(r"[*_#`>|~^]", " ", text)
    # Colapsa espacios multiples.
    text = re.sub(r"\s+", " ", text).strip()

    return text

MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "us.anthropic.claude-haiku-4-5-20251001-v1:0",
)

_model = BedrockModel(model_id=MODEL_ID)

# Memoria multi-turno por sesion. Cada runtimeSessionId conserva su propio
# supervisor (y agentes de dominio) con su historial de conversacion.
_sessions = {}


def _get_supervisor(session_id: str):
    if session_id not in _sessions:
        _sessions[session_id] = build_session(_model)
    return _sessions[session_id]


@app.entrypoint
def invoke(payload):
    """
    Punto de entrada del AgentCore Runtime.

    Contrato de entrada:
        {"session_id": "xxx", "prompt": "mensaje", "conversation_context": {}}

    Contrato de salida (orientado a voz):
        {"type": "flight|knowledge|unknown", "speech": "...", "data": {}}
    """

    session_id = payload.get("session_id") or "default-session"
    prompt = payload.get("prompt", "")

    tools.reset_turn()

    supervisor = _get_supervisor(session_id)
    result = supervisor(prompt)

    turn = tools.get_turn()

    if turn["speech"]:
        speech = turn["speech"]
    else:
        try:
            speech = result.message["content"][0]["text"]
        except Exception:
            speech = str(result.message)

    speech = _sanitize_speech(speech)

    return {
        "type": turn["type"],
        "speech": speech,
        "data": turn["data"],
    }


if __name__ == "__main__":
    app.run()
