from datetime import date

import pytest

from kiosk.models import BoardingPass, IdDocument, ManifestRow


@pytest.fixture
def avkash_row() -> ManifestRow:
    return ManifestRow(
        ticket_no="34236751",
        first_name="Avkash",
        last_name="Chauhan",
        date_of_birth=date(1990, 1, 1),
        sex="M",
        carrier="UA",
        flight_no="234",
        travel_class="Economy",
        origin="San Francisco",
        destination="Chicago",
        flight_date=date(2022, 4, 20),
        boarding_time="10:00 AM PST",
        seat="20A",
        gate="G1",
        baggage="No",
    )


@pytest.fixture
def avkash_id() -> IdDocument:
    return IdDocument(first_name="AVKASH CHAUHAN", last_name="CHAUHAN", date_of_birth="01/01/1990", sex="M")


@pytest.fixture
def avkash_pass() -> BoardingPass:
    return BoardingPass(
        passenger_name="Avkash Chauhan",
        carrier="UA",
        flight_no="234",
        travel_class="E",
        origin="San Francisco",
        destination="Chicago",
        flight_date="April 20, 2022",
        boarding_time="10:00 AM PST",
        seat="20A",
        ticket_no="ETK-34236751E",
    )
