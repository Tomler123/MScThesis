def rle_encode(s: str) -> str:
    """Compress a string using run-length encoding.

    Consecutive runs of the same character are replaced with "<count><char>".
    Single characters are encoded with a count of 1.

    Examples:
        "aaabbc" -> "3a2b1c"
        "a" -> "1a"
        "" -> ""
    """
    if not s:
        return ""

    parts: list[str] = []
    current_char = s[0]
    count = 1

    for char in s[1:]:
        if char == current_char:
            count += 1
        else:
            parts.append(f"{count}{current_char}")
            current_char = char
            count = 1

    parts.append(f"{count}{current_char}")
    return "".join(parts)


def rle_decode(s: str) -> str:
    """Decompress a run-length encoded string.

    The input is expected to consist of one or more "<count><char>" groups,
    where count may be multiple digits.

    Examples:
        "3a2b1c" -> "aaabbc"
        "12a1b" -> "aaaaaaaaaaaab"
        "" -> ""
    """
    if not s:
        return ""

    parts: list[str] = []
    count_str = ""

    for char in s:
        if char.isdigit():
            count_str += char
        else:
            parts.append(char * int(count_str))
            count_str = ""

    return "".join(parts)