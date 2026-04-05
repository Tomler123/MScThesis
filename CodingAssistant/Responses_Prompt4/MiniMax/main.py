def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    Merge all overlapping intervals and return sorted non-overlapping intervals.
    
    Args:
        intervals: A list of tuples where each tuple (start, end) represents an interval.
    
    Returns:
        A new sorted list of non-overlapping intervals covering the same ranges.
    
    Note:
        Two intervals [a, b] and [c, d] overlap if c <= b (one starts before/at the other ends).
    """
    # Handle empty input
    if not intervals:
        return []
    
    # Sort intervals by start time
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    
    # Initialize result with the first interval
    merged = [sorted_intervals[0]]
    
    for current_start, current_end in sorted_intervals[1:]:
        # Get the last interval in merged list
        last_start, last_end = merged[-1]
        
        # Check if current interval overlaps with the last merged interval
        # Overlap condition: current starts before or at the point the last ends
        if current_start <= last_end:
            # Merge by extending the end if necessary
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            # No overlap, add as new interval
            merged.append((current_start, current_end))
    
    return merged


# Run tests
if __name__ == "__main__":
    test_cases = [
        ([], []),
        ([(1, 3)], [(1, 3)]),
        ([(1, 3), (5, 7)], [(1, 3), (5, 7)]),
        ([(1, 3), (2, 5)], [(1, 5)]),
        ([(1, 3), (3, 5)], [(1, 5)]),
        ([(1, 10), (2, 5), (3, 7)], [(1, 10)]),
        ([(5, 7), (1, 3), (2, 6)], [(1, 7)]),
        ([(1, 2), (3, 4), (5, 6)], [(1, 2), (3, 4), (5, 6)]),
        ([(1, 5), (2, 3)], [(1, 5)]),
        ([(1, 4), (2, 5), (7, 9), (8, 11), (13, 15)], [(1, 5), (7, 11), (13, 15)]),
        ([(0, 0), (1, 1)], [(0, 0), (1, 1)]),
        ([(0, 0), (0, 0)], [(0, 0)]),
    ]
    
    for i, (input_data, expected) in enumerate(test_cases):
        result = merge_intervals(input_data)
        status = "✓" if result == expected else "✗"
        print(f"Test {i+1}: {status}")
        if result != expected:
            print(f"  Input:    {input_data}")
            print(f"  Expected: {expected}")
            print(f"  Got:      {result}")
    
    # Run assertions
    print("\nRunning assertions...")
    assert merge_intervals([]) == []
    assert merge_intervals([(1, 3)]) == [(1, 3)]
    assert merge_intervals([(1, 3), (5, 7)]) == [(1, 3), (5, 7)]
    assert merge_intervals([(1, 3), (2, 5)]) == [(1, 5)]
    assert merge_intervals([(1, 3), (3, 5)]) == [(1, 5)]
    assert merge_intervals([(1, 10), (2, 5), (3, 7)]) == [(1, 10)]
    assert merge_intervals([(5, 7), (1, 3), (2, 6)]) == [(1, 7)]
    assert merge_intervals([(1, 2), (3, 4), (5, 6)]) == [(1, 2), (3, 4), (5, 6)]
    assert merge_intervals([(1, 5), (2, 3)]) == [(1, 5)]
    assert merge_intervals([(1, 4), (2, 5), (7, 9), (8, 11), (13, 15)]) == [(1, 5), (7, 11), (13, 15)]
    assert merge_intervals([(0, 0), (1, 1)]) == [(0, 0), (1, 1)]
    assert merge_intervals([(0, 0), (0, 0)]) == [(0, 0)]
    print("All assertions passed!")
