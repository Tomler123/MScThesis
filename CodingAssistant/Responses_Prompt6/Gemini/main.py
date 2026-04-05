def group_anagrams(words: list[str]) -> list[list[str]]:
    """
    Group words that are anagrams of each other.
    
    Maintains the original relative order of the groups based on their first
    appearance, as well as the relative order of words within each group.
    
    Args:
        words: A list of strings to be grouped.
        
    Returns:
        A list of lists, where each inner list contains anagrams.
    """
    anagram_map: dict[str, list[str]] = {}
    
    for word in words:
        # Sort the characters of the word to create a canonical key.
        # Anagrams will always result in the exact same sorted string.
        key = "".join(sorted(word))
        
        if key not in anagram_map:
            anagram_map[key] = []
            
        anagram_map[key].append(word)
        
    # Python 3.7+ dictionaries maintain insertion order.
    # Yielding the values directly satisfies the group ordering requirement.
    return list(anagram_map.values())