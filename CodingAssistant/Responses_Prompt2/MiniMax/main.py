def is_balanced(text: str) -> bool:
    """
    Check if brackets are balanced in a string.

    Brackets are (), [], {}.
    Brackets inside double quotes are ignored.
    Escaped quotes (\\") inside quotes do not end the quoted region.

    Args:
        text: The string to check

    Returns:
        True if all brackets are properly balanced, False otherwise
    """
    stack = []
    in_quotes = False

    pairs = {')': '(', ']': '[', '}': '{'}

    i = 0
    while i < len(text):
        ch = text[i]

        if ch == '"':
            # Check if this is an escaped quote (only if we have a backslash before it)
            if i > 0 and text[i - 1] == '\\':
                # Escaped quote - don't toggle in_quotes
                pass
            else:
                in_quotes = not in_quotes
        elif not in_quotes:
            if ch in "([{":
                stack.append(ch)
            elif ch in ")]}":
                if not stack or stack[-1] != pairs[ch]:
                    return False
                stack.pop()

        i += 1

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