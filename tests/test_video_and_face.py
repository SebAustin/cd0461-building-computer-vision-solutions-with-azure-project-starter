import pytest

from kiosk.services import face, videoindexer as vi

INDEX = {
    "state": "Processed",
    "videos": [
        {
            "insights": {
                "faces": [
                    {"id": 1, "name": "Unknown #1", "thumbnailId": "t-main", "thumbnails": [{"id": "t-a"}, {"id": "t-b"}]},
                    {"id": 2, "name": "Unknown #2", "thumbnailId": "t-other", "thumbnails": [{"id": "t-c"}]},
                ],
                "emotions": [
                    {"type": "Joy", "instances": [{"confidence": 0.8, "start": "0:00:01", "end": "0:00:04"}]},
                    {"type": "Sad", "instances": [{"confidence": 0.3, "start": "0:00:05", "end": "0:00:06"}]},
                ],
                "sentiments": [
                    {"sentimentType": "Positive", "averageScore": 0.9, "instances": [{"start": "0:00:00", "end": "0:00:10"}]},
                    {"sentimentType": "Negative", "averageScore": 0.2, "instances": [{"start": "0:00:10", "end": "0:00:12"}]},
                ],
            }
        }
    ],
}


def test_face_thumbnail_ids_lists_every_thumbnail_of_every_face():
    assert vi.face_thumbnail_ids(INDEX) == {1: ["t-a", "t-b"], 2: ["t-c"]}


def test_face_thumbnail_ids_falls_back_to_main_thumbnail():
    index = {"videos": [{"insights": {"faces": [{"id": 7, "thumbnailId": "t-x"}]}}]}
    assert vi.face_thumbnail_ids(index) == {7: ["t-x"]}


def test_face_thumbnail_ids_empty_when_no_faces():
    assert vi.face_thumbnail_ids({"videos": [{"insights": {}}]}) == {}


def test_feedback_picks_dominant_sentiment_by_duration():
    feedback = vi.passenger_feedback(INDEX)
    assert feedback["label"] == "positive"
    assert feedback["dominant_emotion"] == "Joy"
    assert feedback["sentiments"]["Positive"]["seconds"] == pytest.approx(10.0)
    assert feedback["emotions"]["Joy"]["max_confidence"] == 0.8


def test_feedback_negative_and_neutral():
    negative = {"videos": [{"insights": {"sentiments": [{"sentimentType": "Negative", "averageScore": 0.1, "instances": [{"start": "0:00:00", "end": "0:00:05"}]}]}}]}
    assert vi.passenger_feedback(negative)["label"] == "negative"
    empty = {"videos": [{"insights": {}}]}
    assert vi.passenger_feedback(empty) == {"label": "neutral", "dominant_emotion": None, "emotions": {}, "sentiments": {}}


@pytest.mark.parametrize("raw, seconds", [("0:00:04", 4.0), ("0:01:02.5", 62.5), ("1:00:00", 3600.0)])
def test_timestamp_seconds(raw, seconds):
    assert vi.seconds(raw) == pytest.approx(seconds)


def test_best_verification_takes_highest_confidence():
    results = [{"isIdentical": False, "confidence": 0.4}, {"isIdentical": True, "confidence": 0.82}]
    assert face.best_confidence(results) == 0.82
    assert face.best_confidence([]) is None


def test_single_face_rejects_zero_or_many():
    assert face.single_face_id([{"faceId": "a"}]) == "a"
    with pytest.raises(face.FaceError):
        face.single_face_id([])
    assert face.single_face_id([{"faceId": "a", "faceRectangle": {"width": 10, "height": 10}}, {"faceId": "b", "faceRectangle": {"width": 50, "height": 50}}]) == "b"
