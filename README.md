# Automated Passenger Boarding Kiosk

Udacity *Building Computer Vision Solutions with Azure*, project submission. A kiosk reads a passenger's
digital ID, boarding pass and a short identity video, checks them against the flight manifest, and tells the passenger
whether to board. A separate luggage check detects lighters in carry-on images.

- **Deliverables per rubric step:** [`starter/sample_submission/`](starter/sample_submission)
- **Domain terms:** [GLOSSARY.md](GLOSSARY.md) · **Rules and thresholds:** [docs/validation-rules.md](docs/validation-rules.md)
- **Why current services instead of the 2022 ones:** [docs/adr/0001](docs/adr/0001-current-azure-services-over-retired-ones.md)
- **Walkthrough with live outputs:** [notebooks/kiosk_walkthrough.ipynb](notebooks/kiosk_walkthrough.ipynb)

## Azure services

| Need | Service |
|---|---|
| Digital ID fields | Document Intelligence `prebuilt-idDocument` |
| Boarding pass fields | Document Intelligence custom template model `boarding-pass-v1` |
| Faces, emotions, sentiment from video | Video Indexer |
| ID face vs. video face | Face (person group identify + verify) |
| Lighter detection | Custom Vision object detection |
| Inputs, training data, results | Blob Storage |

## Setup

```bash
uv venv -p 3.11 .venv && uv pip install -p .venv -r requirements-dev.txt
cp .env.example .env   # fill in endpoints and keys; never commit .env
```

Video Indexer tokens come from the Azure CLI login (`az login`).

## Run order

```bash
python -m scripts.build_manifest              # initial manifest, all validations FALSE
python -m scripts.upload_inputs               # Blob containers + inputs
python -m scripts.generate_training_passes 12 # synthetic training passes (needs LibreOffice)
python -m scripts.train_boarding_pass_model   # label, upload, train boarding-pass-v1
python -m scripts.analyze_identity_video      # Video Indexer + Face → person match, feedback
python -m scripts.lighter_detection upload-boxes && python -m scripts.lighter_detection train-advanced 1
python -m scripts.lighter_detection predict   # luggage scans
python -m scripts.run_kiosk                   # validations, kiosk messages, final manifest
pytest --cov=kiosk                            # unit tests (no Azure calls)
scripts/teardown.sh --yes                     # after taking the consumption screenshots
```

## Layout

```
kiosk/            domain: models, normalize, validators, messages, manifest, pipeline, labeling
kiosk/services/   thin Azure wrappers: docintel, storage, face, videoindexer, customvision
scripts/          one script per pipeline step
data/             ground truth, manifests, training passes, lighter boxes (data/out/ is git-ignored)
tests/            pytest, with recorded service responses in tests/fixtures/
docs/             glossary-backed spec, ADR, sources of the submission PDFs
```

## License

[License](LICENSE.txt)
