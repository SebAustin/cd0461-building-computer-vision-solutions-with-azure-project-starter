"""Azure AI Document Intelligence (formerly Form Recognizer).

`analyze_*` functions call Azure and return the raw result as a dict.
`parse_*` functions turn that dict into domain models. They are pure, so tests use recorded results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from kiosk.config import setting
from kiosk.models import BoardingPass, IdDocument

ID_MODEL = "prebuilt-idDocument"

# Field names the custom boarding-pass model is trained to return (labels in Document Intelligence Studio).
BOARDING_PASS_FIELDS = {
    "passenger_name": "PassengerName",
    "carrier": "Carrier",
    "flight_no": "FlightNo",
    "travel_class": "Class",
    "origin": "From",
    "destination": "To",
    "flight_date": "Date",
    "boarding_time": "BoardingTime",
    "seat": "Seat",
    "ticket_no": "TicketNo",
}


def client() -> DocumentIntelligenceClient:
    return DocumentIntelligenceClient(setting("DOCINTEL_ENDPOINT"), AzureKeyCredential(setting("DOCINTEL_KEY")))


def analyze(path: Path, model_id: str, di: DocumentIntelligenceClient | None = None) -> dict[str, Any]:
    """Analyze a local file. Offsets use UTF-16 code units, matching what Document Intelligence Studio stores."""
    di = di or client()
    with path.open("rb") as handle:
        poller = di.begin_analyze_document(
            model_id, body=handle, content_type="application/octet-stream", string_index_type="utf16CodeUnit"
        )
    return poller.result().as_dict()


def _documents(result: dict[str, Any]) -> list[dict[str, Any]]:
    documents = result.get("documents") or []
    if not documents:
        raise ValueError("Document Intelligence returned no documents")
    return documents


def field_text(fields: dict[str, Any], name: str) -> str:
    """Best text value of a field: typed value if present, else the raw content; '' when missing."""
    field = fields.get(name) or {}
    for key in ("valueString", "valueDate", "valuePhoneNumber", "valueCountryRegion"):
        if field.get(key):
            return str(field[key])
    return str(field.get("content") or "").strip()


def field_confidence(fields: dict[str, Any], name: str) -> float | None:
    return (fields.get(name) or {}).get("confidence")


def parse_id_document(result: dict[str, Any]) -> IdDocument:
    fields = _documents(result)[0].get("fields") or {}
    return IdDocument(
        first_name=field_text(fields, "FirstName"),
        last_name=field_text(fields, "LastName"),
        date_of_birth=field_text(fields, "DateOfBirth"),
        sex=field_text(fields, "Sex"),
    )


def parse_boarding_pass(result: dict[str, Any]) -> BoardingPass:
    fields = _documents(result)[0].get("fields") or {}
    return BoardingPass(**{attr: field_text(fields, label) for attr, label in BOARDING_PASS_FIELDS.items()})


def extract_id(path: Path, di: DocumentIntelligenceClient | None = None) -> tuple[IdDocument, dict[str, Any]]:
    raw = analyze(path, ID_MODEL, di)
    return parse_id_document(raw), raw


def extract_boarding_pass(path: Path, di: DocumentIntelligenceClient | None = None) -> tuple[BoardingPass, dict[str, Any]]:
    raw = analyze(path, setting("BOARDING_PASS_MODEL_ID"), di)
    return parse_boarding_pass(raw), raw
