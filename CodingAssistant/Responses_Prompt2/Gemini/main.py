def is_balanced(text: str) -> bool:
    """
    Checks if brackets (), [], and {} are balanced, ignoring content within double quotes.
    Handles escaped quotes (\\") and ensures unclosed quotes at the end of the string
    do not cause a failure unless there are unbalanced brackets outside.
    """
    stack: list[str] = []
    # Mapping of closing brackets to their corresponding opening brackets
    pairs: dict[str, str] = {')': '(', ']': '[', '}': '{'}
    
    in_quotes: bool = False
    escaped: bool = False

    for ch in text:
        # 1. Handle escaped characters
        if escaped:
            escaped = False
            continue

        if ch == '\\':
            escaped = True
            continue

        # 2. Handle quote toggling
        if ch == '"':
            in_quotes = not in_quotes
            continue

        # 3. Handle bracket logic only if we are outside of quotes
        if not in_quotes:
            if ch in "([{":
                stack.append(ch)
            elif ch in ")]}":
                # If stack is empty or top of stack doesn't match, it's unbalanced
                if not stack or stack[-1] != pairs[ch]:
                    return False
                stack.pop()

    # If the stack is empty, all brackets that were tracked were balanced
    return not stack

# Verification with provided test cases
assert is_balanced("") is True
assert is_balanced("([]){}") is True
assert is_balanced("(]") is False
assert is_balanced("([)]") is False
assert is_balanced('"(]"') is True
assert is_balanced('"("') is True
assert is_balanced('(")")') is True
assert is_balanced('(")")(') is False
assert is_balanced('"a \\" b"') is True
assert is_balanced('"a \\" ( ]"') is True
assert is_balanced('"unclosed') is True
print("All Tests Passed!")