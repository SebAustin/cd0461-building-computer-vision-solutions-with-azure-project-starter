from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from kiosk import manifest as m
from kiosk.models import ValidationResult

STARTER_CSV = Path(__file__).parents[1] / "starter/flight-manifest-csv/FlightManifest.csv"
GROUND_TRUTH = {
    "34236751": {"DateOfBirth": "1990-01-01", "Sex": "M"},
}


@pytest.fixture
def built() -> pd.DataFrame:
    return m.build_manifest(pd.read_csv(STARTER_CSV), GROUND_TRUTH | {
        t: {"DateOfBirth": "1980-01-01", "Sex": "F"} for t in
        ["34236746", "34236747", "34236748", "34236749", "34236750"]
    })


def test_build_splits_names_and_adds_columns(built):
    assert list(built.columns) == m.MANIFEST_COLUMNS
    radha = built[built["TicketNo"] == "34236747"].iloc[0]
    assert (radha["FirstName"], radha["LastName"]) == ("Radha S.", "Kumar")


def test_build_starts_all_validations_false(built):
    assert not built[m.VALIDATION_COLUMNS].to_numpy().any()


def test_build_requires_ground_truth_for_every_passenger():
    with pytest.raises(ValueError, match="34236746"):
        m.build_manifest(pd.read_csv(STARTER_CSV), GROUND_TRUTH)


def test_rows_round_trip_to_models(built):
    row = m.find_by_ticket(m.to_rows(built), "34236751")
    assert row is not None
    assert row.first_name == "Avkash"
    assert row.date_of_birth == date(1990, 1, 1)
    assert row.flight_date == date(2022, 4, 20)
    assert row.travel_class == "Economy"


def test_find_by_ticket_returns_none_for_unknown(built):
    assert m.find_by_ticket(m.to_rows(built), "999") is None


def test_apply_result_returns_new_frame_and_leaves_input_untouched(built):
    result = ValidationResult(name=True, dob=True, person=False, boarding_pass=True, luggage=False)
    updated = m.apply_result(built, "34236751", result)
    assert updated is not built
    assert not built[m.VALIDATION_COLUMNS].to_numpy().any()
    row = updated[updated["TicketNo"] == "34236751"].iloc[0]
    assert row["NameValidation"] and row["DoBValidation"] and row["BoardingPassValidation"]
    assert not row["PersonValidation"]


def test_apply_result_unknown_ticket_raises(built):
    with pytest.raises(KeyError):
        m.apply_result(built, "999", ValidationResult.all_false())


def test_csv_round_trip(built, tmp_path):
    path = tmp_path / "manifest.csv"
    m.save_manifest(built, path)
    again = m.load_manifest(path)
    pd.testing.assert_frame_equal(again, built)
