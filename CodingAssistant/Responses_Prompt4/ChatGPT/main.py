def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping intervals into a sorted list of non-overlapping intervals.

    Each interval is a tuple of (start, end) with start <= end. Intervals that
    touch at an endpoint are considered overlapping, so (1, 3) and (3, 5)
    merge into (1, 5).

    Args:
        intervals: A list of integer intervals.

    Returns:
        A new list of sorted, non-overlapping intervals covering the same ranges.
    """
    if not intervals:
        return []

    sorted_intervals = sorted(intervals, key=lambda interval: interval[0])
    merged: list[tuple[int, int]] = []

    current_start, current_end = sorted_intervals[0]

    for start, end in sorted_intervals[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end

    merged.append((current_start, current_end))
    return merged