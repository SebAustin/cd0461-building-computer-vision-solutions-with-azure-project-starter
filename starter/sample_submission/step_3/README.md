# Step 3: Face data extraction (Video Indexer, formerly Video Analyzer, and Face)

| Rubric item | Where |
|---|---|
| Code: upload the local video to Video Indexer | [`kiosk/services/videoindexer.py`](../../../kiosk/services/videoindexer.py) `upload_video` · [`scripts/analyze_identity_video.py`](../../../scripts/analyze_identity_video.py) |
| Code: face thumbnails extracted from Video Indexer | `vi.face_thumbnail_ids`, `vi.thumbnail` → [face_thumbnails/](face_thumbnails) (7 frames) |
| Code: Person model from the face frames | [`kiosk/services/face.py`](../../../kiosk/services/face.py) `build_person_group` (Face person group trained on the 7 frames) |
| Code: emotion and sentiment from Video Indexer | `vi.passenger_feedback` → `passenger_feedback` in [identity_report.json](identity_report.json) |
| Code: face extracted from the digital ID (Face API) | `face.detect` + `face.single_face_id` on `ca-dl-avkash.png` |
| Screenshots | **TODO (you):** notebook section "Step 3" |

Result: the ID face matches the video Person model at **95.7%** (identify) and **95.8%** (best direct verify). The threshold is 65%.
Feedback is *neutral*: Video Indexer derives emotions from speech, and this video has none.
