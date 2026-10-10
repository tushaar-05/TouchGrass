"""Deterministic reflection generator for Sit Spot.

Strict policy:
Never hallucinate or invent species, weather, animals, or acoustic events.
Only reflects upon the user's explicit guesses and the model's actual detected sound categories.
"""
import re
from typing import Sequence
from ..classifier.types import Detection, ScoreBand


def generate_reflection(
    user_guesses: Sequence[str],
    detections: Sequence[Detection],
    is_silent: bool = False,
) -> str:
    """Generate a grounded, deterministic field observation reflection.
    
    Args:
        user_guesses: List of acoustic observations entered by the user.
        detections: List of verified model detections.
        is_silent: Flag indicating whether recording was quiet / sub-threshold.
        
    Returns:
        str: Grounded textual summary contrasting guesses with detections.
    """
    cleaned_guesses = [g.strip() for g in user_guesses if g.strip()]
    detected_labels = list({d.label for d in detections})
    
    # 1. Silent or near-silent recording
    if is_silent or (not detections and not cleaned_guesses):
        return (
            "Your listening session was exceptionally still and quiet. "
            "No prominent acoustic signals crossed the activation threshold, "
            "providing a peaceful moment of deep stillness in your spot."
        )

    lines: list[str] = []

    # 2. Compare user guesses with model detections (substring or common word stem matching)
    matched_observations = []
    unmatched_guesses = []

    for guess in cleaned_guesses:
        guess_lower = guess.lower()
        guess_tokens = {w for w in re.findall(r"\b\w+\b", guess_lower) if len(w) >= 3}
        matched = False

        for det_label in detected_labels:
            det_lower = det_label.lower()
            det_tokens = {w for w in re.findall(r"\b\w+\b", det_lower) if len(w) >= 3}

            # Check direct substring or shared word token (e.g. "bird" in "bird chirps" and "bird vocalization")
            if (guess_lower in det_lower or det_lower in guess_lower) or (guess_tokens & det_tokens):
                matched_observations.append((guess, det_label))
                matched = True
                break

        if not matched:
            unmatched_guesses.append(guess)

    unmatched_detections = [
        label for label in detected_labels
        if not any(
            (g.lower() in label.lower() or label.lower() in g.lower())
            or (set(re.findall(r"\b\w+\b", g.lower())) & set(re.findall(r"\b\w+\b", label.lower())))
            for g in cleaned_guesses
        )
    ]

    # Synthesize grounded reflection
    if matched_observations:
        matches_str = ", ".join(f"'{g}' (aligned with {d})" for g, d in matched_observations)
        lines.append(f"Sharp listening: You noticed {matches_str}.")

    if unmatched_detections:
        det_str = ", ".join(unmatched_detections[:4])
        if matched_observations:
            lines.append(f"The model also picked up signals consistent with {det_str}.")
        else:
            lines.append(f"The model detected acoustic patterns characteristic of {det_str}.")

    if unmatched_guesses:
        guess_str = ", ".join(f"'{g}'" for g in unmatched_guesses)
        lines.append(
            f"You noted {guess_str}, which was not flagged by the general acoustic model. "
            "Subtle animal calls, distant wind, or human footsteps may be below model threshold "
            "or outside its primary training representations."
        )

    if not detected_labels and cleaned_guesses:
        guess_str = ", ".join(f"'{g}'" for g in cleaned_guesses)
        lines.append(
            f"You noted {guess_str}. While the model's activation levels remained below threshold for these sounds, "
            "your active attention captured subtleties that general automated classification often misses."
        )

    return " ".join(lines)
