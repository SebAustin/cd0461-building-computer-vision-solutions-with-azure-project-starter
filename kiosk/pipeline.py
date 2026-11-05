"""Kiosk processing for one Passenger: lookup by Ticket Number, validate, choose the Kiosk Message."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

from kiosk import normalize as n
from kiosk.manifest import find_by_ticket
from kiosk.messages import kiosk_message
from kiosk.models import BoardingPass, IdDocument, LuggageScan, ManifestRow, PersonMatch, ValidationResult
from kiosk.validators import validate_all


@dataclass(frozen=True)
class KioskOutcome:
    ticket_no: str | None
    row: ManifestRow | None
    id_doc: IdDocument
    boarding_pass: BoardingPass
    person: PersonMatch | None
    luggage: LuggageScan
    result: ValidationResult
    message: str

    def summary(self) -> dict[str, Any]:
        return {
            "ticket_no": self.ticket_no,
            "passenger": self.row.full_name if self.row else None,
            "extracted_id": asdict(self.id_doc),
            "extracted_boarding_pass": asdict(self.boarding_pass),
            "person_match": asdict(self.person) if self.person else None,
            "luggage_scan": {**asdict(self.luggage), "status": self.luggage.status.value},
            "validations": self.result.as_dict(),
            "kiosk_message": self.message,
        }


def _ticket(boarding_pass: BoardingPass) -> str | None:
    try:
        return n.ticket_number(boarding_pass.ticket_no)
    except ValueError:
        return None


def process_passenger(
    rows: Iterable[ManifestRow],
    id_doc: IdDocument,
    boarding_pass: BoardingPass,
    person: PersonMatch | None,
    luggage: LuggageScan,
) -> KioskOutcome:
    ticket = _ticket(boarding_pass)
    row = find_by_ticket(rows, ticket) if ticket else None
    result = validate_all(row, id_doc, boarding_pass, person, luggage)
    return KioskOutcome(ticket, row, id_doc, boarding_pass, person, luggage, result, kiosk_message(row, result, luggage))
