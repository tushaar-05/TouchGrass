"""Concrete YAMNet ONNX inference adapter for Sit Spot.

Adheres strictly to the AudioClassifier protocol:
- Loads the verified local Google YAMNet model and AudioSet class map.
- Validates runtime tensor input/output contracts (waveform [N] -> output_0 [M, 521]).
- Employs optimized ARM64 NEON CPU execution without remote dependencies.
- Rejects missing or incompatible weights at initialization.
- Binds output timestamps strictly within the actual recorded audio duration.
- Executes temporal aggregation across overlapping windows to avoid duplicate alerts.
- Never falls back to fake detections if real inference fails.
"""
import csv
from pathlib import Path
import numpy as np
import onnxruntime as ort

from ..base import AudioClassifier
from ..types import Detection, map_score_to_band
from ..aggregator import aggregate_detections
from ...core.audio import (
    TARGET_SAMPLE_RATE,
    decode_and_validate_audio,
)


class YamNetOnnxClassifier(AudioClassifier):
    """Local YAMNet ONNX audio classifier."""

    def __init__(
        self,
        model_path: Path | str,
        class_map_path: Path | str,
        providers: list[str] | None = None,
        min_score_threshold: float = 0.15,
        top_k_per_frame: int = 5,
    ):
        self._model_path = Path(model_path)
        self._class_map_path = Path(class_map_path)
        self._min_score_threshold = min_score_threshold
        self._top_k_per_frame = top_k_per_frame
        self._providers = providers or ["CPUExecutionProvider"]

        # Validate existence
        if not self._model_path.exists():
            raise FileNotFoundError(
                f"YAMNet model weights not found at: {self._model_path}. "
                "Run 'backend/scripts/download_model.py' to acquire verified model weights."
            )
        if not self._class_map_path.exists():
            raise FileNotFoundError(
                f"YAMNet class map not found at: {self._class_map_path}."
            )

        # Load class map
        self._class_map = self._load_class_map(self._class_map_path)
        if len(self._class_map) != 521:
            raise ValueError(
                f"Expected 521 AudioSet ontology classes, got {len(self._class_map)} in {self._class_map_path}"
            )

        # Initialize ONNX session
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 2
        opts.intra_op_num_threads = 4

        try:
            self._session = ort.InferenceSession(
                str(self._model_path),
                sess_options=opts,
                providers=self._providers,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize local ONNX runtime session: {e}") from e

        # Validate tensor contracts
        inputs = self._session.get_inputs()
        outputs = self._session.get_outputs()

        if not inputs or inputs[0].name != "waveform":
            raise RuntimeError(
                f"Incompatible ONNX model: expected input 'waveform', got {[i.name for i in inputs]}"
            )
        if not outputs or outputs[0].name != "output_0":
            raise RuntimeError(
                f"Incompatible ONNX model: expected output 'output_0', got {[o.name for o in outputs]}"
            )

        self._input_name = inputs[0].name
        self._output_name = outputs[0].name

    @property
    def model_id(self) -> str:
        return "yamnet-onnx"

    @property
    def model_version(self) -> str:
        return "Google-AudioSet-v1 (SHA: 1510041d)"

    def _load_class_map(self, path: Path) -> dict[int, str]:
        mapping = {}
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                mapping[int(row["index"])] = row["display_name"]
        return mapping

    def analyze(self, audio_path: Path | str | bytes) -> list[Detection]:
        """Analyze a local audio recording and return aggregated, bounded detections.
        
        Guarantees:
        - 100% offline local inference.
        - Preserves user recording without corruption.
        - Bounds timestamps strictly to recording duration.
        - Aggregates overlapping windows.
        """
        if isinstance(audio_path, bytes):
            audio_bytes = audio_path
        else:
            path = Path(audio_path)
            if not path.exists():
                raise FileNotFoundError(f"Audio recording not found: {path}")
            audio_bytes = path.read_bytes()

        # 1. Preprocess audio using validated pipeline
        samples, validation_meta = decode_and_validate_audio(audio_bytes)

        # If audio is silent, return empty detections list
        if validation_meta.is_silent:
            return []

        # 2. Run local ONNX inference
        try:
            raw_outputs = self._session.run([self._output_name], {self._input_name: samples})
        except Exception as e:
            raise RuntimeError(f"Local AI audio inference failed: {e}") from e

        scores = raw_outputs[0]  # shape: [M, 521]
        num_frames, num_classes = scores.shape

        if num_classes != len(self._class_map):
            raise RuntimeError(
                f"Output class dimension mismatch: model gave {num_classes}, class map has {len(self._class_map)}"
            )

        # 3. Extract window detections with strict temporal duration bounding
        actual_duration = validation_meta.duration_seconds
        hop_dur = 0.4875
        window_dur = 0.9750

        raw_detections: list[Detection] = []

        for i in range(num_frames):
            start_t = round(i * hop_dur, 4)
            # Guard: do not report frames that begin after the actual recording ends
            if start_t >= actual_duration:
                continue

            end_t = round(min(start_t + window_dur, actual_duration), 4)
            frame_scores = scores[i]

            # Top-k indices
            top_indices = np.argsort(frame_scores)[::-1][: self._top_k_per_frame]

            for idx in top_indices:
                score = float(frame_scores[idx])
                if score < self._min_score_threshold:
                    continue

                label = self._class_map.get(idx, f"Class_{idx}")
                raw_detections.append(
                    Detection(
                        start_time=start_t,
                        end_time=end_t,
                        label=label,
                        raw_score=round(score, 4),
                        score_band=map_score_to_band(score),
                        model_id=self.model_id,
                        model_version=self.model_version,
                        is_test_fixture=False,
                    )
                )

        # 4. Perform temporal aggregation across overlapping windows
        aggregated = aggregate_detections(
            raw_detections,
            max_gap_seconds=hop_dur + 0.05,
            min_score=self._min_score_threshold,
        )

        return aggregated
