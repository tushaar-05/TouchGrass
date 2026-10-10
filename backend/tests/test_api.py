"""Unit and integration tests for FastAPI session analysis endpoints."""
import io
import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes_session import get_classifier
from app.classifier.adapters.fake import FakeAudioClassifier
from app.classifier.types import Detection, ScoreBand


def make_wav_bytes(duration_sec: float = 2.0, sample_rate: int = 16000, amplitude: float = 0.5) -> bytes:
    num_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    data = (amplitude * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, data, sample_rate, format="WAV", subtype="PCM_16")
    return buf.getvalue()


@pytest.fixture
def client_with_fake_classifier():
    """Client fixture overriding get_classifier with a predictable FakeAudioClassifier."""
    fake_dets = [
        Detection(
            start_time=0.5,
            end_time=1.475,
            label="Bird vocalization",
            raw_score=0.88,
            score_band=ScoreBand.STRONG_SIGNAL,
            model_id="fake-adapter",
            model_version="1.0",
            is_test_fixture=True,
        ),
        Detection(
            start_time=1.5,
            end_time=2.475,
            label="Wind",
            raw_score=0.45,
            score_band=ScoreBand.MODERATE_SIGNAL,
            model_id="fake-adapter",
            model_version="1.0",
            is_test_fixture=True,
        ),
    ]
    fake_classifier = FakeAudioClassifier(canned_detections=fake_dets)
    app.dependency_overrides[get_classifier] = lambda: fake_classifier
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_analyze_valid_audio_with_guesses(client_with_fake_classifier: TestClient):
    wav_bytes = make_wav_bytes(duration_sec=3.0)
    files = {"file": ("recording.wav", wav_bytes, "audio/wav")}
    data = {"guesses": "birds, footsteps"}

    response = client_with_fake_classifier.post("/api/analyze", files=files, data=data)
    assert response.status_code == 200

    payload = response.json()
    assert "session_id" in payload
    assert payload["duration_seconds"] == 3.0
    assert payload["is_silent"] is False
    assert len(payload["detections"]) == 2
    assert payload["user_guesses"] == ["birds", "footsteps"]
    assert "Bird vocalization" in payload["reflection"]
    assert len(payload["scientific_disclaimer"]) > 0


def test_analyze_silent_audio(client_with_fake_classifier: TestClient):
    silent_data = np.zeros(32000, dtype=np.float32)
    buf = io.BytesIO()
    sf.write(buf, silent_data, 16000, format="WAV", subtype="PCM_16")
    silent_bytes = buf.getvalue()

    files = {"file": ("silent.wav", silent_bytes, "audio/wav")}
    response = client_with_fake_classifier.post("/api/analyze", files=files)
    assert response.status_code == 200

    payload = response.json()
    assert payload["is_silent"] is True
    assert payload["detections"] == []
    assert "stillness" in payload["reflection"].lower()


def test_analyze_too_short_rejected(client_with_fake_classifier: TestClient):
    short_bytes = make_wav_bytes(duration_sec=0.5)
    files = {"file": ("short.wav", short_bytes, "audio/wav")}

    response = client_with_fake_classifier.post("/api/analyze", files=files)
    assert response.status_code == 400
    assert "shorter than the minimum" in response.json()["detail"]


def test_analyze_empty_file_rejected(client_with_fake_classifier: TestClient):
    files = {"file": ("empty.wav", b"", "audio/wav")}

    response = client_with_fake_classifier.post("/api/analyze", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


def test_analyze_unsupported_format_rejected(client_with_fake_classifier: TestClient):
    files = {"file": ("bad.txt", b"plain text payload not audio", "audio/wav")}

    response = client_with_fake_classifier.post("/api/analyze", files=files)
    assert response.status_code == 400
    assert "Unsupported audio container" in response.json()["detail"]
