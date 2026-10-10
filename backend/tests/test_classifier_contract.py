"""Tests verifying the AudioClassifier interface and Detection contracts."""
import pytest
from pathlib import Path
from app.classifier.base import AudioClassifier
from app.classifier.adapters.fake import FakeAudioClassifier
from app.classifier.types import (
    Detection,
    ScoreBand,
    map_score_to_band,
)


def test_score_band_mapping():
    """Verify raw scores map to documented qualitative bands without claiming certainty."""
    assert map_score_to_band(0.95) == ScoreBand.STRONG_SIGNAL
    assert map_score_to_band(0.50) == ScoreBand.STRONG_SIGNAL
    assert map_score_to_band(0.49) == ScoreBand.MODERATE_SIGNAL
    assert map_score_to_band(0.25) == ScoreBand.MODERATE_SIGNAL
    assert map_score_to_band(0.24) == ScoreBand.SUGGESTIVE_TRACE
    assert map_score_to_band(0.10) == ScoreBand.SUGGESTIVE_TRACE


def test_fake_classifier_contract(tmp_audio_file: Path):
    """Verify FakeAudioClassifier complies with AudioClassifier contract."""
    classifier: AudioClassifier = FakeAudioClassifier()

    assert classifier.model_id == "fake-fixture-adapter"
    assert classifier.model_version == "0.0.0-test"

    detections = classifier.analyze(tmp_audio_file)
    assert len(detections) > 0

    for det in detections:
        assert isinstance(det, Detection)
        assert det.end_time > det.start_time
        assert 0.0 <= det.raw_score <= 1.0
        assert det.is_test_fixture is True
        assert "[TEST FIXTURE]" in det.label
        assert det.model_id == "fake-fixture-adapter"
        assert len(det.scientific_disclaimer) > 0


def test_fake_classifier_file_not_found():
    """Verify analyzer raises FileNotFoundError for missing audio path."""
    classifier = FakeAudioClassifier()
    with pytest.raises(FileNotFoundError):
        classifier.analyze("/non/existent/path/nature.wav")


def test_fake_classifier_error_propagation(tmp_audio_file: Path):
    """Verify runtime inference failures are propagated as RuntimeError."""
    classifier = FakeAudioClassifier(should_fail=True)
    with pytest.raises(RuntimeError, match="Simulated inference failure"):
        classifier.analyze(tmp_audio_file)
