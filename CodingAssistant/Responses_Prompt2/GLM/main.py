def is_balanced(text: str) -> bool:
    """
    Check if brackets (), [], {} are balanced in the string, ignoring brackets
    inside double quotes. Handles escaped quotes (\\") inside quoted regions.
    """
    stack = []
    in_quotes = False
    pairs = {')': '(', ']': '[', '}': '{'}

    for i, ch in enumerate(text):
        # Handle quote toggling and escaping
        if ch == '"':
            # Check if the quote is escaped by a backslash
            # We check the count of consecutive backslashes preceding the quote.
            # If odd, it's escaped; if even (including 0), it's not.
            is_escaped = False
            if i > 0:
                backslash_count = 0
                j = i - 1
                while j >= 0 and text[j] == '\\':
                    backslash_count += 1
                    j -= 1
                is_escaped = (backslash_count % 2 == 1)

            if not is_escaped:
                in_quotes = not in_quotes

        # Process brackets only if we are not inside quotes
        if not in_quotes:
            if ch in "([{":
                stack.append(ch)
            elif ch in ")]}":
                if not stack or stack[-1] != pairs[ch]:
                    return False
                stack.pop()

    return stack == []

assert is_balanced("") is True
assert is_balanced("([]){}") is True
assert is_balanced("(]") is False
assert is_balanced("([)]") is False
assert is_balanced('"(]"') is True                  # brackets inside quotes ignored
assert is_balanced('"("') is True                   # ignored
assert is_balanced('(")")') is True                 # inside quotes ignored, outside balanced
assert is_balanced('(")")(') is False               # outside has extra '('
assert is_balanced('"a \\" b"') is True             # escaped quote inside quotes
assert is_balanced('"a \\" ( ]"') is True           # brackets inside quotes ignored
assert is_balanced('"unclosed') is True             # treat as: in_quotes at end -> still ignore inside (no bracket constraint)
print("All Tests Passed!")