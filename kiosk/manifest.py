"""Flight Manifest: build from the starter CSV, read rows, record Validation Statuses.

DataFrames are never modified in place; every update returns a new frame.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

import pandas as pd

from kiosk import normalize as n
from kiosk.models import ManifestRow, ValidationResult

VALIDATION_COLUMNS = ["NameValidation", "DoBValidation", "PersonValidation", "BoardingPassValidation", "LuggageValidation"]
MANIFEST_COLUMNS = [
    "TicketNo", "FirstName", "LastName", "DateOfBirth", "Sex",
    "Carrier", "FlightNo", "Class", "From", "To", "Date",
    "Baggage", "Seat", "Gate", "BoardingTime",
    *VALIDATION_COLUMNS,
]  # fmt: skip

_STARTER_RENAMES = {"Carrier ": "Carrier", "Flight No.": "FlightNo", "Boarding Time": "BoardingTime", "Ticket No.": "TicketNo"}


def _split_name(full_name: str) -> tuple[str, str]:
    words = full_name.split()
    if len(words) < 2:
        raise ValueError(f"cannot split passenger name {full_name!r}")
    return " ".join(words[:-1]), words[-1]


def build_manifest(starter: pd.DataFrame, ground_truth: Mapping[str, Mapping[str, str]]) -> pd.DataFrame:
    """Starter CSV + hand-entered DoB/Sex per ticket -> full Manifest with all Validations FALSE."""
    frame = starter.rename(columns=_STARTER_RENAMES).copy()
    frame["TicketNo"] = frame["TicketNo"].astype(str).str.strip()
    missing = [t for t in frame["TicketNo"] if t not in ground_truth]
    if missing:
        raise ValueError(f"no DoB/Sex ground truth for tickets: {missing}")
    names = frame["Passanger Name"].map(_split_name)
    frame = frame.assign(
        FirstName=names.map(lambda p: p[0]),
        LastName=names.map(lambda p: p[1]),
        DateOfBirth=frame["TicketNo"].map(lambda t: ground_truth[t]["DateOfBirth"]),
        Sex=frame["TicketNo"].map(lambda t: ground_truth[t]["Sex"]),
        FlightNo=frame["FlightNo"].astype(str),
        **{col: False for col in VALIDATION_COLUMNS},
    )
    return frame[MANIFEST_COLUMNS].reset_index(drop=True)


def load_manifest(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"TicketNo": str, "FlightNo": str})[MANIFEST_COLUMNS]


def save_manifest(frame: pd.DataFrame, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _to_row(record: Mapping[str, object]) -> ManifestRow:
    return ManifestRow(
        ticket_no=str(record["TicketNo"]),
        first_name=str(record["FirstName"]),
        last_name=str(record["LastName"]),
        date_of_birth=n.parse_date(str(record["DateOfBirth"])),
        sex=str(record["Sex"]),
        carrier=str(record["Carrier"]),
        flight_no=str(record["FlightNo"]),
        travel_class=str(record["Class"]),
        origin=str(record["From"]),
        destination=str(record["To"]),
        flight_date=n.parse_date(str(record["Date"])),
        boarding_time=str(record["BoardingTime"]),
        seat=str(record["Seat"]),
        gate=str(record["Gate"]),
        baggage=str(record["Baggage"]),
    )


def to_rows(frame: pd.DataFrame) -> list[ManifestRow]:
    return [_to_row(record) for record in frame.to_dict("records")]


def find_by_ticket(rows: Iterable[ManifestRow], ticket_no: str) -> ManifestRow | None:
    return next((row for row in rows if row.ticket_no == ticket_no), None)


def apply_result(frame: pd.DataFrame, ticket_no: str, result: ValidationResult) -> pd.DataFrame:
    mask = frame["TicketNo"] == ticket_no
    if not mask.any():
        raise KeyError(f"ticket {ticket_no} not on manifest")
    updated = frame.copy()
    for column, value in result.as_dict().items():
        updated.loc[mask, column] = value
    return updated
