"""Azure AI Video Indexer (successor of Azure Video Analyzer): upload, index, face thumbnails, feedback.

Access tokens come from the ARM `generateAccessToken` action, authenticated with the Azure CLI login.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import requests
from azure.identity import AzureCliCredential

from kiosk.config import setting

log = logging.getLogger(__name__)

API = "https://api.videoindexer.ai"
ARM = "https://management.azure.com"
ARM_API_VERSION = "2024-01-01"
TIMEOUT_S = 60
POLL_S = 10
MAX_POLLS = 90


class VideoIndexerError(RuntimeError):
    pass


def access_token() -> str:
    arm_token = AzureCliCredential().get_token(f"{ARM}/.default").token
    url = f"{ARM}{setting('VIDEO_INDEXER_ARM_RESOURCE_ID')}/generateAccessToken?api-version={ARM_API_VERSION}"
    response = requests.post(
        url,
        headers={"Authorization": f"Bearer {arm_token}"},
        json={"permissionType": "Contributor", "scope": "Account"},
        timeout=TIMEOUT_S,
    )
    if response.status_code >= 400:
        raise VideoIndexerError(f"generateAccessToken -> {response.status_code}: {response.text[:300]}")
    return response.json()["accessToken"]


def _account_url(path: str) -> str:
    return f"{API}/{setting('VIDEO_INDEXER_LOCATION')}/Accounts/{setting('VIDEO_INDEXER_ACCOUNT_ID')}/{path}"


def _get(path: str, token: str, **params: Any) -> requests.Response:
    response = requests.get(_account_url(path), params={"accessToken": token, **params}, timeout=TIMEOUT_S)
    if response.status_code >= 400:
        raise VideoIndexerError(f"GET {path} -> {response.status_code}: {response.text[:300]}")
    return response


def upload_video(path: Path, token: str, name: str) -> str:
    """Upload a local video file and start indexing; returns the video id."""
    params = {"accessToken": token, "name": name, "privacy": "Private", "indexingPreset": "Advanced"}
    with path.open("rb") as handle:
        response = requests.post(_account_url("Videos"), params=params, files={"file": (path.name, handle, "video/mp4")}, timeout=600)
    if response.status_code >= 400:
        raise VideoIndexerError(f"upload -> {response.status_code}: {response.text[:300]}")
    return response.json()["id"]


def wait_for_index(video_id: str, token: str) -> dict[str, Any]:
    for _ in range(MAX_POLLS):
        index = _get(f"Videos/{video_id}/Index", token).json()
        state = index.get("state")
        if state == "Processed":
            return index
        if state == "Failed":
            raise VideoIndexerError(f"indexing failed for {video_id}")
        log.info("video %s: %s %s", video_id, state, index.get("videos", [{}])[0].get("processingProgress", ""))
        time.sleep(POLL_S)
    raise VideoIndexerError(f"indexing timed out for {video_id}")


def thumbnail(video_id: str, thumbnail_id: str, token: str) -> bytes:
    return _get(f"Videos/{video_id}/Thumbnails/{thumbnail_id}", token, format="Jpeg").content


def _insights(index: Mapping[str, Any]) -> Mapping[str, Any]:
    videos = index.get("videos") or [{}]
    return videos[0].get("insights") or {}


def face_thumbnail_ids(index: Mapping[str, Any]) -> dict[int, list[str]]:
    """Face id -> thumbnail ids for every face Video Indexer found."""
    faces = {}
    for face in _insights(index).get("faces") or []:
        ids = [t["id"] for t in face.get("thumbnails") or []] or [face["thumbnailId"]]
        faces[face["id"]] = ids
    return faces


def seconds(timestamp: str) -> float:
    hours, minutes, secs = timestamp.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(secs)


def _duration(instances: list[Mapping[str, Any]]) -> float:
    return sum(seconds(i["end"]) - seconds(i["start"]) for i in instances)


def passenger_feedback(index: Mapping[str, Any]) -> dict[str, Any]:
    """Emotions, sentiments and a positive/negative/neutral label from the dominant sentiment."""
    insights = _insights(index)
    emotions: dict[str, dict[str, float]] = {}
    for emotion in insights.get("emotions") or []:
        instances = emotion.get("instances") or []
        emotions[emotion["type"]] = {
            "seconds": _duration(instances),
            "max_confidence": max((i.get("confidence", 0.0) for i in instances), default=0.0),
        }
    sentiments: dict[str, dict[str, float]] = defaultdict(dict)
    for sentiment in insights.get("sentiments") or []:
        sentiments[sentiment["sentimentType"]] = {
            "seconds": _duration(sentiment.get("instances") or []),
            "average_score": sentiment.get("averageScore", 0.0),
        }
    dominant_sentiment = max(sentiments, key=lambda s: sentiments[s]["seconds"], default=None)
    label = {"Positive": "positive", "Negative": "negative"}.get(dominant_sentiment or "", "neutral")
    dominant_emotion = max(emotions, key=lambda e: emotions[e]["seconds"], default=None)
    return {"label": label, "dominant_emotion": dominant_emotion, "emotions": emotions, "sentiments": dict(sentiments)}
