from types import SimpleNamespace

from kiosk.services import customvision as cv


def prediction(tag: str, probability: float) -> SimpleNamespace:
    return SimpleNamespace(tag_name=tag, probability=probability)


def test_max_tag_probability_picks_highest_lighter_region():
    preds = [prediction("lighter", 0.2), prediction("lighter", 0.91), prediction("other", 0.99)]
    assert cv.max_tag_probability(preds) == 0.91


def test_max_tag_probability_zero_when_nothing_found():
    assert cv.max_tag_probability([]) == 0.0


def test_batches_split_into_chunks_of_size():
    assert [list(b) for b in cv.batches(list(range(5)), 2)] == [[0, 1], [2, 3], [4]]
