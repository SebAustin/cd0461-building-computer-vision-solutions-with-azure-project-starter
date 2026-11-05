"""Create the Blob containers and upload the manifest and input documents.

Usage: python -m scripts.upload_inputs
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from kiosk.services import storage

ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / "starter"
LUGGAGE_IMAGES = sorted((STARTER / "lighter_test_images").glob("lighter_test_set_*of5.jpg"))


def main() -> None:
    client = storage.service_client()
    created = storage.ensure_containers(client)
    logging.info("containers created: %s", created or "none (already existed)")

    storage.upload_file(client, "manifest", ROOT / "data/manifest/FlightManifest_initial.csv")
    truth = {k: v for k, v in json.loads((ROOT / "data/ground_truth.json").read_text()).items() if not k.startswith("_")}
    for passenger in truth.values():
        storage.upload_file(client, "digital-ids", STARTER / "digital_id_template" / passenger["digital_id"])
        storage.upload_file(client, "boarding-passes", STARTER / "boarding_pass_template" / passenger["boarding_pass"])
        if video := passenger.get("identity_video"):
            storage.upload_file(client, "identity-videos", STARTER / "digital-video-sample" / video)
    for image in LUGGAGE_IMAGES:
        storage.upload_file(client, "luggage-scans", image)

    for name in storage.CONTAINERS:
        logging.info("%-26s %s", name, storage.list_blobs(client, name))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("azure").setLevel(logging.WARNING)
    main()
