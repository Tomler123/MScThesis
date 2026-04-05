def merge_sort(arr: list[int]) -> list[int]:
    """
    Sort a list of integers using the merge sort algorithm.

    Args:
        arr: A list of integers to be sorted.

    Returns:
        A new list containing the sorted integers in ascending order.
        The sort is stable, meaning equal elements maintain their original relative order.

    Examples:
        >>> merge_sort([3, 1, 2])
        [1, 2, 3]
        >>> merge_sort([5, 3, 8, 1, 2])
        [1, 2, 3, 5, 8]
    """
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    return merge(left, right)


def merge(left: list[int], right: list[int]) -> list[int]:
    """
    Merge two sorted lists into a single sorted list.

    Args:
        left: A sorted list of integers.
        right: A sorted list of integers.

    Returns:
        A merged sorted list containing all elements from both input lists.

    Examples:
        >>> merge([1, 3, 5], [2, 4, 6])
        [1, 2, 3, 4, 5, 6]
    """
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])  # Fixed: was right[i], should be right[j]
            j += 1

    result += left[i:]
    result += right[j:]  # Fixed: was right[:j], should be right[j:]

    return result


# Test the implementation
if __name__ == "__main__":
    assert merge_sort([]) == []
    assert merge_sort([1]) == [1]
    assert merge_sort([3, 1, 2]) == [1, 2, 3]
    assert merge_sort([5, 3, 8, 1, 2]) == [1, 2, 3, 5, 8]
    assert merge_sort([1, 1, 1]) == [1, 1, 1]
    assert merge_sort([4, 2, 2, 1, 3, 3]) == [1, 2, 2, 3, 3, 4]
    assert merge_sort([-3, -1, -2, 0]) == [-3, -2, -1, 0]
    assert merge_sort([10, 9, 8, 7, 6, 5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert merge_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
    assert merge_sort([2, 1]) == [1, 2]
    print("All tests passed!")
