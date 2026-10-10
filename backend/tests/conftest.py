"""Pytest configuration and shared fixtures."""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def tmp_audio_file(tmp_path: Path) -> Path:
    """Create a temporary dummy audio file to test path validation."""
    dummy_wav = tmp_path / "test_ambient.wav"
    dummy_wav.write_bytes(b"RIFF....WAVEfmt ....data....")
    return dummy_wav
