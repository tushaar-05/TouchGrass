"""AudioClassifier interface protocol.

All concrete inference adapters (real local ONNX models, bioacoustic plugins,
or deterministic test fixtures) must conform to this interface.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from .types import Detection


class AudioClassifier(ABC):
    """Abstract audio classification interface."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Unique model identifier (e.g. 'yamnet-onnx', 'fake-fixture-classifier')."""
        ...

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Model version or checkpoint hash."""
        ...

    @abstractmethod
    def analyze(self, audio_path: Path | str) -> list[Detection]:
        """Analyze a local audio recording and return timestamped acoustic detections.
        
        Args:
            audio_path: Path to the local audio file to analyze.
            
        Returns:
            list[Detection]: Ordered list of temporal detections.
            
        Raises:
            FileNotFoundError: If the audio file does not exist.
            ValueError: If the audio file format or content is invalid.
            RuntimeError: If model inference fails.
        """
        ...
