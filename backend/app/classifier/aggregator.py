"""Temporal aggregation and score smoothing for overlapping classifier windows.

Rationale:
YAMNet evaluates audio in 0.975s sliding windows with a 0.4875s hop (50% overlap).
An acoustic event (such as a bird calling or wind gust) spanning multiple consecutive
frames will trigger repetitive detections for each individual window.

This module aggregates contiguous or overlapping frame detections for the same acoustic
class into a unified temporal event:
1. Merges overlapping and near-adjacent windows for each class label.
2. Derives the event's raw score from the peak acoustic activation observed during the event.
3. Maps peak score to qualitative score bands without claiming statistical probability.
4. Preserves chronological ordering and exact bounding timestamps.
"""
from collections import defaultdict
from .types import Detection, map_score_to_band


def aggregate_detections(
    detections: list[Detection],
    max_gap_seconds: float = 0.50,
    min_score: float = 0.15,
) -> list[Detection]:
    """Aggregate overlapping or contiguous frame detections by label.
    
    Args:
        detections: List of raw window detections.
        max_gap_seconds: Maximum time gap between detections of the same label
                         to be considered part of the same acoustic event.
                         Default 0.50s (~ one hop interval).
        min_score: Minimum raw score required to enter the aggregation pipeline.
                   Filters out ambient baseline noise floor.
                   
    Returns:
        list[Detection]: Deduplicated, chronologically sorted acoustic events.
    """
    if not detections:
        return []

    # 1. Filter out sub-threshold noise
    filtered = [d for d in detections if d.raw_score >= min_score]
    if not filtered:
        return []

    # 2. Group detections by label
    by_label: dict[str, list[Detection]] = defaultdict(list)
    for d in filtered:
        by_label[d.label].append(d)

    aggregated: list[Detection] = []

    # 3. Merge overlapping intervals for each label
    for label, group in by_label.items():
        # Sort by start_time
        group.sort(key=lambda x: (x.start_time, x.end_time))

        current_start = group[0].start_time
        current_end = group[0].end_time
        peak_score = group[0].raw_score
        model_id = group[0].model_id
        model_version = group[0].model_version
        is_fixture = group[0].is_test_fixture
        disclaimer = group[0].scientific_disclaimer

        for next_det in group[1:]:
            if next_det.start_time <= current_end + max_gap_seconds:
                # Overlapping or contiguous: extend the event boundary
                current_end = max(current_end, next_det.end_time)
                peak_score = max(peak_score, next_det.raw_score)
            else:
                # Gap detected: commit the current event and begin new one
                aggregated.append(
                    Detection(
                        start_time=round(current_start, 4),
                        end_time=round(current_end, 4),
                        label=label,
                        raw_score=round(peak_score, 4),
                        score_band=map_score_to_band(peak_score),
                        model_id=model_id,
                        model_version=model_version,
                        is_test_fixture=is_fixture,
                        scientific_disclaimer=disclaimer,
                    )
                )
                current_start = next_det.start_time
                current_end = next_det.end_time
                peak_score = next_det.raw_score

        # Commit final event for this label
        aggregated.append(
            Detection(
                start_time=round(current_start, 4),
                end_time=round(current_end, 4),
                label=label,
                raw_score=round(peak_score, 4),
                score_band=map_score_to_band(peak_score),
                model_id=model_id,
                model_version=model_version,
                is_test_fixture=is_fixture,
                scientific_disclaimer=disclaimer,
            )
        )

    # 4. Sort aggregated results chronologically, tie-broken by peak score descending
    aggregated.sort(key=lambda x: (x.start_time, -x.raw_score, x.end_time))
    return aggregated
