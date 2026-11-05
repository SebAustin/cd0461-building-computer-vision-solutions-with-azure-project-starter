from datetime import date

import pytest

from kiosk import normalize as n


@pytest.mark.parametrize(
    "given, surname, expected",
    [
        ("Avkash", "Chauhan", ("avkash", "chauhan")),
        ("AVKASH CHAUHAN", "CHAUHAN", ("avkash", "chauhan")),
        ("Radha", "S Kumar", ("radha", "kumar")),
        ("Radha S.", "Kumar", ("radha", "kumar")),
        ("  james ", " Webb ", ("james", "webb")),
    ],
)
def test_name_key_uses_first_given_word_and_last_surname_word(given, surname, expected):
    assert n.name_key(given, surname) == expected


def test_name_key_of_full_name_splits_on_first_and_last_word():
    assert n.full_name_key("Radha S Kumar") == ("radha", "kumar")


def test_name_key_rejects_blank_names():
    with pytest.raises(ValueError):
        n.name_key("", "Kumar")
    with pytest.raises(ValueError):
        n.full_name_key("Cher")


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("April 20, 2022", date(2022, 4, 20)),
        ("01/25/1990", date(1990, 1, 25)),
        ("1990-01-25", date(1990, 1, 25)),
        (date(1990, 1, 25), date(1990, 1, 25)),
    ],
)
def test_parse_date_accepts_common_formats(raw, expected):
    assert n.parse_date(raw) == expected


def test_parse_date_rejects_garbage():
    with pytest.raises(ValueError):
        n.parse_date("not a date")


@pytest.mark.parametrize(
    "raw, expected",
    [("10:00 AM PST", "10:00"), ("10:00 AM  PST", "10:00"), ("4:30 PM", "16:30"), ("16:30", "16:30")],
)
def test_parse_time_returns_24h_and_ignores_timezone(raw, expected):
    assert n.parse_time(raw) == expected


def test_parse_time_rejects_garbage():
    with pytest.raises(ValueError):
        n.parse_time("soon")


@pytest.mark.parametrize("carrier, number", [("UA", "234"), ("ua", " 234"), ("", "UA 234"), ("", "UA234")])
def test_flight_key_joins_carrier_and_number(carrier, number):
    assert n.flight_key(carrier, number) == "UA234"


@pytest.mark.parametrize("raw, expected", [("E", "economy"), ("Economy", "economy"), ("B", "business"), ("Business ", "business"), ("F", "first")])
def test_class_key_maps_codes_to_names(raw, expected):
    assert n.class_key(raw) == expected


@pytest.mark.parametrize("raw, expected", [("ETK-34236751E", "34236751"), ("34236751", "34236751"), (" ETK-34236747E ", "34236747")])
def test_ticket_number_extracts_digits(raw, expected):
    assert n.ticket_number(raw) == expected


def test_ticket_number_rejects_missing_digits():
    with pytest.raises(ValueError):
        n.ticket_number("ETK-")


def test_text_key_ignores_case_whitespace_and_punctuation():
    assert n.text_key("  San  Francisco. ") == "san francisco"
