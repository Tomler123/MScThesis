def merge_sort(arr: list[int]) -> list[int]:
    """Sort a list of integers using merge sort (stable, O(n log n)).

    Args:
        arr: The list of integers to sort.

    Returns:
        A new sorted list of integers in ascending order.
    """
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)


def merge(left: list[int], right: list[int]) -> list[int]:
    """Merge two sorted lists into one sorted list (stable).

    Args:
        left: A sorted list of integers.
        right: A sorted list of integers.

    Returns:
        A single merged sorted list.
    """
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])  # ← Bug 1 fixed
            j += 1
    result += left[i:]
    result += right[j:]              # ← Bug 2 fixed
    return result