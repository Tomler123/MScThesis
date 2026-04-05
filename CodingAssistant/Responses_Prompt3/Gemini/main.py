def merge_sort(arr: list[int]) -> list[int]:
    """
    Sorts a list of integers in ascending order using the merge sort algorithm.
    
    This implementation is recursive and maintains stability (equal elements 
    retain their original relative order).
    """
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left: list[int], right: list[int]) -> list[int]:
    """
    Merges two sorted lists into a single sorted list.
    
    Uses two pointers to compare elements from the left and right lists,
    appending the smaller element to the result list to maintain order.
    """
    result = []
    i = j = 0
    
    # Compare elements from both lists and merge them in order
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            # Bug 1 Fixed: Changed right[i] to right[j]
            result.append(right[j])
            j += 1
            
    # Append any remaining elements from either list
    result += left[i:]
    # Bug 2 Fixed: Changed right[:j] to right[j:]
    result += right[j:]
    
    return result