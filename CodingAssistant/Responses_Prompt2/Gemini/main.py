import re

def rle_encode(s: str) -> str:
    """
    Compress a string using run-length encoding.
    Consecutive characters are replaced with <count><char>.
    """
    if not s:
        return ""

    res = []
    i = 0
    while i < len(s):
        count = 1
        # Check for consecutive identical characters
        while i + 1 < len(s) and s[i] == s[i + 1]:
            i += 1
            count += 1
        res.append(f"{count}{s[i]}")
        i += 1
    
    return "".join(res)

def rle_decode(s: str) -> str:
    """
    Decompress a run-length encoded string.
    Supports multi-digit counts preceding each character.
    """
    if not s:
        return ""

    # Matches one or more digits followed by a single character
    # Group 1: (\d+), Group 2: ([a-zA-Z])
    pairs = re.findall(r"(\d+)([a-zA-Z])", s)
    
    return "".join(str(char) * int(count) for count, char in pairs)

# Verification with provided tests
if __name__ == "__main__":
    # Encoding tests
    assert rle_encode("aaabbc") == "3a2b1c"
    assert rle_encode("a") == "1a"
    assert rle_encode("") == ""
    assert rle_encode("abcd") == "1a1b1c1d"
    assert rle_encode("aaa") == "3a"
    assert rle_encode("aaaaaaaaaaaab") == "12a1b"

    # Decoding tests
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