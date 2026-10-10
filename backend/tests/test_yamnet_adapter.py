"""Tests for the YamNetOnnxClassifier adapter.

Includes:
1. Unit tests with mocks / synthetic faults (missing files, invalid tensors, silence, errors, no-fallback policy).
2. Real-model integration test executing the local ONNX weights on Apple Silicon under strict network isolation.
"""
import io
import socket
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
import soundfile as sf

from app.classifier.adapters.yamnet_onnx import YamNetOnnxClassifier
from app.classifier.types import Detection, ScoreBand
from app.config import settings
from app.core.exceptions import AudioDurationError


# Helper to generate in-memory wav bytes
def make_wav_bytes(duration_sec: float = 2.0, sample_rate: int = 16000, amplitude: float = 0.5) -> bytes:
    num_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    data = (amplitude * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, data, sample_rate, format="WAV", subtype="PCM_16")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Unit Tests (Mocks and Synthetic Faults)
# ---------------------------------------------------------------------------

def test_missing_model_file_raises_error(tmp_path: Path):
    non_existent_onnx = tmp_path / "missing.onnx"
    dummy_csv = tmp_path / "classes.csv"
    dummy_csv.write_text("index,mid,display_name\n0,/m/0,Speech\n")

    with pytest.raises(FileNotFoundError, match="model weights not found"):
        YamNetOnnxClassifier(model_path=non_existent_onnx, class_map_path=dummy_csv)


def test_missing_class_map_raises_error(tmp_path: Path):
    dummy_onnx = tmp_path / "model.onnx"
    dummy_onnx.write_bytes(b"dummy onnx header")
    missing_csv = tmp_path / "missing_classes.csv"

    with pytest.raises(FileNotFoundError, match="class map not found"):
        YamNetOnnxClassifier(model_path=dummy_onnx, class_map_path=missing_csv)


def test_invalid_class_map_count_raises_error(tmp_path: Path):
    dummy_onnx = tmp_path / "model.onnx"
    dummy_onnx.write_bytes(b"dummy")
    short_csv = tmp_path / "classes.csv"
    # Only 2 classes instead of required 521
    short_csv.write_text("index,mid,display_name\n0,/m/0,Speech\n1,/m/1,Music\n")

    with pytest.raises(ValueError, match="Expected 521 AudioSet ontology classes"):
        YamNetOnnxClassifier(model_path=dummy_onnx, class_map_path=short_csv)


def test_incompatible_tensor_signatures_rejected(tmp_path: Path):
    dummy_onnx = tmp_path / "model.onnx"
    dummy_onnx.write_bytes(b"dummy")
    valid_csv = tmp_path / "classes.csv"
    lines = ["index,mid,display_name"] + [f"{i},/m/{i},Class_{i}" for i in range(521)]
    valid_csv.write_text("\n".join(lines) + "\n")

    mock_input = MagicMock()
    mock_input.name = "wrong_input_name"
    mock_output = MagicMock()
    mock_output.name = "output_0"

    mock_session = MagicMock()
    mock_session.get_inputs.return_value = [mock_input]
    mock_session.get_outputs.return_value = [mock_output]

    with patch("onnxruntime.InferenceSession", return_value=mock_session):
        with pytest.raises(RuntimeError, match="Incompatible ONNX model: expected input 'waveform'"):
            YamNetOnnxClassifier(model_path=dummy_onnx, class_map_path=valid_csv)


def test_silent_audio_returns_empty_detections(tmp_path: Path):
    """Silent recording must return an empty list without hallucinations."""
    # Create a 2s silent audio file
    silent_wav = tmp_path / "silent.wav"
    silent_data = np.zeros(32000, dtype=np.float32)
    sf.write(str(silent_wav), silent_data, 16000, format="WAV", subtype="PCM_16")

    # Use actual model files
    classifier = YamNetOnnxClassifier(
        model_path=settings.model_path,
        class_map_path=settings.class_map_path,
    )
    detections = classifier.analyze(silent_wav)
    assert detections == []


def test_missing_audio_file_raises_error():
    classifier = YamNetOnnxClassifier(
        model_path=settings.model_path,
        class_map_path=settings.class_map_path,
    )
    with pytest.raises(FileNotFoundError, match="Audio recording not found"):
        classifier.analyze("/path/that/does/not/exist/ambient.wav")


def test_short_audio_rejected_by_duration_boundary(tmp_path: Path):
    """Audio shorter than minimum duration (1.0s) must fail with AudioDurationError."""
    short_wav = tmp_path / "short.wav"
    short_data = np.random.uniform(-0.1, 0.1, 8000).astype(np.float32)  # 0.5s
    sf.write(str(short_wav), short_data, 16000, format="WAV", subtype="PCM_16")

    classifier = YamNetOnnxClassifier(
        model_path=settings.model_path,
        class_map_path=settings.class_map_path,
    )
    with pytest.raises(AudioDurationError):
        classifier.analyze(short_wav)


def test_no_silent_fallback_on_runtime_failure(tmp_path: Path):
    """When inference fails, raise RuntimeError immediately. Never fall back to fake fixture adapter."""
    test_wav = tmp_path / "test.wav"
    test_wav.write_bytes(make_wav_bytes(duration_sec=2.0))

    classifier = YamNetOnnxClassifier(
        model_path=settings.model_path,
        class_map_path=settings.class_map_path,
    )

    with patch.object(classifier._session, "run", side_effect=Exception("ONNX internal fault")):
        with pytest.raises(RuntimeError, match="Local AI audio inference failed"):
            classifier.analyze(test_wav)


# ---------------------------------------------------------------------------
# Real-Model Integration Test (Actual Local Inference on Apple Silicon)
# ---------------------------------------------------------------------------

def test_real_yamnet_inference_offline():
    """Real AI inference test:
    - Loads local yamnet.onnx and yamnet_class_map.csv
    - Evaluates 3.0s synthetic bird chirp fixture
    - Strictly blocks network sockets to verify offline operation
    - Asserts real acoustic detections with honest score bands
    """
    fixture_path = Path(__file__).parent / "fixtures" / "synthetic_bird_chirp_16k.wav"
    assert fixture_path.exists(), f"Fixture missing: {fixture_path}"

    real_connect = socket.socket.connect

    def blocked_connect(*args, **kwargs):
        raise RuntimeError("OFFLINE VIOLATION: Network connection attempted during inference!")

    socket.socket.connect = blocked_connect
    try:
        classifier = YamNetOnnxClassifier(
            model_path=settings.model_path,
            class_map_path=settings.class_map_path,
            min_score_threshold=0.20,
        )

        assert classifier.model_id == "yamnet-onnx"
        assert "Google-AudioSet-v1" in classifier.model_version

        detections = classifier.analyze(fixture_path)
    finally:
        socket.socket.connect = real_connect

    assert len(detections) > 0

    # Verify every detection satisfies honest boundaries
    for det in detections:
        assert isinstance(det, Detection)
        assert det.is_test_fixture is False
        assert det.model_id == "yamnet-onnx"
        assert 0.0 <= det.start_time < det.end_time
        # STRICT REQUIREMENT: timestamps bounded by 3.0s actual duration
        assert det.end_time <= 3.0
        assert 0.0 <= det.raw_score <= 1.0
        assert len(det.scientific_disclaimer) > 0

    # Chirp fixture should detect Bird or Animal signals
    labels = {d.label for d in detections}
    assert any("Bird" in label or "Animal" in label for label in labels), f"Expected Bird/Animal in labels: {labels}"

    # Verify score band
    top_det = max(detections, key=lambda d: d.raw_score)
    assert top_det.score_band == ScoreBand.STRONG_SIGNAL
    assert top_det.raw_score >= 0.50
