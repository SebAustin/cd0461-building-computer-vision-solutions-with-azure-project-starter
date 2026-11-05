"""The five Validations. Each returns a plain bool; unreadable evidence fails."""

from __future__ import annotations

import logging

from kiosk import normalize as n
from kiosk.models import BoardingPass, IdDocument, LuggageScan, ManifestRow, PersonMatch, ValidationResult

log = logging.getLogger(__name__)

PERSON_MATCH_THRESHOLD = 0.65
LIGHTER_THRESHOLD = 0.5


def validate_name(row: ManifestRow | None, id_doc: IdDocument, boarding_pass: BoardingPass) -> bool:
    """Three-way: Boarding Pass name and Digital ID name both match the Manifest."""
    if row is None:
        return False
    try:
        expected = n.name_key(row.first_name, row.last_name)
        return n.full_name_key(boarding_pass.passenger_name) == expected and n.name_key(id_doc.first_name, id_doc.last_name) == expected
    except ValueError as exc:
        log.info("name validation failed for ticket %s: %s", row.ticket_no, exc)
        return False


def validate_dob(row: ManifestRow | None, id_doc: IdDocument) -> bool:
    if row is None:
        return False
    try:
        return n.parse_date(id_doc.date_of_birth) == row.date_of_birth
    except ValueError as exc:
        log.info("DoB validation failed for ticket %s: %s", row.ticket_no, exc)
        return False


def validate_boarding_pass(row: ManifestRow | None, bp: BoardingPass) -> bool:
    """The seven flight fields on the Boarding Pass match the Manifest."""
    if row is None:
        return False
    try:
        checks = {
            "flight": n.flight_key(bp.carrier, bp.flight_no) == n.flight_key(row.carrier, row.flight_no),
            "seat": n.text_key(bp.seat) == n.text_key(row.seat),
            "class": n.class_key(bp.travel_class) == n.class_key(row.travel_class),
            "origin": n.text_key(bp.origin) == n.text_key(row.origin),
            "destination": n.text_key(bp.destination) == n.text_key(row.destination),
            "date": n.parse_date(bp.flight_date) == row.flight_date,
            "time": n.parse_time(bp.boarding_time) == n.parse_time(row.boarding_time),
        }
    except ValueError as exc:
        log.info("boarding pass validation failed for ticket %s: %s", row.ticket_no, exc)
        return False
    mismatched = [field for field, ok in checks.items() if not ok]
    if mismatched:
        log.info("boarding pass mismatch for ticket %s: %s", row.ticket_no, mismatched)
    return not mismatched


def validate_person(match: PersonMatch | None, threshold: float = PERSON_MATCH_THRESHOLD) -> bool:
    return match is not None and match.confidence is not None and match.confidence >= threshold


def validate_luggage(scan: LuggageScan, threshold: float = LIGHTER_THRESHOLD) -> bool:
    return scan.is_scanned and scan.lighter_probability is not None and scan.lighter_probability < threshold


def validate_all(
    row: ManifestRow | None,
    id_doc: IdDocument,
    boarding_pass: BoardingPass,
    person: PersonMatch | None,
    luggage: LuggageScan,
) -> ValidationResult:
    known = row is not None
    return ValidationResult(
        name=validate_name(row, id_doc, boarding_pass),
        dob=validate_dob(row, id_doc),
        person=known and validate_person(person),
        boarding_pass=validate_boarding_pass(row, boarding_pass),
        luggage=known and validate_luggage(luggage),
    )
