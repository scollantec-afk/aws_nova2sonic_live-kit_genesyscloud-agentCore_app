import contextvars


# Estado del turno actual. Se usa para construir el contrato de salida
# {type, speech, data} sin acoplar los agentes al transporte. Cada agente
# / tool registra aqui el dominio y los datos estructurados que produjo.
# NO contiene ninguna logica de decision de intencion.

_turn = contextvars.ContextVar("turn", default=None)


def _current():
    state = _turn.get()
    if state is None:
        state = {"type": "unknown", "speech": "", "data": {}}
        _turn.set(state)
    return state


def reset_turn():
    _turn.set({"type": "unknown", "speech": "", "data": {}})


def set_type(value: str):
    _current()["type"] = value


def set_speech(value: str):
    _current()["speech"] = value


def set_data(value: dict):
    _current()["data"] = value


def get_turn() -> dict:
    return dict(_current())
