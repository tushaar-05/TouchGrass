"""API routes for listening session analysis and processing."""
import json
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from ..classifier.base import AudioClassifier
from ..classifier.adapters.yamnet_onnx import YamNetOnnxClassifier
from ..classifier.types import Detection
from ..config import settings
from ..core.audio import decode_and_validate_audio
from ..core.exceptions import SitSpotAudioError
from ..reflection.generator import generate_reflection

router = APIRouter(prefix="/api", tags=["session"])

# Classifier singleton management
_classifier_instance: AudioClassifier | None = None


def get_classifier() -> AudioClassifier:
    """Dependency providing the production YamNetOnnxClassifier."""
    global _classifier_instance
    if _classifier_instance is None:
        if not settings.model_path.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Local AI model weights are not installed. Run 'backend/scripts/download_model.py' to acquire model weights.",
            )
        try:
            _classifier_instance = YamNetOnnxClassifier(
                model_path=settings.model_path,
                class_map_path=settings.class_map_path,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize local AI model: {e}",
            )
    return _classifier_instance


class AnalysisResponse(BaseModel):
    session_id: str = Field(..., description="Unique ID for this listening session")
    duration_seconds: float = Field(..., description="Actual recorded duration in seconds")
    sample_count: int = Field(..., description="Total PCM samples at 16kHz")
    is_silent: bool = Field(..., description="True if recording was quiet or sub-threshold")
    has_clipping_warning: bool = Field(..., description="True if acoustic clipping exceeded warning threshold")
    detections: list[Detection] = Field(default_factory=list, description="Aggregated acoustic event detections")
    user_guesses: list[str] = Field(default_factory=list, description="User entered guesses before reveal")
    reflection: str = Field(..., description="Grounded naturalist reflection")
    scientific_disclaimer: str = Field(
        default="Acoustic detections reflect uncalibrated model activations and may be inaccurate. Biological species are not identified.",
        description="Scientific limitation statement",
    )


def _parse_guesses(raw: str | None) -> list[str]:
    """Parse guesses from JSON string or comma/newline separated text."""
    if not raw or not raw.strip():
        return []
    text = raw.strip()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
    # Fallback to newline / comma splitting
    items = [line.strip() for line in text.replace(",", "\n").splitlines() if line.strip()]
    return items


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_recording(
    file: Annotated[UploadFile, File(description="Recorded audio file (WAV, WebM, MP4)")],
    guesses: Annotated[str | None, Form(description="User sound guesses")] = None,
    classifier: AudioClassifier = Depends(get_classifier),
):
    """Analyze a listening session recording using local AI inference."""
    try:
        audio_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded audio stream: {e}",
        )

    # 1. Validate and decode audio bytes
    try:
        samples, validation_meta = decode_and_validate_audio(
            audio_bytes,
            max_file_size_bytes=settings.max_file_size_bytes,
            min_duration_seconds=settings.min_duration_seconds,
            max_duration_seconds=settings.max_duration_seconds,
        )
    except SitSpotAudioError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio decoding error: {e}",
        )

    # 2. Run local AI inference
    parsed_guesses = _parse_guesses(guesses)

    if validation_meta.is_silent:
        detections = []
    else:
        try:
            detections = classifier.analyze(audio_bytes)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference processing error: {e}",
            )

    # 3. Generate grounded deterministic reflection
    reflection = generate_reflection(
        user_guesses=parsed_guesses,
        detections=detections,
        is_silent=validation_meta.is_silent,
    )

    session_id = str(uuid.uuid4())

    return AnalysisResponse(
        session_id=session_id,
        duration_seconds=validation_meta.duration_seconds,
        sample_count=validation_meta.sample_count,
        is_silent=validation_meta.is_silent,
        has_clipping_warning=validation_meta.has_clipping_warning,
        detections=detections,
        user_guesses=parsed_guesses,
        reflection=reflection,
    )
