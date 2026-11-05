"""Build Document Intelligence Studio label files (*.labels.json, fields.json) from layout results.

Given the words the layout model found on a page and the value we know is printed there,
locate the value's words and record their normalized bounding boxes, exactly as the
Studio labeling UI would.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from kiosk.normalize import text_key


def find_span(words: Sequence[Mapping[str, Any]], value: str) -> list[int] | None:
    """Indices of the first contiguous run of words whose text equals `value` (case/punctuation-insensitive)."""
    target = text_key(value).split()
    if not target:
        return None
    tokens = [text_key(w["content"]).split() for w in words]
    for start in range(len(tokens)):
        collected: list[str] = []
        for end in range(start, len(tokens)):
            collected += tokens[end]
            if collected == target:
                return list(range(start, end + 1))
            if collected != target[: len(collected)]:
                break
    return None


def label_entry(label: str, page: Mapping[str, Any], indices: Sequence[int]) -> dict[str, Any]:
    width, height = page["width"], page["height"]
    values = []
    for i in indices:
        word = page["words"][i]
        polygon = word["polygon"]
        box = [coord / (width if axis % 2 == 0 else height) for axis, coord in enumerate(polygon)]
        values.append({"page": page["pageNumber"], "text": word["content"], "boundingBoxes": [box]})
    return {"label": label, "key": None, "value": values}


def build_labels(
    document: str, pages: Sequence[Mapping[str, Any]], expected: Mapping[str, str]
) -> tuple[dict[str, Any], list[str]]:
    """Labels for every expected field found on the document, plus the fields that were not found."""
    labels, missing = [], []
    for field, value in expected.items():
        hit = next(((page, span) for page in pages if (span := find_span(page.get("words", []), value))), None)
        if hit is None:
            missing.append(field)
        else:
            labels.append(label_entry(field, hit[0], hit[1]))
    # No "$schema" key: the 2024-11-30 build API rejects label files that carry one ("Generic error during processing labels").
    return {"document": document, "labels": labels}, missing


def fields_schema(field_names: Sequence[str]) -> dict[str, Any]:
    return {"fields": [{"fieldKey": name, "fieldType": "string", "fieldFormat": "not-specified"} for name in field_names]}


def ocr_document(analyze_result: Mapping[str, Any], timestamp: str) -> dict[str, Any]:
    """Wrap a layout result the way Studio stores it in <document>.ocr.json."""
    return {"status": "succeeded", "createdDateTime": timestamp, "lastUpdatedDateTime": timestamp, "analyzeResult": analyze_result}
