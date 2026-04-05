def evaluate(expression: str) -> float:
    """
    Evaluate a mathematical expression string respecting operator precedence.

    Supports +, -, *, / (true division), parentheses, and unary minus.
    Raises ValueError for malformed expressions or division by zero.

    Args:
        expression: A string containing a mathematical expression.

    Returns:
        The result of the expression as a float.

    Raises:
        ValueError: For empty input, unmatched parentheses, trailing operators,
                    or division by zero.
    """
    tokens = _tokenize(expression)
    if not tokens:
        raise ValueError("Empty expression")
    pos, result = _parse_expr(tokens, 0)
    if pos != len(tokens):
        raise ValueError(f"Unexpected token at position {pos}: '{tokens[pos]}'")
    return result


def _tokenize(expression: str) -> list[str]:
    """Convert expression string into a list of token strings."""
    tokens: list[str] = []
    i = 0
    s = expression
    while i < len(s):
        if s[i].isspace():
            i += 1
        elif s[i].isdigit() or s[i] == '.':
            j = i
            while j < len(s) and (s[j].isdigit() or s[j] == '.'):
                j += 1
            tokens.append(s[i:j])
            i = j
        elif s[i] in '+-*/()':
            tokens.append(s[i])
            i += 1
        else:
            raise ValueError(f"Invalid character: '{s[i]}'")
    return tokens


def _parse_expr(tokens: list[str], pos: int) -> tuple[int, float]:
    """Parse additive-level expression: expr = term (('+' | '-') term)*"""
    pos, left = _parse_term(tokens, pos)
    while pos < len(tokens) and tokens[pos] in ('+', '-'):
        op = tokens[pos]
        pos += 1
        pos, right = _parse_term(tokens, pos)
        left = left + right if op == '+' else left - right
    return pos, left


def _parse_term(tokens: list[str], pos: int) -> tuple[int, float]:
    """Parse multiplicative-level expression: term = unary (('*' | '/') unary)*"""
    pos, left = _parse_unary(tokens, pos)
    while pos < len(tokens) and tokens[pos] in ('*', '/'):
        op = tokens[pos]
        pos += 1
        pos, right = _parse_unary(tokens, pos)
        if op == '/':
            if right == 0.0:
                raise ValueError("Division by zero")
            left = left / right
        else:
            left = left * right
    return pos, left


def _parse_unary(tokens: list[str], pos: int) -> tuple[int, float]:
    """Parse unary minus or delegate to primary."""
    if pos < len(tokens) and tokens[pos] == '-':
        pos += 1
        pos, val = _parse_unary(tokens, pos)  # right-recursive: handles --3
        return pos, -val
    return _parse_primary(tokens, pos)


def _parse_primary(tokens: list[str], pos: int) -> tuple[int, float]:
    """Parse a number or parenthesised sub-expression."""
    if pos >= len(tokens):
        raise ValueError("Unexpected end of expression: expected a value")
    token = tokens[pos]
    if token == '(':
        pos += 1
        pos, val = _parse_expr(tokens, pos)
        if pos >= len(tokens) or tokens[pos] != ')':
            raise ValueError("Unmatched '(' — missing closing ')'")
        pos += 1  # consume ')'
        return pos, val
    if token == ')':
        raise ValueError("Unexpected ')'")
    if token in ('+', '-', '*', '/'):
        raise ValueError(f"Unexpected operator '{token}': expected a value")
    try:
        return pos + 1, float(token)
    except ValueError:
        raise ValueError(f"Invalid token: '{token}'")