from typing import List, Tuple

def merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Merge all overlapping intervals and return sorted non-overlapping intervals.

    Two intervals overlap if one starts before or at the point the other ends.
    Intervals are considered closed intervals: [start, end].

    Args:
        intervals: List of tuples (start, end) with start <= end.

    Returns:
        List of merged, non-overlapping intervals sorted by start.
    """
    if not intervals:
        return []

    # Sort intervals by start coordinate
    sorted_intervals = sorted(intervals, key=lambda x: x[0])

    merged: List[Tuple[int, int]] = [sorted_intervals[0]]

    for start, end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]

        # Overlap if current start <= last end (including touching)
        if start <= last_end:
            # Merge: extend the end if necessary
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged