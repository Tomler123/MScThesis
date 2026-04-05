def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    Merge all overlapping intervals and return a sorted list of non-overlapping intervals.
    
    Args:
        intervals: A list of tuples, where each tuple represents (start, end).
        
    Returns:
        A new list of merged and sorted tuples.
    """
    if not intervals:
        return []

    # 1. Sort the intervals based on the start time.
    # This ensures that any potential overlaps are adjacent in the list.
    sorted_intervals = sorted(intervals, key=lambda x: x[0])

    # Initialize the merged list with the first interval.
    merged = [sorted_intervals[0]]

    for current in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        curr_start, curr_end = current

        # 2. Check for overlap:
        # Since they are sorted by start time, we only need to check if 
        # the current start is less than or equal to the previous end.
        if curr_start <= last_end:
            # Overlap found: Update the end of the last interval in 'merged'
            # to be the maximum of the two ends (handles nested intervals).
            merged[-1] = (last_start, max(last_end, curr_end))
        else:
            # No overlap: Add the current interval as a new entry.
            merged.append(current)

    return merged

# --- Test Cases ---
assert merge_intervals([]) == []
assert merge_intervals([(1, 3)]) == [(1, 3)]
assert merge_intervals([(1, 3), (5, 7)]) == [(1, 3), (5, 7)]
assert merge_intervals([(1, 3), (2, 5)]) == [(1, 5)]
assert merge_intervals([(1, 3), (3, 5)]) == [(1, 5)]
assert merge_intervals([(1, 10), (2, 5), (3, 7)]) == [(1, 10)]
assert merge_intervals([(5, 7), (1, 3), (2, 6)]) == [(1, 7)]  # unsorted input
assert merge_intervals([(1, 2), (3, 4), (5, 6)]) == [(1, 2), (3, 4), (5, 6)]
assert merge_intervals([(1, 5), (2, 3)]) == [(1, 5)]  # fully nested
assert merge_intervals([(1, 4), (2, 5), (7, 9), (8, 11), (13, 15)]) == [(1, 5), (7, 11), (13, 15)]
assert merge_intervals([(0, 0), (1, 1)]) == [(0, 0), (1, 1)]  # point intervals
assert merge_intervals([(0, 0), (0, 0)]) == [(0, 0)]

print("All tests passed!")