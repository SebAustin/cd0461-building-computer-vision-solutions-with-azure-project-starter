"""Identity Video analysis for one Passenger: Video Indexer faces + feedback, Face API matching.

  1. Upload the local MP4 to Video Indexer and wait for indexing
  2. Download every face thumbnail Video Indexer extracted
  3. Build a Person model (Face person group) from those thumbnails
  4. Detect the face on the Digital ID; identify it against the Person model and verify it
     against each thumbnail
  5. Save the Person match (data/out/person_matches.json) and the Passenger Feedback

Usage: python -m scripts.analyze_identity_video [ticket_no]   (default: Avkash, 34236751)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from kiosk.services import face, storage
from kiosk.services import videoindexer as vi

ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / "starter"
OUT = ROOT / "data/out"


def _index(video: Path, ticket: str, token: str) -> tuple[str, dict]:
    cache = OUT / "video" / f"{ticket}_index.json"
    if cache.exists():
        index = json.loads(cache.read_text())
        return index["id"], index
    video_id = vi.upload_video(video, token, name=f"identity-{ticket}")
    logging.info("uploaded %s to Video Indexer as %s", video.name, video_id)
    index = vi.wait_for_index(video_id, token)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(index, indent=1))
    return video_id, index


def _thumbnails(video_id: str, index: dict, ticket: str, token: str) -> list[Path]:
    folder = OUT / "video" / f"{ticket}_faces"
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for face_id, thumb_ids in vi.face_thumbnail_ids(index).items():
        for thumb_id in thumb_ids:
            path = folder / f"face{face_id}_{thumb_id}.jpg"
            if not path.exists():
                path.write_bytes(vi.thumbnail(video_id, thumb_id, token))
            paths.append(path)
    return paths


def _merge_json(path: Path, key: str, value: dict) -> None:
    data = json.loads(path.read_text()) if path.exists() else {}
    path.write_text(json.dumps({**data, key: value}, indent=2))


def main(ticket: str = "34236751") -> None:
    truth = json.loads((ROOT / "data/ground_truth.json").read_text())[ticket]
    video = STARTER / "digital-video-sample" / truth["identity_video"]
    id_image = STARTER / "digital_id_template" / truth["digital_id"]

    token = vi.access_token()
    video_id, index = _index(video, ticket, token)
    thumbs = _thumbnails(video_id, index, ticket, token)
    logging.info("Video Indexer found %d face(s), %d thumbnail(s)", len(vi.face_thumbnail_ids(index)), len(thumbs))

    id_face = face.single_face_id(face.detect(id_image.read_bytes()))
    group_id = f"passenger-{ticket}"
    person_id, faces_added = face.build_person_group(group_id, truth["name"], (p.read_bytes() for p in thumbs))
    candidates = face.identify(group_id, id_face)[0]["candidates"]
    identify_conf = next((c["confidence"] for c in candidates if c["personId"] == person_id), 0.0)

    verifications = []
    for thumb in thumbs:
        try:
            thumb_face = face.single_face_id(face.detect(thumb.read_bytes()))
            verifications.append({"thumbnail": thumb.name, **face.verify(id_face, thumb_face)})
        except face.FaceError as exc:
            logging.warning("%s: %s", thumb.name, exc)
    best_verify = face.best_confidence(verifications)

    logging.info("Person model: %d face frames; identify confidence %.3f", faces_added, identify_conf)
    logging.info("Verify ID vs thumbnails: best %.3f over %d frames", best_verify or 0.0, len(verifications))

    match = {"confidence": identify_conf, "source": "face-person-group-identify"}
    _merge_json(OUT / "person_matches.json", ticket, match)
    feedback = vi.passenger_feedback(index)
    report = {
        "ticket_no": ticket,
        "video_indexer_video_id": video_id,
        "person_model": {"person_group": group_id, "face_frames": faces_added, "identify_confidence": identify_conf},
        "verify": {"best_confidence": best_verify, "per_thumbnail": verifications},
        "passenger_feedback": feedback,
    }
    (OUT / "video" / f"{ticket}_identity_report.json").write_text(json.dumps(report, indent=2))
    storage.upload_json(storage.service_client(), "kiosk-results", f"{ticket}_identity_report.json", report)
    logging.info("Passenger Feedback: %s", json.dumps(feedback, indent=1))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("azure").setLevel(logging.WARNING)
    main(*sys.argv[1:2])
