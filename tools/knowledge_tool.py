import re
import unicodedata
from pathlib import Path

from strands import tool


_KB_PATH = (
    Path(__file__).resolve().parent.parent / "knowledge" / "airline_manual.txt"
)

# Palabras genericas que no aportan a la relevancia de la busqueda.
_STOPWORDS = {
    "para",
    "como",
    "cual",
    "cuales",
    "cuanto",
    "cuanta",
    "puedo",
    "puede",
    "quiero",
    "necesito",
    "sobre",
    "informacion",
    "info",
    "tema",
    "favor",
    "ayuda",
    "saber",
    "consulta",
    "cliente",
    "llevar",
    "tengo",
    "acerca",
    "mi",
    "un",
    "una",
}


def _normalize(text: str) -> str:
    text = (text or "").lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def _tokens(text: str):
    raw = re.split(r"[^a-z0-9]+", _normalize(text))
    return [t for t in raw if len(t) >= 4 and t not in _STOPWORDS]


def _load_sections():
    if not _KB_PATH.exists():
        return []

    raw = _KB_PATH.read_text(encoding="utf-8").strip()
    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]

    sections = []
    for block in blocks[1:]:  # se omite el titulo del manual
        title = block.splitlines()[0].rstrip(":").strip()
        sections.append((title, block))
    return sections


@tool
def search_manual(query: str) -> dict:
    """
    Busca en el manual de la aerolinea la seccion relevante para la consulta.

    Recupera unicamente la seccion pertinente (no todo el documento). Si no
    hay ninguna seccion relevante, devuelve found=false para que el agente
    informe que no dispone de esa informacion.
    """

    query_tokens = _tokens(query)
    sections = _load_sections()

    best = None
    best_hits = 0

    for title, block in sections:
        body = _normalize(block)
        hits = sum(1 for token in query_tokens if token in body)
        if hits > best_hits:
            best_hits = hits
            best = (title, block)

    if not best or best_hits == 0:
        return {"found": False}

    return {"found": True, "section": best[0], "content": best[1]}
