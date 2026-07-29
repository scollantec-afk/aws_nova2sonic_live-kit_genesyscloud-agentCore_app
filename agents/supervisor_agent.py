from strands import Agent, tool

from tools import set_type, set_speech
from .flight_agent import build_flight_agent
from .knowledge_agent import build_knowledge_agent


SUPERVISOR_SYSTEM_PROMPT = """
Eres un supervisor conversacional del asistente de voz de una aerolinea.

Tu unica tarea es entender la intencion del usuario mediante comprension
semantica (no por palabras exactas ni frases fijas) y delegar en el agente
adecuado usando las tools disponibles.

Orientacion (no son reglas literales, guian tu comprension):
- Intenciones relacionadas con vuelos, viajes aereos, estado del vuelo, puerta
  de embarque, horarios, o cuando el usuario responde con un codigo de vuelo
  -> delega en consult_flight_agent.
- Intenciones relacionadas con una reserva, pasaje, asiento o cuando el usuario
  da un codigo de reserva
  -> delega tambien en consult_flight_agent.
- Preguntas abiertas sobre politicas e informacion de la aerolinea (equipaje,
  mascotas, check-in, cambios, cancelaciones, protocolos y similares) -> delega
  en consult_knowledge_agent.

Instrucciones:
- Mantén el contexto de la conversacion entre turnos.
- Pasa el mensaje del usuario tal cual a la tool que elijas.
- Delega en un unico agente por turno.
- Devuelve exactamente la respuesta del agente al que delegaste, sin anadir
  texto adicional ni inventar informacion.
""".strip()


def build_session(model) -> Agent:
    """
    Construye un supervisor con memoria propia y sus agentes de dominio
    (tambien con memoria) para una sesion conversacional.
    """

    flight_agent = build_flight_agent(model)
    knowledge_agent = build_knowledge_agent(model)

    @tool
    def consult_flight_agent(user_message: str) -> str:
        """
        Delega en el agente de vuelos cualquier intencion relacionada con
        vuelos (estado, puerta, horario, codigo de vuelo) y con reservas
        (codigo de reserva, pasaje o asiento).
        """
        set_type("flight")
        response = flight_agent(user_message)
        try:
            answer = response.message["content"][0]["text"]
        except Exception:
            answer = str(response.message)
        set_speech(answer)
        return answer

    @tool
    def consult_knowledge_agent(user_message: str) -> str:
        """
        Delega en el agente de conocimiento las preguntas abiertas sobre
        politicas e informacion de la aerolinea.
        """
        set_type("knowledge")
        response = knowledge_agent(user_message)
        try:
            answer = response.message["content"][0]["text"]
        except Exception:
            answer = str(response.message)
        set_speech(answer)
        return answer

    return Agent(
        model=model,
        tools=[consult_flight_agent, consult_knowledge_agent],
        system_prompt=SUPERVISOR_SYSTEM_PROMPT,
    )
