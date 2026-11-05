"""Label the Training Boarding Passes, upload them to Blob, and train the custom template model.

Steps:
  1. Run prebuilt-layout on each training PDF  -> <pdf>.ocr.json (what Studio stores)
  2. Locate each known value on the page          -> <pdf>.labels.json + fields.json
  3. Upload PDFs and label files to the `training-boarding-passes` container
  4. Build a template model from that container (read/list SAS URL)

Usage: python -m scripts.train_boarding_pass_model
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from azure.ai.documentintelligence import DocumentIntelligenceAdministrationClient
from azure.ai.documentintelligence.models import AzureBlobContentSource, BuildDocumentModelRequest, DocumentBuildMode
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import ContainerSasPermissions, generate_container_sas

from kiosk import labeling
from kiosk.config import setting
from kiosk.services import docintel, storage

ROOT = Path(__file__).resolve().parents[1]
PASS_DIR = ROOT / "data/training_boarding_passes"
CONTAINER = "training-boarding-passes"

# Training-pass attribute -> label name used by the model (kiosk.services.docintel.BOARDING_PASS_FIELDS).
VALUE_TO_LABEL = {
    "name": "PassengerName",
    "carrier": "Carrier",
    "flight_no": "FlightNo",
    "travel_class": "Class",
    "origin": "From",
    "destination": "To",
    "date": "Date",
    "boarding_time": "BoardingTime",
    "seat": "Seat",
    "ticket": "TicketNo",
}


def label_all(di) -> dict[str, list[str]]:
    values = json.loads((PASS_DIR / "values.json").read_text())
    missing_by_doc = {}
    for pdf_name, data in values.items():
        pdf = PASS_DIR / pdf_name
        layout = docintel.analyze(pdf, "prebuilt-layout", di)
        expected = {label: data[attr] for attr, label in VALUE_TO_LABEL.items()}
        labels, missing = labeling.build_labels(pdf_name, layout["pages"], expected)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        (PASS_DIR / f"{pdf_name}.ocr.json").write_text(json.dumps(labeling.ocr_document(layout, stamp), default=str))
        (PASS_DIR / f"{pdf_name}.labels.json").write_text(json.dumps(labels, indent=1))
        missing_by_doc[pdf_name] = missing
        logging.info("%s: %d labels, missing %s", pdf_name, len(labels["labels"]), missing or "none")
    (PASS_DIR / "fields.json").write_text(json.dumps(labeling.fields_schema(list(VALUE_TO_LABEL.values())), indent=1))
    return missing_by_doc


def upload_all(client) -> None:
    for path in sorted(PASS_DIR.iterdir()):
        if path.suffix in {".pdf", ".json"} and path.name != "values.json":
            storage.upload_file(client, CONTAINER, path)


def container_sas_url(client) -> str:
    account = client.account_name
    key = client.credential.account_key
    sas = generate_container_sas(
        account,
        CONTAINER,
        account_key=key,
        permission=ContainerSasPermissions(read=True, list=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    return f"https://{account}.blob.core.windows.net/{CONTAINER}?{sas}"


def main() -> None:
    di = docintel.client()
    missing = label_all(di)
    incomplete = {doc: fields for doc, fields in missing.items() if fields}
    if incomplete:
        raise SystemExit(f"labels incomplete, fix before training: {incomplete}")

    blob = storage.service_client()
    upload_all(blob)

    admin = DocumentIntelligenceAdministrationClient(setting("DOCINTEL_ENDPOINT"), AzureKeyCredential(setting("DOCINTEL_KEY")))
    model_id = setting("BOARDING_PASS_MODEL_ID")
    request = BuildDocumentModelRequest(
        model_id=model_id,
        build_mode=DocumentBuildMode.TEMPLATE,
        description="Udacity boarding pass extractor (template model, synthetic training passes)",
        azure_blob_source=AzureBlobContentSource(container_url=container_sas_url(blob)),
    )
    model = admin.begin_build_document_model(request).result()
    doc_type = next(iter(model.doc_types.values()))
    logging.info("trained model %s; field confidence: %s", model.model_id, json.dumps(doc_type.field_confidence, indent=1))
    (ROOT / "data/out").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/out/boarding_pass_model.json").write_text(json.dumps(model.as_dict(), indent=1, default=str))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("azure").setLevel(logging.WARNING)
    main()
