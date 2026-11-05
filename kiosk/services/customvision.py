"""Azure AI Custom Vision: lighter object-detection project (Luggage Scan)."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateBatch, ImageFileCreateEntry, Region
from msrest.authentication import ApiKeyCredentials

from kiosk.config import setting

log = logging.getLogger(__name__)

PROJECT_NAME = "lighter-detection"
TAG_NAME = "lighter"
UPLOAD_BATCH = 64  # Custom Vision accepts at most 64 images per batch


def trainer() -> CustomVisionTrainingClient:
    creds = ApiKeyCredentials(in_headers={"Training-key": setting("CUSTOM_VISION_TRAINING_KEY")})
    return CustomVisionTrainingClient(setting("CUSTOM_VISION_TRAINING_ENDPOINT"), creds)


def predictor() -> CustomVisionPredictionClient:
    creds = ApiKeyCredentials(in_headers={"Prediction-key": setting("CUSTOM_VISION_PREDICTION_KEY")})
    return CustomVisionPredictionClient(setting("CUSTOM_VISION_PREDICTION_ENDPOINT"), creds)


def find_or_create_project(client: CustomVisionTrainingClient) -> Any:
    existing = next((p for p in client.get_projects() if p.name == PROJECT_NAME), None)
    if existing:
        return existing
    domain = next(d for d in client.get_domains() if d.type == "ObjectDetection" and d.name == "General")
    return client.create_project(PROJECT_NAME, description="Lighter detection in carry-on items", domain_id=domain.id)


def find_or_create_tag(client: CustomVisionTrainingClient, project_id: str) -> Any:
    return next((t for t in client.get_tags(project_id) if t.name == TAG_NAME), None) or client.create_tag(project_id, TAG_NAME)


def batches(items: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def upload_untagged(client: CustomVisionTrainingClient, project_id: str, images: Sequence[Path]) -> int:
    """Upload images without regions; boxes are drawn in the customvision.ai labeling UI."""
    uploaded = 0
    for chunk in batches(list(images), UPLOAD_BATCH):
        entries = [ImageFileCreateEntry(name=p.name, contents=p.read_bytes()) for p in chunk]
        result = client.create_images_from_files(project_id, ImageFileCreateBatch(images=entries))
        for image in result.images:
            if image.status not in ("OK", "OKDuplicate"):
                log.warning("upload %s: %s", image.source_url, image.status)
            else:
                uploaded += 1
    return uploaded


def replace_with_boxed_images(
    client: CustomVisionTrainingClient, project_id: str, tag_id: str, images: Sequence[Path], boxes: dict[str, list[dict[str, float]]]
) -> int:
    """Delete every image in the project and upload `images` again with their lighter regions.

    `boxes` maps file name -> [{left, top, width, height}] as fractions of the image size.
    """
    client.delete_images(project_id, all_images=True, all_iterations=True)
    uploaded = 0
    for chunk in batches([p for p in images if p.name in boxes], UPLOAD_BATCH):
        entries = [
            ImageFileCreateEntry(
                name=p.name,
                contents=p.read_bytes(),
                regions=[Region(tag_id=tag_id, **box) for box in boxes[p.name]],
            )
            for p in chunk
        ]
        result = client.create_images_from_files(project_id, ImageFileCreateBatch(images=entries))
        uploaded += sum(1 for image in result.images if image.status in ("OK", "OKDuplicate"))
    return uploaded


def max_tag_probability(predictions: Iterable[Any], tag: str = TAG_NAME) -> float:
    """Highest probability among predicted regions with the given tag; 0.0 when none."""
    return max((p.probability for p in predictions if p.tag_name == tag), default=0.0)


def predict_lighter(client: CustomVisionPredictionClient, project_id: str, image: Path) -> tuple[float, list[dict[str, Any]]]:
    with image.open("rb") as handle:
        result = client.detect_image(project_id, setting("CUSTOM_VISION_PUBLISHED_NAME"), handle)
    regions = [
        {"tag": p.tag_name, "probability": p.probability, "box": p.bounding_box.as_dict() if p.bounding_box else None}
        for p in result.predictions
    ]
    return max_tag_probability(result.predictions), regions
