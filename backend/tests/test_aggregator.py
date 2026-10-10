"""Unit tests for temporal detection aggregation and score smoothing."""
import pytest
from app.classifier.aggregator import aggregate_detections
from app.classifier.types import Detection, ScoreBand


def make_det(start: float, end: float, label: str, score: float, fixture: bool = True) -> Detection:
    return Detection(
        start_time=start,
        end_time=end,
        label=label,
        raw_score=score,
        score_band=ScoreBand.STRONG_SIGNAL if score >= 0.5 else ScoreBand.MODERATE_SIGNAL,
        model_id="test-model",
        model_version="1.0",
        is_test_fixture=fixture,
    )


def test_aggregate_empty():
    assert aggregate_detections([]) == []


def test_aggregate_filters_below_min_score():
    dets = [
        make_det(0.0, 0.975, "Wind", 0.10),   # below 0.15 threshold
        make_det(1.0, 1.975, "Noise", 0.05),
    ]
    assert aggregate_detections(dets, min_score=0.15) == []


def test_aggregate_overlapping_windows_same_label():
    """Overlapping windows of the same class must merge into a single continuous event with peak score."""
    dets = [
        # Window 1: 0.00s - 0.975s, score 0.62
        make_det(0.000, 0.975, "Bird", 0.62),
        # Window 2 (50% overlap): 0.4875s - 1.4625s, score 0.88
        make_det(0.4875, 1.4625, "Bird", 0.88),
        # Window 3 (50% overlap): 0.9750s - 1.9500s, score 0.55
        make_det(0.9750, 1.9500, "Bird", 0.55),
    ]

    merged = aggregate_detections(dets, max_gap_seconds=0.50, min_score=0.15)
    assert len(merged) == 1
    event = merged[0]

    assert event.label == "Bird"
    assert event.start_time == 0.000
    assert event.end_time == 1.9500
    assert event.raw_score == 0.88  # Peak score preserved
    assert event.score_band == ScoreBand.STRONG_SIGNAL
    assert event.is_test_fixture is True


def test_aggregate_disjoint_windows_same_label():
    """Non-overlapping windows with a significant gap must remain distinct events."""
    dets = [
        # Call 1 in first half
        make_det(0.5, 1.475, "Bird", 0.75),
        # Call 2 much later (3 second gap)
        make_det(4.5, 5.475, "Bird", 0.82),
    ]

    merged = aggregate_detections(dets, max_gap_seconds=0.50)
    assert len(merged) == 2
    assert merged[0].start_time == 0.5
    assert merged[0].end_time == 1.475
    assert merged[1].start_time == 4.5
    assert merged[1].end_time == 5.475


def test_aggregate_concurrent_different_classes():
    """Concurrent sounds of different categories must both be preserved without collisions."""
    dets = [
        make_det(0.0, 0.975, "Bird", 0.70),
        make_det(0.0, 0.975, "Wind", 0.55),
        make_det(0.4875, 1.4625, "Bird", 0.85),
    ]

    merged = aggregate_detections(dets, max_gap_seconds=0.50)
    assert len(merged) == 2
    labels = {d.label for d in merged}
    assert labels == {"Bird", "Wind"}

    bird_event = next(d for d in merged if d.label == "Bird")
    assert bird_event.start_time == 0.0
    assert bird_event.end_time == 1.4625
    assert bird_event.raw_score == 0.85
