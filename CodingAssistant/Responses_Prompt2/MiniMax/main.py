"""Run-Length Encoding (RLE) implementation."""


def rle_encode(s: str) -> str:
    """
    Compress a string using run-length encoding.

    Replaces consecutive runs of the same character with <count><char>.
    Single characters still get a count of 1.

    Args:
        s: The input string to compress.

    Returns:
        The RLE encoded string.

    Examples:
        >>> rle_encode("aaabbc")
        '3a2b1c'
        >>> rle_encode("a")
        '1a'
        >>> rle_encode("")
        ''
    """
    if not s:
        return ""

    result = []
    current_char = s[0]
    count = 1

    for char in s[1:]:
        if char == current_char:
            count += 1
        else:
            result.append(f"{count}{current_char}")
            current_char = char
            count = 1

    # Append the last run
    result.append(f"{count}{current_char}")

    return "".join(result)


def rle_decode(s: str) -> str:
    """
    Decompress a run-length encoded string.

    Reverses the encoding by parsing count-character pairs.
    Supports multi-digit counts.

    Args:
        s: The RLE encoded string to decompress.

    Returns:
        The original uncompressed string.

    Examples:
        >>> rle_decode("3a2b1c")
        'aaabbc'
        >>> rle_decode("1a")
        'a'
        >>> rle_decode("")
        ''
        >>> rle_decode("12a1b")
        'aaaaaaaaaaaab'
    """
    if not s:
        return ""

    result = []
    i = 0

    while i < len(s):
        # Parse the count (may be multi-digit)
        count_str = ""
        while i < len(s) and s[i].isdigit():
            count_str += s[i]
            i += 1

        # Extract the character
        if i < len(s):
            char = s[i]
            i += 1

            # Repeat the character count times
            count = int(count_str)
            result.append(char * count)

    return "".join(result)


if __name__ == "__main__":
    # Run tests
    assert rle_encode("aaabbc") == "3a2b1c"
    assert rle_encode("a") == "1a"
    assert rle_encode("") == ""
    assert rle_encode("abcd") == "1a1b1c1d"
    assert rle_encode("aaa") == "3a"
    assert rle_encode("aaaaaaaaaaaab") == "12a1b"

    assert rle_decode("3a2b1c") == "aaabbc"
    assert rle_decode("1a") == "a"
    assert rle_decode("") == ""
    assert rle_decode("12a1b") == "aaaaaaaaaaaab"
    assert rle_decode("1a1b1c1d") == "abcd"
    assert rle_decode("10x") == "xxxxxxxxxx"

    # Roundtrip property
    for test in ["hello", "aaabbbccc", "x", "", "aabbccdd", "zzzzzzzzzz"]:
        assert rle_decode(rle_encode(test)) == test

    print("All tests passed!")
