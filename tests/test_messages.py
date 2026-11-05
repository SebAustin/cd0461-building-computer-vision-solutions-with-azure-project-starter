from dataclasses import replace

from kiosk.messages import kiosk_message
from kiosk.models import LuggageScan, ValidationResult

ALL_PASS = ValidationResult(name=True, dob=True, person=True, boarding_pass=True, luggage=True)
CLEAN = LuggageScan.scanned(0.1, image="x.jpg")
LIGHTER = LuggageScan.scanned(0.9, image="x.jpg")


def test_all_pass_welcomes_and_boards(avkash_row):
    msg = kiosk_message(avkash_row, ALL_PASS, CLEAN)
    assert msg.startswith("Dear Mr. Avkash Chauhan,")
    assert "flight # UA234 leaving at 10:00 AM from San Francisco to Chicago" in msg
    assert "Your seat number is 20A, and it is confirmed." in msg
    assert "We did not find a prohibited item (lighter)" in msg
    assert "Your identity is verified so please board the plane." in msg


def test_ms_for_female_passenger(avkash_row):
    assert kiosk_message(replace(avkash_row, sex="F"), ALL_PASS, CLEAN).startswith("Dear Ms.")


def test_boarding_pass_failure_wins_over_everything(avkash_row):
    result = replace(ALL_PASS, boarding_pass=False, name=False)
    msg = kiosk_message(avkash_row, result, CLEAN)
    assert msg.startswith("Dear Sir/Madam,")
    assert "information in your boarding pass does not match" in msg


def test_unknown_passenger_gets_boarding_pass_message():
    msg = kiosk_message(None, ValidationResult.all_false(), LuggageScan.not_scanned())
    assert "boarding pass does not match" in msg


def test_id_failure_when_pass_ok(avkash_row):
    for result in (replace(ALL_PASS, dob=False), replace(ALL_PASS, name=False)):
        msg = kiosk_message(avkash_row, result, CLEAN)
        assert msg.startswith("Dear Sir/Madam,")
        assert "information on your ID card does not match" in msg


def test_lighter_found(avkash_row):
    msg = kiosk_message(avkash_row, replace(ALL_PASS, luggage=False), LIGHTER)
    assert "We have found a prohibited item in your carry-on baggage" in msg
    assert "your baggage verification failed" in msg


def test_identity_not_verified(avkash_row):
    msg = kiosk_message(avkash_row, replace(ALL_PASS, person=False), CLEAN)
    assert "Your identity could not be verified. Please see a customer service representative." in msg
    assert "please board the plane" not in msg


def test_not_scanned_omits_luggage_sentence(avkash_row):
    msg = kiosk_message(avkash_row, replace(ALL_PASS, luggage=False), LuggageScan.not_scanned())
    assert "prohibited item" not in msg
    assert "Your identity is verified so please board the plane." in msg


def test_lighter_and_identity_both_fail(avkash_row):
    msg = kiosk_message(avkash_row, replace(ALL_PASS, luggage=False, person=False), LIGHTER)
    assert "flagged for removal" in msg
    assert "Your identity could not be verified" in msg
