def rle_encode(s: str) -> str:
    """Compress a string using run-length encoding.
    
    Replaces consecutive runs of the same character with <count><char>.
    Single characters still get a count of 1.
    
    Args:
        s: The input string to compress.
        
    Returns:
        The run-length encoded string, or empty string if input is empty.
    """
    if not s:
        return ""
    
    result = []
    count = 1
    prev_char = s[0]
    
    for char in s[1:]:
        if char == prev_char:
            count += 1
        else:
            result.append(f"{count}{prev_char}")
            count = 1
            prev_char = char
    
    # Append the final run
    result.append(f"{count}{prev_char}")
    
    return "".join(result)


def rle_decode(s: str) -> str:
    """Decompress a run-length encoded string.
    
    Reverses the encoding performed by rle_encode. Handles multi-digit counts.
    
    Args:
        s: The run-length encoded string to decompress.
        
    Returns:
        The original decompressed string, or empty string if input is empty.
    """
    if not s:
        return ""
    
    result = []
    i = 0
    
    while i < len(s):
        # Accumulate all consecutive digits to form the count
        count_str = ""
        while i < len(s) and s[i].isdigit():
            count_str += s[i]
            i += 1
        
        # The next character is what to repeat
        if i < len(s):
            char = s[i]
            count = int(count_str)
            result.append(char * count)
            i += 1
    
    return "".join(result)