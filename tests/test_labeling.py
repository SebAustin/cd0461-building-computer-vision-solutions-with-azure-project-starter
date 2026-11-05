import pytest

from kiosk import labeling


def word(text: str, x: float) -> dict:
    return {"content": text, "polygon": [x, 1.0, x + 0.5, 1.0, x + 0.5, 1.2, x, 1.2]}


PAGE = {"pageNumber": 1, "width": 11.0, "height": 8.5, "words": [
    word("ETK-50007919E", 9.0), word("Passenger", 1.0), word("Name", 1.6),
    word("Grace", 1.0), word("Brown,", 1.6), word("AA", 4.0), word("533", 5.0),
    word("From:", 1.0), word("Boston", 1.6), word("Grace", 7.0), word("Brown", 7.6),
]}  # fmt: skip


def test_find_span_matches_contiguous_words_first_occurrence():
    assert labeling.find_span(PAGE["words"], "Grace Brown") == [3, 4]


def test_find_span_ignores_punctuation_and_case():
    assert labeling.find_span(PAGE["words"], "boston") == [8]


def test_find_span_handles_words_containing_punctuation():
    words = [word("GATE", 1.0), word("10:00", 2.0), word("PM", 3.0), word("CST", 4.0)]
    assert labeling.find_span(words, "10:00 PM CST") == [1, 2, 3]
    assert labeling.find_span(PAGE["words"], "ETK-50007919E") == [0]


def test_find_span_returns_none_when_absent():
    assert labeling.find_span(PAGE["words"], "Phoenix") is None


def test_label_entry_normalizes_polygons_to_page_size():
    entry = labeling.label_entry("Carrier", PAGE, [5])
    assert entry["label"] == "Carrier"
    assert entry["key"] is None
    (value,) = entry["value"]
    assert value["page"] == 1 and value["text"] == "AA"
    box = value["boundingBoxes"][0]
    assert box[0] == pytest.approx(4.0 / 11.0)
    assert box[1] == pytest.approx(1.0 / 8.5)


def test_build_labels_reports_missing_fields():
    labels, missing = labeling.build_labels("pass.pdf", [PAGE], {"PassengerName": "Grace Brown", "To": "Phoenix"})
    assert set(labels) == {"document", "labels"}  # a "$schema" key makes the build API reject the file
    assert labels["document"] == "pass.pdf"
    assert [lab["label"] for lab in labels["labels"]] == ["PassengerName"]
    assert missing == ["To"]


def test_fields_schema_lists_every_field_as_string():
    schema = labeling.fields_schema(["A", "B"])
    assert [f["fieldKey"] for f in schema["fields"]] == ["A", "B"]
    assert {f["fieldType"] for f in schema["fields"]} == {"string"}
    assert set(schema) == {"fields"}


def test_ocr_document_wraps_result_with_timestamps():
    doc = labeling.ocr_document({"pages": []}, "2026-11-05T00:00:00Z")
    assert doc["status"] == "succeeded"
    assert doc["createdDateTime"] == doc["lastUpdatedDateTime"] == "2026-11-05T00:00:00Z"
    assert doc["analyzeResult"] == {"pages": []}
