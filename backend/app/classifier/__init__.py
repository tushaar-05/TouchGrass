"""Classifier package for audio event detection."""
from .types import Detection, ScoreBand
from .base import AudioClassifier

__all__ = ["Detection", "ScoreBand", "AudioClassifier"]
