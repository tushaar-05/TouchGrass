"""Core utilities for Sit Spot backend."""
from .audio import (
    AudioValidationResult,
    compute_yamnet_windows,
    decode_and_validate_audio,
    detect_format_from_bytes,
)
from .exceptions import (
    AudioClippingError,
    AudioCorruptError,
    AudioDecoderTimeoutError,
    AudioDurationError,
    AudioFileSizeError,
    SitSpotAudioError,
    UnsupportedAudioFormatError,
)

__all__ = [
    "AudioValidationResult",
    "compute_yamnet_windows",
    "decode_and_validate_audio",
    "detect_format_from_bytes",
    "SitSpotAudioError",
    "AudioFileSizeError",
    "UnsupportedAudioFormatError",
    "AudioDurationError",
    "AudioCorruptError",
    "AudioClippingError",
    "AudioDecoderTimeoutError",
]
