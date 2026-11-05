"""Azure AI Face (REST v1.2): detect, verify, and a person group built from video face frames.

Person Validation compares the Digital ID face with faces from the Identity Video. Two measures:
  - verify:   ID face vs. each video thumbnail face (Face - Verify), best confidence wins
  - identify: a Person model ("person group") trained on the video thumbnails, queried with the ID face
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import requests

from kiosk.config import setting

log = logging.getLogger(__name__)

API = "face/v1.2"
DETECTION_MODEL = "detection_03"
RECOGNITION_MODEL = "recognition_04"
TIMEOUT_S = 30
TRAIN_POLL_S = 2
TRAIN_MAX_POLLS = 60


class FaceError(RuntimeError):
    pass


def _url(path: str) -> str:
    return f"{setting('FACE_ENDPOINT').rstrip('/')}/{API}/{path}"


def _headers(content_type: str = "application/json") -> dict[str, str]:
    return {"Ocp-Apim-Subscription-Key": setting("FACE_KEY"), "Content-Type": content_type}


def _call(method: str, path: str, **kwargs: Any) -> Any:
    response = requests.request(method, _url(path), timeout=TIMEOUT_S, **kwargs)
    if response.status_code >= 400:
        raise FaceError(f"{method} {path} -> {response.status_code}: {response.text[:300]}")
    return response.json() if response.content else None


def detect(image: bytes) -> list[dict[str, Any]]:
    params = {"detectionModel": DETECTION_MODEL, "recognitionModel": RECOGNITION_MODEL, "returnFaceId": "true"}
    return _call("POST", "detect", params=params, headers=_headers("application/octet-stream"), data=image)


def single_face_id(faces: Sequence[Mapping[str, Any]]) -> str:
    """The face to use from a detection: the only one, or the largest when several are found."""
    if not faces:
        raise FaceError("no face detected")
    if len(faces) == 1:
        return faces[0]["faceId"]
    largest = max(faces, key=lambda f: f["faceRectangle"]["width"] * f["faceRectangle"]["height"])
    return largest["faceId"]


def verify(face_id_1: str, face_id_2: str) -> dict[str, Any]:
    return _call("POST", "verify", headers=_headers(), json={"faceId1": face_id_1, "faceId2": face_id_2})


def best_confidence(results: Iterable[Mapping[str, Any]]) -> float | None:
    confidences = [r["confidence"] for r in results]
    return max(confidences) if confidences else None


def build_person_group(group_id: str, person_name: str, face_images: Iterable[bytes]) -> tuple[str, int]:
    """Create (or recreate) a person group with one person trained on the given face images."""
    if _exists(group_id):
        _call("DELETE", f"persongroups/{group_id}", headers=_headers())
    _call("PUT", f"persongroups/{group_id}", headers=_headers(), json={"name": group_id, "recognitionModel": RECOGNITION_MODEL})
    person_id = _call("POST", f"persongroups/{group_id}/persons", headers=_headers(), json={"name": person_name})["personId"]
    added = 0
    for image in face_images:
        try:
            _call(
                "POST",
                f"persongroups/{group_id}/persons/{person_id}/persistedfaces",
                params={"detectionModel": DETECTION_MODEL},
                headers=_headers("application/octet-stream"),
                data=image,
            )
            added += 1
        except FaceError as exc:
            log.warning("skipped a face frame: %s", exc)
    if added == 0:
        raise FaceError("no usable face frames for the person model")
    _call("POST", f"persongroups/{group_id}/train", headers=_headers())
    _wait_trained(group_id)
    return person_id, added


def _exists(group_id: str) -> bool:
    response = requests.get(_url(f"persongroups/{group_id}"), headers=_headers(), timeout=TIMEOUT_S)
    return response.status_code == 200


def _wait_trained(group_id: str) -> None:
    for _ in range(TRAIN_MAX_POLLS):
        status = _call("GET", f"persongroups/{group_id}/training", headers=_headers())["status"]
        if status == "succeeded":
            return
        if status == "failed":
            raise FaceError(f"person group {group_id} training failed")
        time.sleep(TRAIN_POLL_S)
    raise FaceError(f"person group {group_id} training timed out")


def identify(group_id: str, face_id: str) -> list[dict[str, Any]]:
    body = {"personGroupId": group_id, "faceIds": [face_id], "maxNumOfCandidatesReturned": 1, "confidenceThreshold": 0.0}
    return _call("POST", "identify", headers=_headers(), json=body)
