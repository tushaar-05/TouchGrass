"""Unit tests for the grounded deterministic reflection engine."""
import pytest
from app.classifier.types import Detection, ScoreBand
from app.reflection.generator import generate_reflection


def make_det(label: str, score: float = 0.8) -> Detection:
    return Detection(
        start_time=0.0,
        end_time=1.0,
        label=label,
        raw_score=score,
        score_band=ScoreBand.STRONG_SIGNAL,
        model_id="test",
        model_version="1.0",
    )


def test_reflection_silent_audio():
    reflection = generate_reflection(user_guesses=[], detections=[], is_silent=True)
    assert "stillness" in reflection.lower()


def test_reflection_aligned_observation():
    reflection = generate_reflection(
        user_guesses=["bird chirps"],
        detections=[make_det("Bird vocalization, bird call")],
        is_silent=False,
    )
    assert "Sharp listening" in reflection
    assert "bird chirps" in reflection


def test_reflection_unmatched_guess():
    reflection = generate_reflection(
        user_guesses=["running deer"],
        detections=[make_det("Wind")],
        is_silent=False,
    )
    assert "running deer" in reflection
    assert "Wind" in reflection
    assert "not flagged" in reflection


def test_reflection_only_detections_no_guesses():
    reflection = generate_reflection(
        user_guesses=[],
        detections=[make_det("Rain")],
        is_silent=False,
    )
    assert "Rain" in reflection
    assert "acoustic patterns" in reflection
