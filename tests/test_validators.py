from dataclasses import replace

import pytest

from kiosk import validators as v
from kiosk.models import LuggageScan, PersonMatch


class TestNameValidation:
    def test_passes_when_pass_and_id_match_manifest(self, avkash_row, avkash_id, avkash_pass):
        assert v.validate_name(avkash_row, avkash_id, avkash_pass) is True

    def test_fails_when_boarding_pass_name_differs(self, avkash_row, avkash_id, avkash_pass):
        assert v.validate_name(avkash_row, avkash_id, replace(avkash_pass, passenger_name="Avinash Chauhan")) is False

    def test_fails_when_id_surname_differs(self, avkash_row, avkash_id, avkash_pass):
        assert v.validate_name(avkash_row, replace(avkash_id, last_name="Chavan"), avkash_pass) is False

    def test_fails_when_name_unreadable(self, avkash_row, avkash_id, avkash_pass):
        assert v.validate_name(avkash_row, replace(avkash_id, first_name=""), avkash_pass) is False


class TestDobValidation:
    def test_passes_on_same_calendar_date(self, avkash_row, avkash_id):
        assert v.validate_dob(avkash_row, avkash_id) is True

    def test_fails_one_day_off(self, avkash_row, avkash_id):
        assert v.validate_dob(avkash_row, replace(avkash_id, date_of_birth="01/02/1990")) is False

    def test_fails_when_unreadable(self, avkash_row, avkash_id):
        assert v.validate_dob(avkash_row, replace(avkash_id, date_of_birth="??")) is False


class TestBoardingPassValidation:
    def test_passes_when_all_seven_fields_match(self, avkash_row, avkash_pass):
        assert v.validate_boarding_pass(avkash_row, avkash_pass) is True

    @pytest.mark.parametrize(
        "field, value",
        [
            ("flight_no", "235"),
            ("seat", "20B"),
            ("travel_class", "B"),
            ("origin", "Seattle"),
            ("destination", "Boston"),
            ("flight_date", "April 21, 2022"),
            ("boarding_time", "10:30 AM PST"),
        ],
    )
    def test_fails_when_any_field_differs(self, avkash_row, avkash_pass, field, value):
        assert v.validate_boarding_pass(avkash_row, replace(avkash_pass, **{field: value})) is False

    def test_ignores_gate_and_baggage(self, avkash_row, avkash_pass):
        assert v.validate_boarding_pass(replace(avkash_row, gate="G9", baggage="YES"), avkash_pass) is True

    def test_fails_when_no_manifest_row(self, avkash_pass):
        assert v.validate_boarding_pass(None, avkash_pass) is False

    def test_fails_when_date_unreadable(self, avkash_row, avkash_pass):
        assert v.validate_boarding_pass(avkash_row, replace(avkash_pass, flight_date="")) is False


class TestPersonValidation:
    @pytest.mark.parametrize("confidence, expected", [(0.65, True), (0.9, True), (0.6499, False), (0.1, False)])
    def test_threshold_is_065_inclusive(self, confidence, expected):
        assert v.validate_person(PersonMatch(confidence=confidence, source="face")) is expected

    def test_fails_without_identity_video(self):
        assert v.validate_person(None) is False

    def test_fails_when_service_unavailable(self):
        assert v.validate_person(PersonMatch(confidence=None, source="unavailable")) is False


class TestLuggageValidation:
    @pytest.mark.parametrize("probability, expected", [(0.0, True), (0.4999, True), (0.5, False), (0.97, False)])
    def test_lighter_threshold_is_05(self, probability, expected):
        assert v.validate_luggage(LuggageScan.scanned(probability, image="x.jpg")) is expected

    def test_not_scanned_is_false(self):
        assert v.validate_luggage(LuggageScan.not_scanned()) is False


def test_validate_all_combines_the_five(avkash_row, avkash_id, avkash_pass):
    result = v.validate_all(
        row=avkash_row,
        id_doc=avkash_id,
        boarding_pass=avkash_pass,
        person=PersonMatch(confidence=0.8, source="face"),
        luggage=LuggageScan.scanned(0.1, image="x.jpg"),
    )
    assert result.as_dict() == {
        "NameValidation": True,
        "DoBValidation": True,
        "PersonValidation": True,
        "BoardingPassValidation": True,
        "LuggageValidation": True,
    }
    assert result.passed_count == 5


def test_validate_all_without_row_fails_everything_manifest_based(avkash_id, avkash_pass):
    result = v.validate_all(None, avkash_id, avkash_pass, None, LuggageScan.not_scanned())
    assert result.passed_count == 0
