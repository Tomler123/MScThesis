def merge_sort(arr: list[int]) -> list[int]:
    """Sort a list of integers using the merge sort algorithm.

    Args:
        arr: The list of integers to be sorted.

    Returns:
        A new list containing the sorted integers.
    """
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left: list[int], right: list[int]) -> list[int]:
    """Merge two sorted lists into a single sorted list (stable).

    Args:
        left: A sorted list of integers.
        right: A sorted list of integers.

    Returns:
        A sorted list containing all elements from left and right.
    """
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result += left[i:]
    result += right[j:]
    return result