import json
from pathlib import Path

import pytest

from kiosk.services import docintel
from kiosk.validators import validate_dob

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_parse_id_prefers_typed_values_over_raw_content():
    doc = docintel.parse_id_document(load("id_radha.json"))
    assert (doc.first_name, doc.last_name, doc.date_of_birth, doc.sex) == ("Radha", "S Kumar", "1994-03-05", "F")


def test_parsed_id_passes_dob_against_manifest(avkash_row):
    assert validate_dob(avkash_row, docintel.parse_id_document(load("id_avkash.json")))


def test_parse_id_with_no_documents_raises():
    with pytest.raises(ValueError):
        docintel.parse_id_document({"documents": []})


def test_missing_field_becomes_empty_string():
    doc = docintel.parse_id_document({"documents": [{"fields": {"FirstName": {"content": " Libby "}}}]})
    assert doc.first_name == "Libby"
    assert doc.last_name == ""


def test_parse_boarding_pass_maps_labels_to_model():
    fields = {label: {"valueString": f"v-{label}"} for label in docintel.BOARDING_PASS_FIELDS.values()}
    bp = docintel.parse_boarding_pass({"documents": [{"fields": fields}]})
    assert bp.passenger_name == "v-PassengerName"
    assert bp.ticket_no == "v-TicketNo"


def test_field_confidence():
    assert docintel.field_confidence({"A": {"confidence": 0.5}}, "A") == 0.5
    assert docintel.field_confidence({}, "A") is None
