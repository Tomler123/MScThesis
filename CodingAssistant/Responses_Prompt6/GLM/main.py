from typing import List

def group_anagrams(words: List[str]) -> List[List[str]]:
    """Group words that are anagrams of each other.

    The groups are returned in the order of the first appearance of each
    anagram key in the input. Within each group, words keep their original order.

    Args:
        words: List of strings to be grouped.

    Returns:
        List of groups, where each group is a list of anagrams.
    """
    groups_dict: dict[str, List[str]] = {}
    key_order: List[str] = []

    for w in words:
        # The sorted string acts as a canonical key for anagrams.
        key = ''.join(sorted(w))
        if key not in groups_dict:
            groups_dict[key] = []
            key_order.append(key)
        groups_dict[key].append(w)

    return [groups_dict[key] for key in key_order]