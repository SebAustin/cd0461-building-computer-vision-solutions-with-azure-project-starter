# Step 5: Validation and metrics monitoring

| Rubric item | Where |
|---|---|
| Python libraries | [python_libraries.txt](python_libraries.txt) (pinned; dev extras: pytest, pytest-cov, jupyter) |
| Face match % (video vs ID) | [face_match.json](face_match.json): **95.7%** (person model identify); best direct verify 95.8%; threshold 65% |
| Code: validations from all data, stored in the manifest | [`kiosk/validators.py`](../../../kiosk/validators.py), [`kiosk/pipeline.py`](../../../kiosk/pipeline.py), [`kiosk/manifest.py`](../../../kiosk/manifest.py) `apply_result`, [`scripts/run_kiosk.py`](../../../scripts/run_kiosk.py) |
| Final manifest | [FlightManifest_final.csv](FlightManifest_final.csv) (also uploaded to Blob `manifest/`) |
| Screenshots: successful validations / error messages | [kiosk_messages.txt](kiosk_messages.txt), [kiosk_results/](kiosk_results) · **TODO (you):** screenshot notebook "Step 5" |
| Screenshots: Service Consumption Report | **TODO (you):** Azure portal → each resource → Monitoring → Metrics (Total Calls, Latency, Errors): `kiosk-formrecognizer-1aq`, `kiosk-face-305856`, `kiosk-training-305856`, `kiosk-prediction-305856`, `kiosk-vi-305856`, `kioskst1aqrpsihqh`. Take these **before** `scripts/teardown.sh --yes` |
| Final reflection | [final_reflection.pdf](final_reflection.pdf) |

At least 3 of 5 validations pass for every passenger except James Webb, whose manifest DoB is deliberately one day off to demonstrate the ID-mismatch message.
Luggage is a simulated scan: test image N belongs to passenger N. Avkash (6th) is "not scanned", so his message has no luggage sentence.
