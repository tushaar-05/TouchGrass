"""Domain exceptions for Sit Spot audio processing and validation.

All exceptions are designed to provide safe, actionable error messages
without leaking internal filesystem paths or system implementation details.
"""


class SitSpotAudioError(Exception):
    """Base exception for all Sit Spot audio errors."""
    def __init__(self, message: str, code: str = "AUDIO_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class AudioFileSizeError(SitSpotAudioError):
    """Raised when an audio upload is empty or exceeds the configured size cap."""
    def __init__(self, message: str):
        super().__init__(message, code="FILE_SIZE_ERROR")


class UnsupportedAudioFormatError(SitSpotAudioError):
    """Raised when an uploaded file is not an allowed audio container/codec."""
    def __init__(self, message: str):
        super().__init__(message, code="UNSUPPORTED_FORMAT")


class AudioDurationError(SitSpotAudioError):
    """Raised when audio duration is outside the allowed range (1s - 300s)."""
    def __init__(self, message: str):
        super().__init__(message, code="DURATION_OUT_OF_BOUNDS")


class AudioCorruptError(SitSpotAudioError):
    """Raised when audio data is malformed, truncated, or unreadable."""
    def __init__(self, message: str):
        super().__init__(message, code="MALFORMED_AUDIO")


class AudioClippingError(SitSpotAudioError):
    """Raised when severe acoustic clipping renders the recording unusable."""
    def __init__(self, message: str):
        super().__init__(message, code="SEVERE_CLIPPING")


class AudioDecoderTimeoutError(SitSpotAudioError):
    """Raised when the background decoder times out while processing audio."""
    def __init__(self, message: str = "Audio processing timed out."):
        super().__init__(message, code="DECODER_TIMEOUT")
