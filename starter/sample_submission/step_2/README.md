# Step 2: Text data extraction (Document Intelligence, formerly Form Recognizer)

| Rubric item | Where |
|---|---|
| Code: prebuilt ID API on the digital ID | [`kiosk/services/docintel.py`](../../../kiosk/services/docintel.py) (`extract_id`, `parse_id_document`) · notebook cell "Step 2a" |
| Screenshot: extracted ID data matches the ID | **TODO (you):** run notebook cell "Step 2a" and screenshot it (ID image + extracted fields) |
| Boarding passes used to generate labels; passes + labels in Blob | 12 synthetic passes from the template (`scripts/generate_training_passes.py`), labeled in code (`kiosk/labeling.py`, `scripts/train_boarding_pass_model.py`) → container `training-boarding-passes`. **TODO (you):** screenshot that container in the portal (PDF + `.labels.json` + `.ocr.json` + `fields.json`) |
| Code: training the custom model | [`scripts/train_boarding_pass_model.py`](../../../scripts/train_boarding_pass_model.py) (`begin_build_document_model`, template mode) · model card [boarding_pass_model.json](boarding_pass_model.json) |
| Code: custom model extracting boarding passes | `docintel.extract_boarding_pass` · notebook cell "Step 2b" |
| Screenshot: extracted data matches the boarding pass | **TODO (you):** notebook cell "Step 2b" next to `boarding-avkash.pdf` |
| All extracted values | [extracted_fields.json](extracted_fields.json) |

The brief's labeling site (FOTT) has been retired. Document Intelligence Studio and the build API read the same `*.labels.json` / `*.ocr.json` files from Blob, so the labels were written in that format directly.
