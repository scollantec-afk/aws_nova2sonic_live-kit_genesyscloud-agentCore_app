import json
import re
from pathlib import Path

from strands import tool

from . import set_data


_DATA_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "mock_flights.json"
)

_RESERVATIONS_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "mock_reservations.json"
)


def _load_flights() -> dict:
    if not _DATA_PATH.exists():
        return {}
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


def _load_reservations() -> dict:
    if not _RESERVATIONS_PATH.exists():
        return {}
    return json.loads(_RESERVATIONS_PATH.read_text(encoding="utf-8"))


_MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _format_date_es(value: str) -> str:
    """Convierte una fecha ISO (YYYY-MM-DD) a un formato hablado en espanol.

    Ejemplo: "2026-08-12" -> "12 de agosto de 2026". Si el valor no tiene el
    formato esperado, se devuelve tal cual para no perder informacion.
    """

    try:
        year, month, day = (value or "").split("-")
        return f"{int(day)} de {_MESES_ES[int(month) - 1]} de {int(year)}"
    except Exception:
        return value


def _with_spoken_date(payload: dict) -> dict:
    """Anade un campo date_es con la fecha en formato hablado si existe date."""

    if payload.get("date"):
        payload["date_es"] = _format_date_es(payload["date"])
    return payload


@tool
def get_flight_status(flight_number: str) -> dict:
    """
    Obtiene el estado de un vuelo a partir de su codigo (por ejemplo IB1234).

    Usar unicamente cuando el usuario ha proporcionado un codigo de vuelo.
    Devuelve los datos del vuelo (mock) o found=false si no existe.
    """

    match = re.search(r"[A-Za-z]{2}\s?\d{3,4}", flight_number or "")
    code = (match.group(0) if match else (flight_number or "")).upper().replace(" ", "")

    info = _load_flights().get(code)

    if not info:
        return {"found": False, "flight_number": code}

    payload = {"flight_number": code, **info}
    set_data(payload)

    return {"found": True, **payload}


@tool
def get_reservation(reference: str) -> dict:
    """
    Busca una reserva de vuelo por su codigo de reserva (por ejemplo, ABC123).

    Acepta el codigo con o sin espacios. Usar cuando el usuario pregunta por su
    reserva, su pasaje o su asiento y proporciona el codigo de reserva.

    Devuelve los datos de la reserva (mock) o found=false si no existe.
    """

    ref = (reference or "").strip()
    reservations = _load_reservations()

    # Coincidencia por codigo de reserva, tolerante a espacios/formato.
    code = re.sub(r"[^A-Za-z0-9]", "", ref).upper()
    if code and code in reservations:
        payload = _with_spoken_date({"reservation_code": code, **reservations[code]})
        set_data(payload)
        return {"found": True, **payload}

    return {"found": False, "reference": ref}
