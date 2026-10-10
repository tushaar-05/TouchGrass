"""Comprehensive unit tests for Sit Spot audio validation, decoding, and preprocessing.

Tests cover:
- Format / container signature validation (WAV, WebM, MP4, unsupported)
- File size bounds (empty, valid, oversized)
- Duration bounds (too short, valid, too long)
- Sample rate resampling and stereo-to-mono mixdown
- Browser-recorded WebM and MP4 decoding via FFmpeg
- Silence detection and clipping diagnostics
- Severe clipping rejection threshold (30%)
- Corrupt and truncated file handling
- Subprocess timeout and process error handling
- Temporary directory and file cleanup
- YAMNet temporal window bounding (no padded audio presented as observed)
- Zero network socket usage during processing
"""
import io
import socket
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pytest
import soundfile as sf

from app.core.audio import (
    CLIPPING_REJECT_RATIO,
    CLIPPING_WARNING_RATIO,
    TARGET_SAMPLE_RATE,
    AudioValidationResult,
    compute_yamnet_windows,
    decode_and_validate_audio,
    detect_format_from_bytes,
)
from app.core.exceptions import (
    AudioClippingError,
    AudioCorruptError,
    AudioDecoderTimeoutError,
    AudioDurationError,
    AudioFileSizeError,
    UnsupportedAudioFormatError,
)


# Helper functions to construct in-memory test audio bytes
def make_wav_bytes(
    duration_sec: float = 2.0,
    sample_rate: int = 16000,
    channels: int = 1,
    amplitude: float = 0.5,
    frequency: float = 440.0,
) -> bytes:
    """Generate in-memory WAV file bytes."""
    num_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, num_samples, endpoint=False)
    sine = amplitude * np.sin(2 * np.pi * frequency * t)

    if channels == 1:
        data = sine.astype(np.float32)
    elif channels == 2:
        # 2 channels with slightly different phase
        data = np.stack([sine, amplitude * np.cos(2 * np.pi * frequency * t)], axis=1).astype(np.float32)
    else:
        raise ValueError(f"Unsupported channel count: {channels}")

    buf = io.BytesIO()
    sf.write(buf, data, sample_rate, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def make_encoded_bytes(fmt: str, duration_sec: float = 2.0) -> bytes:
    """Use installed FFmpeg to create a genuine WebM/Opus or MP4/AAC byte payload."""
    with tempfile.TemporaryDirectory() as td:
        out_path = Path(td) / f"test.{fmt}"
        codec = "libopus" if fmt == "webm" else "aac"
        cmd = [
            "ffmpeg",
            "-nostdin",
            "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency=800:duration={duration_sec}",
            "-c:a", codec,
            str(out_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return out_path.read_bytes()


# ---------------------------------------------------------------------------
# Format Detection & Magic Bytes
# ---------------------------------------------------------------------------

def test_detect_format_valid():
    wav_bytes = make_wav_bytes(duration_sec=1.0)
    assert detect_format_from_bytes(wav_bytes) == "wav"

    webm_fake = b"\x1a\x45\xdf\xa3" + b"\x00" * 20
    assert detect_format_from_bytes(webm_fake) == "webm"

    mp4_fake = b"\x00\x00\x00\x20ftypisom" + b"\x00" * 16
    assert detect_format_from_bytes(mp4_fake) == "mp4"


def test_detect_format_unsupported():
    with pytest.raises(UnsupportedAudioFormatError, match="Unsupported audio container"):
        detect_format_from_bytes(b"RIFF....AVI \x00\x00\x00\x00")

    with pytest.raises(UnsupportedAudioFormatError, match="too small"):
        detect_format_from_bytes(b"RIFF")


# ---------------------------------------------------------------------------
# File Size Validation
# ---------------------------------------------------------------------------

def test_empty_audio_rejected():
    with pytest.raises(AudioFileSizeError, match="empty"):
        decode_and_validate_audio(b"")


def test_oversized_audio_rejected():
    # Pretend file is 30 MB
    fake_oversized = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * (26 * 1024 * 1024)
    with pytest.raises(AudioFileSizeError, match="exceeds maximum allowed limit"):
        decode_and_validate_audio(fake_oversized, max_file_size_bytes=25 * 1024 * 1024)


# ---------------------------------------------------------------------------
# WAV Decoding, Resampling, and Stereo-to-Mono
# ---------------------------------------------------------------------------

def test_valid_16k_mono_wav():
    wav_bytes = make_wav_bytes(duration_sec=2.5, sample_rate=16000, channels=1, amplitude=0.4)
    samples, meta = decode_and_validate_audio(wav_bytes)

    assert isinstance(samples, np.ndarray)
    assert samples.dtype == np.float32
    assert samples.ndim == 1
    assert len(samples) == int(2.5 * 16000)
    assert meta.sample_rate == 16000
    assert meta.duration_seconds == 2.5
    assert meta.detected_format == "wav"
    assert not meta.is_silent
    assert not meta.has_clipping_warning


def test_stereo_to_mono_mixdown():
    wav_bytes = make_wav_bytes(duration_sec=2.0, sample_rate=16000, channels=2, amplitude=0.3)
    samples, meta = decode_and_validate_audio(wav_bytes)

    assert samples.ndim == 1
    assert len(samples) == int(2.0 * 16000)
    assert meta.sample_rate == 16000
    assert meta.duration_seconds == 2.0


def test_resampling_44k_and_48k_wav():
    for sr in [44100, 48000]:
        wav_bytes = make_wav_bytes(duration_sec=2.0, sample_rate=sr, channels=1, amplitude=0.4)
        samples, meta = decode_and_validate_audio(wav_bytes)

        assert meta.sample_rate == 16000
        # Tolerating 0.05s rounding in ffmpeg resampling
        assert abs(meta.duration_seconds - 2.0) < 0.05
        assert samples.dtype == np.float32
        assert samples.ndim == 1


# ---------------------------------------------------------------------------
# Browser-Recorded WebM and MP4 Decoding
# ---------------------------------------------------------------------------

def test_webm_opus_decoding():
    webm_bytes = make_encoded_bytes("webm", duration_sec=2.0)
    samples, meta = decode_and_validate_audio(webm_bytes)

    assert meta.detected_format == "webm"
    assert meta.sample_rate == 16000
    assert abs(meta.duration_seconds - 2.0) < 0.1
    assert samples.ndim == 1
    assert not meta.is_silent


def test_mp4_aac_decoding():
    mp4_bytes = make_encoded_bytes("mp4", duration_sec=2.0)
    samples, meta = decode_and_validate_audio(mp4_bytes)

    assert meta.detected_format == "mp4"
    assert meta.sample_rate == 16000
    assert abs(meta.duration_seconds - 2.0) < 0.1
    assert samples.ndim == 1
    assert not meta.is_silent


# ---------------------------------------------------------------------------
# Silence and Duration Detection
# ---------------------------------------------------------------------------

def test_silent_audio_detection():
    # Audio with amplitude 0.00001 (below -80 dBFS)
    wav_bytes = make_wav_bytes(duration_sec=2.0, sample_rate=16000, amplitude=0.00001)
    samples, meta = decode_and_validate_audio(wav_bytes)

    assert meta.is_silent is True
    assert meta.rms_energy < 1e-4


def test_duration_too_short():
    # 0.5s is below the 1.0s minimum
    wav_bytes = make_wav_bytes(duration_sec=0.5, sample_rate=16000)
    with pytest.raises(AudioDurationError, match="shorter than the minimum"):
        decode_and_validate_audio(wav_bytes, min_duration_seconds=1.0)


def test_duration_too_long():
    # Duration > max limit
    wav_bytes = make_wav_bytes(duration_sec=3.5, sample_rate=16000)
    with pytest.raises(AudioDurationError, match="exceeds the maximum allowed duration"):
        decode_and_validate_audio(wav_bytes, max_duration_seconds=3.0)


# ---------------------------------------------------------------------------
# Clipping Diagnostics and Rejection Policy
# ---------------------------------------------------------------------------

def test_clipping_warning_diagnostic():
    # Construct audio with 8% clipped samples
    num_samples = 32000
    audio = np.random.uniform(-0.5, 0.5, num_samples).astype(np.float32)
    # Clip 8% of samples to 1.0
    clip_count = int(num_samples * 0.08)
    audio[:clip_count] = 1.0

    buf = io.BytesIO()
    sf.write(buf, audio, 16000, format="WAV", subtype="PCM_16")

    samples, meta = decode_and_validate_audio(buf.getvalue())
    assert meta.has_clipping_warning is True
    assert 0.05 < meta.clipping_ratio < 0.15


def test_clipping_severe_rejection():
    # Construct audio with 35% clipped samples (exceeds 30% rejection threshold)
    num_samples = 32000
    audio = np.random.uniform(-0.5, 0.5, num_samples).astype(np.float32)
    clip_count = int(num_samples * 0.35)
    audio[:clip_count] = 1.0

    buf = io.BytesIO()
    sf.write(buf, audio, 16000, format="WAV", subtype="PCM_16")

    with pytest.raises(AudioClippingError, match="Severe audio clipping detected"):
        decode_and_validate_audio(buf.getvalue())


# ---------------------------------------------------------------------------
# Corrupt Data, Decoder Failure, and Timeout Handling
# ---------------------------------------------------------------------------

def test_corrupt_audio_stream():
    # Starts with WebM magic bytes but body is corrupt gibberish
    corrupt_webm = b"\x1a\x45\xdf\xa3" + b"CORRUPT_PAYLOAD" * 50
    with pytest.raises(AudioCorruptError, match="Audio decoder failed"):
        decode_and_validate_audio(corrupt_webm)


def test_ffmpeg_timeout_handling():
    wav_bytes = make_wav_bytes(duration_sec=2.0)

    # Simulate subprocess timeout
    def mock_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=0.1)

    with patch("subprocess.run", side_effect=mock_run):
        # Trigger FFmpeg path by asking to decode WebM magic bytes
        fake_webm = b"\x1a\x45\xdf\xa3" + wav_bytes[4:]
        with pytest.raises(AudioDecoderTimeoutError, match="exceeded time limit"):
            decode_and_validate_audio(fake_webm)


# ---------------------------------------------------------------------------
# Temporary Directory Cleanup Verification
# ---------------------------------------------------------------------------

def test_temp_directory_cleaned_up_after_processing():
    created_dirs = []
    real_temp_dir = tempfile.TemporaryDirectory

    def track_temp_dir(*args, **kwargs):
        td = real_temp_dir(*args, **kwargs)
        created_dirs.append(Path(td.name))
        return td

    with patch("tempfile.TemporaryDirectory", side_effect=track_temp_dir):
        webm_bytes = make_encoded_bytes("webm", duration_sec=1.5)
        _, _ = decode_and_validate_audio(webm_bytes)

    assert len(created_dirs) > 0
    for path in created_dirs:
        assert not path.exists(), f"Temporary directory {path} leaked on disk!"


def test_temp_directory_cleaned_up_on_error():
    created_dirs = []
    real_temp_dir = tempfile.TemporaryDirectory

    def track_temp_dir(*args, **kwargs):
        td = real_temp_dir(*args, **kwargs)
        created_dirs.append(Path(td.name))
        return td

    with patch("tempfile.TemporaryDirectory", side_effect=track_temp_dir):
        corrupt_webm = b"\x1a\x45\xdf\xa3" + b"GARBAGE_PAYLOAD" * 20
        with pytest.raises(AudioCorruptError):
            decode_and_validate_audio(corrupt_webm)

    assert len(created_dirs) > 0
    for path in created_dirs:
        assert not path.exists(), f"Temporary directory {path} leaked after error!"


# ---------------------------------------------------------------------------
# YAMNet Temporal Window Bounding (No Padded Audio Presented)
# ---------------------------------------------------------------------------

def test_yamnet_windows_temporal_bounds():
    # 2.3 seconds of audio = 36,800 samples at 16kHz
    total_samples = 36800
    sample_rate = 16000
    total_duration = total_samples / sample_rate  # exactly 2.3s

    windows = compute_yamnet_windows(total_samples, sample_rate=sample_rate)

    assert len(windows) > 0

    for start_t, end_t, start_idx, end_idx in windows:
        # Check start before end
        assert start_t < end_t
        # Check start within bounds
        assert 0.0 <= start_t < total_duration
        # STRICT REQUIREMENT: end_t must NEVER exceed actual duration
        assert end_t <= total_duration
        # Sample indices must be valid
        assert 0 <= start_idx < end_idx <= total_samples

    # Final window check: end_t must be exactly total_duration (clamped)
    last_start, last_end, last_s_idx, last_e_idx = windows[-1]
    assert last_end == total_duration
    assert last_e_idx == total_samples


# ---------------------------------------------------------------------------
# Network Isolation Verification
# ---------------------------------------------------------------------------

def test_offline_guarantee_no_sockets_opened():
    real_connect = socket.socket.connect

    def blocked_connect(*args, **kwargs):
        raise RuntimeError("NETWORK ATTEMPT DETECTED: Offline audio processing must never connect.")

    socket.socket.connect = blocked_connect
    try:
        wav_bytes = make_wav_bytes(duration_sec=2.0)
        samples, meta = decode_and_validate_audio(wav_bytes)
        assert len(samples) > 0
        assert meta.sample_rate == 16000
    finally:
        socket.socket.connect = real_connect
