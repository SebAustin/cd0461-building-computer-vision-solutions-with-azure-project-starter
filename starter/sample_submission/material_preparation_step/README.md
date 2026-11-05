# Project starter material

| Rubric item | Where |
|---|---|
| Flight manifest (CSV), ≥ 5 passengers, validations FALSE | [FlightManifest_initial.csv](FlightManifest_initial.csv) (6 passengers; built by `scripts/build_manifest.py` from the starter CSV + hand-read DoB/Sex in `data/ground_truth.json`) |
| 5+ boarding passes (PDF) | [boarding_passes/](boarding_passes) (6) |
| 5+ digital IDs (image) | [digital_ids/](digital_ids) (6) |
| 30-second MP4 video | [avkash-boarding-pass.mp4](avkash-boarding-pass.mp4) (matches `ca-dl-avkash.png`) |
| Screenshot: Azure Storage resources | **TODO (you):** Azure portal → storage account `kioskst1aqrpsihqh` → Containers (7 containers) |
| Screenshot: manifest stored in Blob | **TODO (you):** container `manifest` → `FlightManifest_initial.csv` |

Note: James Webb's `DateOfBirth` is deliberately one day off from his ID (1970-12-16 vs 1970-12-15) to demonstrate a failed DoB Validation.
Uploads: `python -m scripts.upload_inputs`.
