from dataclasses import replace

from kiosk.models import LuggageScan, PersonMatch
from kiosk.pipeline import process_passenger


def test_finds_row_by_ticket_and_boards(avkash_row, avkash_id, avkash_pass):
    outcome = process_passenger([avkash_row], avkash_id, avkash_pass, PersonMatch(0.9, "face"), LuggageScan.scanned(0.1, "x.jpg"))
    assert outcome.row == avkash_row
    assert outcome.result.passed_count == 5
    assert "please board the plane" in outcome.message
    assert outcome.ticket_no == "34236751"


def test_unknown_ticket_is_boarding_pass_failure(avkash_row, avkash_id, avkash_pass):
    outcome = process_passenger([avkash_row], avkash_id, replace(avkash_pass, ticket_no="ETK-1E"), None, LuggageScan.not_scanned())
    assert outcome.row is None
    assert outcome.result.passed_count == 0
    assert "boarding pass does not match" in outcome.message


def test_unreadable_ticket_is_boarding_pass_failure(avkash_row, avkash_id, avkash_pass):
    outcome = process_passenger([avkash_row], avkash_id, replace(avkash_pass, ticket_no=""), None, LuggageScan.not_scanned())
    assert outcome.row is None
    assert outcome.ticket_no is None


def test_summary_is_json_friendly(avkash_row, avkash_id, avkash_pass):
    outcome = process_passenger([avkash_row], avkash_id, avkash_pass, None, LuggageScan.not_scanned())
    summary = outcome.summary()
    assert summary["ticket_no"] == "34236751"
    assert summary["validations"]["PersonValidation"] is False
    assert summary["luggage_scan"]["status"] == "not_scanned"
    assert summary["person_match"] is None
