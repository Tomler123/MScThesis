def is_balanced(text: str) -> bool:
    """
    Return True if all bracket pairs ( ), [ ], { } in *text* are balanced.

    Brackets that appear inside double-quoted regions are ignored.
    A backslash immediately before a double quote (\\") is treated as an
    escaped quote and does NOT open or close a quoted region.
    """
    stack: list[str] = []
    in_quotes: bool = False
    pairs: dict[str, str] = {')': '(', ']': '[', '}': '{'}

    i = 0
    while i < len(text):
        ch = text[i]

        if ch == '\\' and in_quotes:
            i += 2          # skip the escaped character (e.g. \") wholesale
            continue

        if ch == '"':
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
assert is_balanced('"(]"') is True
assert is_balanced('"("') is True
assert is_balanced('(")")') is True
assert is_balanced('(")")(') is False
assert is_balanced('"a \\" b"') is True
assert is_balanced('"a \\" ( ]"') is True
assert is_balanced('"unclosed') is True
print("All tests passed.")