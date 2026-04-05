"""Efficient anagram grouping algorithm."""


def group_anagrams(words: list[str]) -> list[list[str]]:
    """Group words that are anagrams of each other.

    Uses sorted characters as a canonical key for each anagram group.
    Time complexity: O(n * k log k) where n = number of words,
                     k = max word length.
    Space complexity: O(n * k) for storing all words.
    """
    if not words:
        return []

    # Dictionary to group words by their anagram key
    # Keys are sorted character strings, values are lists of words
    anagram_groups: dict[str, list[str]] = {}

    for word in words:
        # Create a key by sorting the word's characters
        key = ''.join(sorted(word))
        if key not in anagram_groups:
            anagram_groups[key] = []
        anagram_groups[key].append(word)

    # Return groups in the order they first appeared
    return list(anagram_groups.values())


# Tests
if __name__ == "__main__":
    assert group_anagrams([]) == []
    assert group_anagrams(["a"]) == [["a"]]
    assert group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]) == [
        ["eat", "tea", "ate"], ["tan", "nat"], ["bat"]
    ]
    assert group_anagrams(["", "", "x"]) == [["", ""], ["x"]]
    assert group_anagrams(["abc", "def", "ghi"]) == [["abc"], ["def"], ["ghi"]]
    assert group_anagrams(["listen", "silent", "enlist"]) == [["listen", "silent", "enlist"]]
    assert group_anagrams(["Tea", "eat"]) == [["Tea"], ["eat"]]  # case-sensitive
    assert group_anagrams(["a", "b", "a"]) == [["a", "a"], ["b"]]

    print("All tests passed!")
