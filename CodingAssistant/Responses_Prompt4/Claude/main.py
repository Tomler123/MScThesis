def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    Merge all overlapping intervals and return sorted non-overlapping intervals.

    Two intervals overlap if one starts before or at the point the other ends,
    e.g. [1, 3] and [3, 5] merge into [1, 5].

    Args:
        intervals: A list of (start, end) tuples where start <= end.

    Returns:
        A new sorted list of non-overlapping (start, end) tuples covering the
        same ranges as the input.
    """
    if not intervals:
        return []

    sorted_intervals = sorted(intervals, key=lambda iv: (iv[0], iv[1]))

    merged: list[tuple[int, int]] = [sorted_intervals[0]]

    for start, end in sorted_intervals[1:]:
        current_start, current_end = merged[-1]
        if start <= current_end:          # overlap or touching
            merged[-1] = (current_start, max(current_end, end))
        else:
            merged.append((start, end))

    return merged