"""Lighter detection with Custom Vision: check labeling, train + publish, predict the Luggage Scans.

Usage:
  python -m scripts.lighter_detection status    # how many images have boxes
  python -m scripts.lighter_detection train     # train, report precision/recall/mAP, publish
  python -m scripts.lighter_detection train-advanced 1   # Advanced training with a 1-hour budget
  python -m scripts.lighter_detection predict   # score the 5 test images, write luggage_scans.json
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

from kiosk.config import setting
from kiosk.services import customvision as cv
from kiosk.services import storage

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/out"
TEST_IMAGES = sorted((ROOT / "starter/lighter_test_images").glob("lighter_test_set_*of5.jpg"))
MIN_TAGGED = 15
MIN_PRECISION = 0.75
POLL_S = 10


def status() -> int:
    client = cv.trainer()
    project_id = setting("CUSTOM_VISION_PROJECT_ID")
    tagged, untagged = client.get_tagged_image_count(project_id), client.get_untagged_image_count(project_id)
    logging.info("tagged images: %d, untagged: %d", tagged, untagged)
    return tagged


def upload_boxes() -> None:
    """Re-upload the training images with the lighter boxes from data/lighter_boxes.json."""
    client = cv.trainer()
    project_id = setting("CUSTOM_VISION_PROJECT_ID")
    tag = cv.find_or_create_tag(client, project_id)
    boxes = json.loads((ROOT / "data/lighter_boxes.json").read_text())
    images = sorted((ROOT / "starter/lighter_images").iterdir())
    uploaded = cv.replace_with_boxed_images(client, project_id, tag.id, images, boxes)
    logging.info("uploaded %d images with %d boxes", uploaded, sum(map(len, boxes.values())))
    status()


def publish(client, project_id: str, iteration_id: str) -> None:
    """Publish an iteration under the configured name, moving the name off any older iteration first."""
    name = setting("CUSTOM_VISION_PUBLISHED_NAME")
    for old in client.get_iterations(project_id):
        if old.publish_name == name and old.id != iteration_id:
            client.unpublish_iteration(project_id, old.id)
            logging.info("unpublished %s", old.name)
    client.publish_iteration(project_id, iteration_id, name, setting("CUSTOM_VISION_PREDICTION_RESOURCE_ID"))


def train(advanced_hours: int = 0) -> None:
    """Train an iteration. advanced_hours > 0 uses Advanced training with that budget (slower, usually better recall)."""
    client = cv.trainer()
    project_id = setting("CUSTOM_VISION_PROJECT_ID")
    if status() < MIN_TAGGED:
        raise SystemExit(f"label at least {MIN_TAGGED} images on customvision.ai before training")
    if advanced_hours:
        iteration = client.train_project(project_id, training_type="Advanced", reserved_budget_in_hours=advanced_hours)
    else:
        iteration = client.train_project(project_id)
    while iteration.status not in ("Completed", "Failed"):
        logging.info("training: %s", iteration.status)
        time.sleep(POLL_S)
        iteration = client.get_iteration(project_id, iteration.id)
    if iteration.status == "Failed":
        raise SystemExit("training failed")
    perf = client.get_iteration_performance(project_id, iteration.id, threshold=0.5, overlap_threshold=0.3)
    metrics = {"iteration": iteration.name, "precision": perf.precision, "recall": perf.recall, "mAP": perf.average_precision}
    logging.info("performance @50%% probability: %s", metrics)
    if perf.precision < MIN_PRECISION:
        logging.warning("precision %.2f is below %.2f: label more images or tighten boxes, then retrain", perf.precision, MIN_PRECISION)
    publish(client, project_id, iteration.id)
    endpoint = f"{setting('CUSTOM_VISION_PREDICTION_ENDPOINT').rstrip('/')}/customvision/v3.0/Prediction/{project_id}/detect/iterations/{setting('CUSTOM_VISION_PUBLISHED_NAME')}/image"
    logging.info("published %s as '%s'\nprediction endpoint: %s", iteration.name, setting("CUSTOM_VISION_PUBLISHED_NAME"), endpoint)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "lighter_model.json").write_text(json.dumps({**metrics, "prediction_endpoint": endpoint}, indent=2))


def predict() -> None:
    """Score the test images. Simulated scan: image N belongs to the Nth Passenger on the Manifest."""
    client = cv.predictor()
    project_id = setting("CUSTOM_VISION_PROJECT_ID")
    tickets = list(k for k in json.loads((ROOT / "data/ground_truth.json").read_text()) if not k.startswith("_"))
    scans, details = {}, {}
    for ticket, image in zip(tickets, TEST_IMAGES):
        probability, regions = cv.predict_lighter(client, project_id, image)
        scans[ticket] = {"lighter_probability": probability, "image": image.name}
        details[image.name] = {"ticket_no": ticket, "max_lighter_probability": probability, "regions": regions}
        logging.info("%s -> ticket %s: lighter probability %.1f%%", image.name, ticket, probability * 100)
    (OUT / "luggage_scans.json").write_text(json.dumps(scans, indent=2))
    (OUT / "lighter_predictions.json").write_text(json.dumps(details, indent=2))
    storage.upload_json(storage.service_client(), "kiosk-results", "lighter_predictions.json", details)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("azure").setLevel(logging.WARNING)
    commands = {
        "status": status,
        "upload-boxes": upload_boxes,
        "train": train,
        "train-advanced": lambda: train(advanced_hours=int(sys.argv[2]) if len(sys.argv) > 2 else 1),
        "predict": predict,
    }
    commands[sys.argv[1] if len(sys.argv) > 1 else "status"]()
