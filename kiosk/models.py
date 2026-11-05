"""Domain models for the boarding kiosk. All immutable; see GLOSSARY.md for terms."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


@dataclass(frozen=True)
class ManifestRow:
    """One Passenger's row on the Flight Manifest (the ground truth)."""

    ticket_no: str
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    carrier: str
    flight_no: str
    travel_class: str
    origin: str
    destination: str
    flight_date: date
    boarding_time: str
    seat: str
    gate: str
    baggage: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass(frozen=True)
class IdDocument:
    """Fields extracted from a Digital ID. Raw strings, as the extractor returned them."""

    first_name: str
    last_name: str
    date_of_birth: str
    sex: str


@dataclass(frozen=True)
class BoardingPass:
    """Fields extracted from a Boarding Pass. Raw strings, as the extractor returned them."""

    passenger_name: str
    carrier: str
    flight_no: str
    travel_class: str
    origin: str
    destination: str
    flight_date: str
    boarding_time: str
    seat: str
    ticket_no: str


@dataclass(frozen=True)
class PersonMatch:
    """Outcome of comparing the Digital ID face with the Identity Video face.

    `confidence` is None when no comparison could be made (service unavailable).
    """

    confidence: float | None
    source: str


class ScanStatus(Enum):
    SCANNED = "scanned"
    NOT_SCANNED = "not_scanned"


@dataclass(frozen=True)
class LuggageScan:
    """A Luggage Scan result. Not Scanned is distinct from a failed Luggage Validation."""

    status: ScanStatus
    lighter_probability: float | None = None
    image: str | None = None

    @classmethod
    def scanned(cls, lighter_probability: float, image: str) -> LuggageScan:
        if not 0.0 <= lighter_probability <= 1.0:
            raise ValueError(f"lighter probability out of range: {lighter_probability}")
        return cls(ScanStatus.SCANNED, lighter_probability, image)

    @classmethod
    def not_scanned(cls) -> LuggageScan:
        return cls(ScanStatus.NOT_SCANNED)

    @property
    def is_scanned(self) -> bool:
        return self.status is ScanStatus.SCANNED


@dataclass(frozen=True)
class ValidationResult:
    """The five Validation Statuses for one Passenger."""

    name: bool
    dob: bool
    person: bool
    boarding_pass: bool
    luggage: bool

    @classmethod
    def all_false(cls) -> ValidationResult:
        return cls(False, False, False, False, False)

    def as_dict(self) -> dict[str, bool]:
        return {
            "NameValidation": self.name,
            "DoBValidation": self.dob,
            "PersonValidation": self.person,
            "BoardingPassValidation": self.boarding_pass,
            "LuggageValidation": self.luggage,
        }

    @property
    def passed_count(self) -> int:
        return sum(self.as_dict().values())
