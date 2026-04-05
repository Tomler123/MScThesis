from collections import OrderedDict


def group_anagrams(words: list[str]) -> list[list[str]]:
    """Group words that are anagrams of each other efficiently.

    Words are grouped by a canonical key formed by sorting their characters.
    Within each group, words keep their original input order.
    The order of groups matches the first time each anagram class appears.
    Matching is case-sensitive, so uppercase and lowercase letters differ.
    Empty strings are treated as anagrams of each other.
    """
    groups: OrderedDict[str, list[str]] = OrderedDict()

    for word in words:
        key = "".join(sorted(word))
        if key not in groups:
            groups[key] = []
        groups[key].append(word)

    return list(groups.values())