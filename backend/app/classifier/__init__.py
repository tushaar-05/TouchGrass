"""Classifier package for audio event detection."""
from .types import Detection, ScoreBand, map_score_to_band
from .base import AudioClassifier
from .aggregator import aggregate_detections
from .adapters.fake import FakeAudioClassifier
from .adapters.yamnet_onnx import YamNetOnnxClassifier

__all__ = [
    "Detection",
    "ScoreBand",
    "map_score_to_band",
    "AudioClassifier",
    "aggregate_detections",
    "FakeAudioClassifier",
    "YamNetOnnxClassifier",
]
