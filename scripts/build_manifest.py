"""Build the initial Flight Manifest (all Validations FALSE) from the starter CSV.

Usage: python -m scripts.build_manifest
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from kiosk.manifest import build_manifest, save_manifest

ROOT = Path(__file__).resolve().parents[1]
STARTER_CSV = ROOT / "starter/flight-manifest-csv/FlightManifest.csv"
GROUND_TRUTH = ROOT / "data/ground_truth.json"
OUTPUT = ROOT / "data/manifest/FlightManifest_initial.csv"


def main() -> None:
    truth = {k: v for k, v in json.loads(GROUND_TRUTH.read_text()).items() if not k.startswith("_")}
    manifest = build_manifest(pd.read_csv(STARTER_CSV), truth)
    path = save_manifest(manifest, OUTPUT)
    logging.info("wrote %s (%d passengers)", path, len(manifest))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
