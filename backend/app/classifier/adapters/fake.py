"""Fake AudioClassifier adapter for deterministic unit tests.

IMPORTANT:
This adapter returns predetermined fixture detections solely to test
downstream contracts, API routes, and data models without requiring
actual AI weights. It explicitly marks all outputs with `is_test_fixture=True`
and prefixes labels with `[TEST FIXTURE]`.
"""
from pathlib import Path
from ..base import AudioClassifier
from ..types import Detection, ScoreBand


class FakeAudioClassifier(AudioClassifier):
    """Deterministic fixture classifier strictly for automated testing."""

    def __init__(
        self,
        canned_detections: list[Detection] | None = None,
        should_fail: bool = False,
    ):
        self._canned = canned_detections
        self._should_fail = should_fail

    @property
    def model_id(self) -> str:
        return "fake-fixture-adapter"

    @property
    def model_version(self) -> str:
        return "0.0.0-test"

    def analyze(self, audio_path: Path | str) -> list[Detection]:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        if self._should_fail:
            raise RuntimeError("Simulated inference failure for error testing.")

        if self._canned is not None:
            return self._canned

        # Default deterministic test detections
        return [
            Detection(
                start_time=0.5,
                end_time=1.475,
                label="[TEST FIXTURE] Bird vocalization",
                raw_score=0.82,
                score_band=ScoreBand.STRONG_SIGNAL,
                model_id=self.model_id,
                model_version=self.model_version,
                is_test_fixture=True,
            ),
            Detection(
                start_time=2.0,
                end_time=2.975,
                label="[TEST FIXTURE] Wind rustle",
                raw_score=0.41,
                score_band=ScoreBand.MODERATE_SIGNAL,
                model_id=self.model_id,
                model_version=self.model_version,
                is_test_fixture=True,
            ),
        ]
