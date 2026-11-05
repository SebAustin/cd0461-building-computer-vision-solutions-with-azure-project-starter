"""Run the Kiosk for every Passenger and write the final Flight Manifest.

Inputs
  - data/manifest/FlightManifest_initial.csv      (all Validations FALSE)
  - starter Digital IDs and Boarding Passes        (extracted with Document Intelligence; results cached)
  - data/out/person_matches.json  (optional)       {ticket_no: {"confidence": float|null, "source": str}}
  - data/out/luggage_scans.json   (optional)       {ticket_no: {"lighter_probability": float, "image": str}}

Outputs (local data/out/ and Blob)
  - FlightManifest_final.csv                       (manifest container)
  - <ticket>.json per passenger                    (kiosk-results container)

Usage: python -m scripts.run_kiosk [--refresh]   (--refresh re-runs extraction instead of using the cache)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from kiosk import manifest as m
from kiosk.models import LuggageScan, PersonMatch
from kiosk.pipeline import process_passenger
from kiosk.services import docintel, storage

ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / "starter"
OUT = ROOT / "data/out"
CACHE = OUT / "extracted"


def _cached(kind: str, ticket: str, refresh: bool, extract) -> dict:
    path = CACHE / kind / f"{ticket}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    _, raw = extract()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(raw, indent=1, default=str))
    return raw


def _load_optional(name: str) -> dict:
    path = OUT / name
    return json.loads(path.read_text()) if path.exists() else {}


def main(refresh: bool = False) -> None:
    truth = {k: v for k, v in json.loads((ROOT / "data/ground_truth.json").read_text()).items() if not k.startswith("_")}
    frame = m.load_manifest(ROOT / "data/manifest/FlightManifest_initial.csv")
    rows = m.to_rows(frame)
    persons, scans = _load_optional("person_matches.json"), _load_optional("luggage_scans.json")
    di = docintel.client()
    blob = storage.service_client()

    for ticket, files in truth.items():
        id_path = STARTER / "digital_id_template" / files["digital_id"]
        bp_path = STARTER / "boarding_pass_template" / files["boarding_pass"]
        id_doc = docintel.parse_id_document(_cached("ids", ticket, refresh, lambda: docintel.extract_id(id_path, di)))
        bp = docintel.parse_boarding_pass(_cached("boarding_passes", ticket, refresh, lambda: docintel.extract_boarding_pass(bp_path, di)))
        person = PersonMatch(**persons[ticket]) if ticket in persons else None
        scan = LuggageScan.scanned(**scans[ticket]) if ticket in scans else LuggageScan.not_scanned()

        outcome = process_passenger(rows, id_doc, bp, person, scan)
        if outcome.row is not None:
            frame = m.apply_result(frame, outcome.row.ticket_no, outcome.result)
        storage.upload_json(blob, "kiosk-results", f"{ticket}.json", outcome.summary())
        (OUT / "kiosk_results").mkdir(parents=True, exist_ok=True)
        (OUT / "kiosk_results" / f"{ticket}.json").write_text(json.dumps(outcome.summary(), indent=2, default=str))
        logging.info("\n=== %s (%s) %d/5 passed %s\n%s", files["name"], ticket, outcome.result.passed_count, outcome.result.as_dict(), outcome.message)

    final = m.save_manifest(frame, ROOT / "data/manifest/FlightManifest_final.csv")
    storage.upload_file(blob, "manifest", final)
    logging.info("\nfinal manifest:\n%s", frame[["TicketNo", "FirstName", "LastName", *m.VALIDATION_COLUMNS]].to_string(index=False))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("azure").setLevel(logging.WARNING)
    main(refresh="--refresh" in sys.argv)
