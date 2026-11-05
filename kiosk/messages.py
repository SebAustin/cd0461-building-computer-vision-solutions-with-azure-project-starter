"""Kiosk Message selection (docs/validation-rules.md, 'Kiosk Message selection')."""

from __future__ import annotations

from kiosk import normalize as n
from kiosk.models import LuggageScan, ManifestRow, ValidationResult

_REPRESENTATIVE = "Please see a customer service representative."

BOARDING_PASS_MISMATCH = (
    "Dear Sir/Madam,\n"
    "Some of the information in your boarding pass does not match the flight manifest data, "
    f"so you cannot board the plane.\n{_REPRESENTATIVE}"
)
ID_MISMATCH = (
    "Dear Sir/Madam,\n"
    "Some of the information on your ID card does not match the flight manifest data, "
    f"so you cannot board the plane.\n{_REPRESENTATIVE}"
)


def _salutation(row: ManifestRow) -> str:
    title = {"M": "Mr.", "F": "Ms."}.get(row.sex.strip().upper()[:1], "")
    return f"Dear {title} {row.full_name},".replace("  ", " ")


def _twelve_hour(raw: str) -> str:
    hour, minute = map(int, n.parse_time(raw).split(":"))
    return f"{hour % 12 or 12}:{minute:02d} {'PM' if hour >= 12 else 'AM'}"


def _luggage_sentence(result: ValidationResult, scan: LuggageScan) -> str | None:
    if not scan.is_scanned:
        return None
    if result.luggage:
        return "We did not find a prohibited item (lighter) in your carry-on baggage, thanks for following the procedure."
    return "We have found a prohibited item in your carry-on baggage, and it is flagged for removal."


def _identity_sentence(result: ValidationResult, scan: LuggageScan) -> str:
    luggage_failed = scan.is_scanned and not result.luggage
    if not result.person:
        return f"Your identity could not be verified. {_REPRESENTATIVE}"
    if luggage_failed:
        return "Your identity is verified. However, your baggage verification failed, so please see a customer service representative."
    return "Your identity is verified so please board the plane."


def kiosk_message(row: ManifestRow | None, result: ValidationResult, scan: LuggageScan) -> str:
    if row is None or not result.boarding_pass:
        return BOARDING_PASS_MISMATCH
    if not (result.name and result.dob):
        return ID_MISMATCH
    lines = [
        _salutation(row),
        f"You are welcome to flight # {n.flight_key(row.carrier, row.flight_no)} leaving at "
        f"{_twelve_hour(row.boarding_time)} from {row.origin} to {row.destination}.",
        f"Your seat number is {row.seat}, and it is confirmed.",
        _luggage_sentence(result, scan),
        _identity_sentence(result, scan),
    ]
    return "\n".join(line for line in lines if line)
