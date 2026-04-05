def rle_encode(s: str) -> str:
    """Compress a string using run-length encoding.

    Each run of consecutive identical characters is replaced by
    <count><char>, where count is always present (even for single chars).

    Args:
        s: The input string to encode.

    Returns:
        The run-length encoded string, e.g. "aaabbc" -> "3a2b1c".
    """
    if not s:
        return ""
    result = []
    count = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            count += 1
        else:
            result.append(f"{count}{s[i - 1]}")
            count = 1
    result.append(f"{count}{s[-1]}")
    return "".join(result)


def rle_decode(s: str) -> str:
    """Decompress a run-length encoded string.

    Parses alternating sequences of digits (multi-digit supported) and
    a single character, expanding each pair into a repeated character run.

    Args:
        s: The run-length encoded string, e.g. "3a2b1c".

    Returns:
        The decoded original string, e.g. "aaabbc".
    """
    if not s:
        return ""
    result = []
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j].isdigit():
            j += 1
        count = int(s[i:j])
        result.append(s[j] * count)
        i = j + 1
    return "".join(result)