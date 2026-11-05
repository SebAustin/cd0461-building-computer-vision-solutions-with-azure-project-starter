"""Normalization used to compare extracted text against the Flight Manifest.

Every function raises ValueError on input it cannot interpret, so callers can
turn "unreadable" into a failed Validation instead of a silent match.
"""

from __future__ import annotations

import re
from datetime import date, datetime

from dateutil import parser as date_parser

_NON_WORD = re.compile(r"[^\w\s]")
_SPACES = re.compile(r"\s+")
_TIME = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*([AaPp][Mm])?")
_CLASS_CODES = {"e": "economy", "economy": "economy", "b": "business", "business": "business", "f": "first", "first": "first"}


def text_key(value: str) -> str:
    """Lower-case, strip punctuation, collapse whitespace."""
    return _SPACES.sub(" ", _NON_WORD.sub(" ", value or "")).strip().lower()


def _words(value: str) -> list[str]:
    return text_key(value).split()


def name_key(given: str, surname: str) -> tuple[str, str]:
    """(first word of the given name, last word of the surname)."""
    given_words, surname_words = _words(given), _words(surname)
    if not given_words or not surname_words:
        raise ValueError(f"unreadable name: given={given!r} surname={surname!r}")
    return given_words[0], surname_words[-1]


def full_name_key(full_name: str) -> tuple[str, str]:
    """Name key of a single full-name string, e.g. a Boarding Pass name."""
    words = _words(full_name)
    if len(words) < 2:
        raise ValueError(f"full name needs a given name and a surname: {full_name!r}")
    return words[0], words[-1]


def parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    try:
        return date_parser.parse(value, dayfirst=False).date()
    except (ValueError, OverflowError, TypeError) as exc:
        raise ValueError(f"unreadable date: {value!r}") from exc


def parse_time(value: str) -> str:
    """'10:00 AM PST' -> '10:00'; timezone labels are ignored."""
    match = _TIME.match(value or "")
    if not match:
        raise ValueError(f"unreadable time: {value!r}")
    hour, minute, meridiem = int(match[1]), int(match[2]), (match[3] or "").lower()
    if meridiem:
        hour = hour % 12 + (12 if meridiem == "pm" else 0)
    return datetime(2000, 1, 1, hour, minute).strftime("%H:%M")


def flight_key(carrier: str, number: str) -> str:
    """Carrier and number joined, whitespace removed: ('UA', '234') -> 'UA234'."""
    return re.sub(r"\s+", "", f"{carrier or ''}{number or ''}").upper()


def class_key(value: str) -> str:
    key = text_key(value)
    if key not in _CLASS_CODES:
        raise ValueError(f"unknown travel class: {value!r}")
    return _CLASS_CODES[key]


def ticket_number(value: str) -> str:
    """'ETK-34236751E' -> '34236751'."""
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        raise ValueError(f"no ticket number in {value!r}")
    return digits
