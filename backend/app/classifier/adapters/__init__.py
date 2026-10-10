"""Classifier adapters package."""
from .fake import FakeAudioClassifier
from .yamnet_onnx import YamNetOnnxClassifier

__all__ = ["FakeAudioClassifier", "YamNetOnnxClassifier"]
