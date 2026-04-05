from collections import defaultdict

def group_anagrams(words: list[str]) -> list[list[str]]:
    """
    Group words that are anagrams of each other.

    Each group preserves the original input order of its words, and groups
    are ordered by the first appearance of their key in the input.

    Args:
        words: A list of strings to group by anagram equivalence.

    Returns:
        A list of groups, where each group is a list of anagram-equivalent words.

    Time complexity:  O(n * k log k) — n words, each sorted in O(k log k).
    Space complexity: O(n * k)       — storing all words in the hash map.
    """
    groups: dict[tuple, list[str]] = {}
    for word in words:
        key = tuple(sorted(word))       # O(k log k) per word
        if key not in groups:
            groups[key] = []
        groups[key].append(word)
    return list(groups.values())