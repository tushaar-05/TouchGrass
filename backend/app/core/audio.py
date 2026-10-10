"""Audio validation, decoding, normalization, and window preprocessing.

Strict privacy, security, and quality guarantees:
1. Validates magic bytes / signatures before passing to decoders.
2. Enforces maximum file size (25 MB) and duration bounds (1.0s - 300.0s).
3. Executes FFmpeg fallback without a shell, using strict timeouts and sandboxed temporary directories.
4. Normalizes valid audio to 16 kHz mono float32 [-1.0, 1.0] without synthetic amplification.
5. Performs silence detection and documented clipping diagnostics.
6. Bounds temporal window boundaries strictly to actual recording duration.
"""
import io
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import soundfile as sf

from .exceptions import (
    AudioClippingError,
    AudioCorruptError,
    AudioDecoderTimeoutError,
    AudioDurationError,
    AudioFileSizeError,
    UnsupportedAudioFormatError,
)

# Constants
TARGET_SAMPLE_RATE = 16000
YAMNET_WINDOW_SAMPLES = 15600     # 0.975s at 16kHz
YAMNET_HOP_SAMPLES = 7800         # 0.4875s at 16kHz
SILENCE_RMS_THRESHOLD = 1e-4      # ~ -80 dBFS
SILENCE_PEAK_THRESHOLD = 1e-3     # ~ -60 dBFS
CLIPPING_SAMPLE_THRESHOLD = 0.999
CLIPPING_WARNING_RATIO = 0.05     # 5% of samples clipped -> warning
CLIPPING_REJECT_RATIO = 0.30      # 30% of samples clipped -> reject
DEFAULT_FFMPEG_TIMEOUT_SEC = 15.0


@dataclass(frozen=True)
class AudioValidationResult:
    """Metrics and diagnostic findings from audio validation and decoding."""
    duration_seconds: float
    sample_count: int
    sample_rate: int
    rms_energy: float
    peak_amplitude: float
    clipping_ratio: float
    is_silent: bool
    has_clipping_warning: bool
    detected_format: str


def detect_format_from_bytes(data: bytes) -> str:
    """Sniff container format from header magic bytes.
    
    Returns:
        One of 'wav', 'webm', 'mp4'.
        
    Raises:
        UnsupportedAudioFormatError: If magic bytes do not match supported containers.
    """
    if len(data) < 12:
        raise UnsupportedAudioFormatError("Audio data is too small to contain valid container headers.")

    # WAV container: 'RIFF....WAVE'
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"

    # WebM / Matroska container: starts with EBML ID 0x1A45DFA3
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return "webm"

    # MP4 / M4A container: ftyp box at offset 4
    if data[4:8] == b"ftyp":
        return "mp4"

    raise UnsupportedAudioFormatError(
        "Unsupported audio container. Only WAV, browser-recorded WebM, and MP4/M4A are supported."
    )


def resolve_ffmpeg_path() -> str | None:
    """Find installed FFmpeg binary on host system."""
    return shutil.which("ffmpeg") or ("/opt/homebrew/bin/ffmpeg" if Path("/opt/homebrew/bin/ffmpeg").exists() else None)


def _decode_with_ffmpeg(
    data: bytes,
    fmt: str,
    ffmpeg_path: str,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
) -> np.ndarray:
    """Decode audio bytes to 16 kHz mono float32 using sandboxed FFmpeg invocation.
    
    Guarantees:
    - No shell interpolation (shell=False).
    - Enforced process timeout.
    - All temp files quarantined in a temporary directory and wiped in finally block.
    """
    with tempfile.TemporaryDirectory(prefix="sitspot_audio_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        in_file = tmp_path / f"input.{fmt}"
        out_file = tmp_path / "output.wav"

        in_file.write_bytes(data)

        cmd = [
            ffmpeg_path,
            "-nostdin",
            "-v", "error",
            "-y",
            "-i", str(in_file),
            "-vn",
            "-ac", "1",
            "-ar", str(TARGET_SAMPLE_RATE),
            "-f", "wav",
            str(out_file),
        ]

        try:
            res = subprocess.run(
                cmd,
                shell=False,
                capture_output=True,
                timeout=timeout_sec,
                check=False,
            )
            if res.returncode != 0:
                err_msg = res.stderr.decode("utf-8", errors="replace").strip()
                raise AudioCorruptError(
                    f"Audio decoder failed (code {res.returncode}): {err_msg or 'Invalid audio stream.'}"
                )
        except subprocess.TimeoutExpired:
            raise AudioDecoderTimeoutError(f"Audio decoding exceeded time limit of {timeout_sec:.1f}s.")

        if not out_file.exists() or out_file.stat().st_size == 0:
            raise AudioCorruptError("Decoder produced empty or missing audio stream.")

        try:
            samples, sr = sf.read(str(out_file), dtype="float32")
        except Exception as e:
            raise AudioCorruptError(f"Failed to read decoded audio stream: {e}")

        if sr != TARGET_SAMPLE_RATE:
            raise AudioCorruptError(f"Decoded sample rate mismatch: expected {TARGET_SAMPLE_RATE}, got {sr}")

        if samples.ndim > 1:
            samples = samples.mean(axis=1)

        return samples.astype(np.float32)


def decode_and_validate_audio(
    data: bytes,
    max_file_size_bytes: int = 25 * 1024 * 1024,
    min_duration_seconds: float = 1.0,
    max_duration_seconds: float = 300.0,
    ffmpeg_path: str | None = None,
    timeout_sec: float = DEFAULT_FFMPEG_TIMEOUT_SEC,
) -> tuple[np.ndarray, AudioValidationResult]:
    """Validate, decode, and preprocess audio recording.
    
    Args:
        data: Raw audio file bytes.
        max_file_size_bytes: Upload size cap (default 25 MB).
        min_duration_seconds: Lower duration boundary (default 1.0s).
        max_duration_seconds: Upper duration boundary (default 300.0s).
        ffmpeg_path: Optional explicit path to ffmpeg binary.
        timeout_sec: Subprocess decoding timeout in seconds.
        
    Returns:
        tuple[np.ndarray, AudioValidationResult]:
            - Preprocessed 16 kHz mono float32 waveform in [-1.0, 1.0].
            - Structured validation metrics and quality flags.
            
    Raises:
        AudioFileSizeError
        UnsupportedAudioFormatError
        AudioDurationError
        AudioCorruptError
        AudioClippingError
        AudioDecoderTimeoutError
    """
    # 1. Size Validation
    if len(data) == 0:
        raise AudioFileSizeError("Audio file is empty (0 bytes).")

    if len(data) > max_file_size_bytes:
        size_mb = len(data) / (1024 * 1024)
        max_mb = max_file_size_bytes / (1024 * 1024)
        raise AudioFileSizeError(
            f"Uploaded audio size ({size_mb:.1f} MB) exceeds maximum allowed limit of {max_mb:.0f} MB."
        )

    # 2. Format / Magic Byte Sniffing
    fmt = detect_format_from_bytes(data)

    # 3. Decoding
    samples: np.ndarray | None = None

    if fmt == "wav":
        # Fast in-memory path for standard WAV files
        try:
            wav_data, sr = sf.read(io.BytesIO(data), dtype="float32")
            if sr == TARGET_SAMPLE_RATE:
                if wav_data.ndim > 1:
                    samples = wav_data.mean(axis=1).astype(np.float32)
                else:
                    samples = wav_data.astype(np.float32)
        except Exception:
            # If soundfile fails on non-standard WAV headers, fall back to FFmpeg
            samples = None

    if samples is None:
        # Fallback / WebM / MP4 / Resampling path via FFmpeg
        resolved_ffmpeg = ffmpeg_path or resolve_ffmpeg_path()
        if not resolved_ffmpeg:
            raise AudioCorruptError(
                f"Decoding {fmt.upper()} requires FFmpeg, but no compatible decoder binary was found."
            )
        samples = _decode_with_ffmpeg(data, fmt, resolved_ffmpeg, timeout_sec=timeout_sec)

    # Ensure 1D float32
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    samples = samples.astype(np.float32)

    total_samples = len(samples)
    duration_sec = total_samples / float(TARGET_SAMPLE_RATE)

    # 4. Duration Bounds
    if duration_sec < min_duration_seconds:
        raise AudioDurationError(
            f"Recording duration ({duration_sec:.2f}s) is shorter than the minimum required duration of {min_duration_seconds:.1f}s."
        )

    if duration_sec > max_duration_seconds:
        raise AudioDurationError(
            f"Recording duration ({duration_sec:.1f}s) exceeds the maximum allowed duration of {max_duration_seconds:.1f}s."
        )

    # 5. Energy and Silence Detection
    rms_energy = float(np.sqrt(np.mean(samples ** 2))) if total_samples > 0 else 0.0
    peak_amp = float(np.max(np.abs(samples))) if total_samples > 0 else 0.0
    is_silent = bool(rms_energy < SILENCE_RMS_THRESHOLD or peak_amp < SILENCE_PEAK_THRESHOLD)

    # 6. Clipping Diagnostics & Policy
    clipped_count = int(np.sum(np.abs(samples) >= CLIPPING_SAMPLE_THRESHOLD))
    clipping_ratio = float(clipped_count / total_samples) if total_samples > 0 else 0.0

    if clipping_ratio > CLIPPING_REJECT_RATIO:
        raise AudioClippingError(
            f"Severe audio clipping detected ({clipping_ratio * 100:.1f}% of samples exceed threshold). "
            "The recording is too distorted for reliable acoustic analysis."
        )

    has_clipping_warning = bool(clipping_ratio > CLIPPING_WARNING_RATIO)

    # Enforce safe bounds [-1.0, 1.0] without synthetic amplification
    samples = np.clip(samples, -1.0, 1.0).astype(np.float32)

    result = AudioValidationResult(
        duration_seconds=round(duration_sec, 4),
        sample_count=total_samples,
        sample_rate=TARGET_SAMPLE_RATE,
        rms_energy=round(rms_energy, 6),
        peak_amplitude=round(peak_amp, 6),
        clipping_ratio=round(clipping_ratio, 6),
        is_silent=is_silent,
        has_clipping_warning=has_clipping_warning,
        detected_format=fmt,
    )

    return samples, result


def compute_yamnet_windows(
    total_samples: int,
    sample_rate: int = TARGET_SAMPLE_RATE,
    window_samples: int = YAMNET_WINDOW_SAMPLES,
    hop_samples: int = YAMNET_HOP_SAMPLES,
) -> list[tuple[float, float, int, int]]:
    """Compute temporal window slices for YAMNet, strictly bounding the final partial window.
    
    YAMNet uses 0.975s windows (15,600 samples) with 50% hop (0.4875s / 7,800 samples).
    
    Requirement:
    Detection timestamps must be strictly bounded by the actual recording duration,
    and no padded audio may be presented as observed sound.
    
    Returns:
        list of tuples: (start_time_sec, end_time_sec, start_idx, end_idx)
    """
    if total_samples <= 0:
        return []

    total_duration_sec = total_samples / float(sample_rate)
    windows = []
    start_idx = 0

    while start_idx < total_samples:
        end_idx = min(start_idx + window_samples, total_samples)
        start_sec = start_idx / float(sample_rate)
        # End timestamp is clamped to total duration
        end_sec = min(start_sec + (window_samples / float(sample_rate)), total_duration_sec)

        windows.append((round(start_sec, 4), round(end_sec, 4), start_idx, end_idx))

        # Advance by hop
        start_idx += hop_samples

        # If the remaining unobserved slice is tiny (< 0.1s) and start_idx >= total_samples, finish
        if start_idx >= total_samples:
            break

    return windows
