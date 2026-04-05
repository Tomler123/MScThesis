def evaluate(expression: str) -> float:
    """Evaluate a mathematical expression string respecting operator precedence.

    Supports +, -, *, /, parentheses, and unary minus. Whitespace is ignored.

    Args:
        expression: The expression to evaluate.

    Returns:
        The numeric result as a float.

    Raises:
        ValueError: If the expression is malformed (empty, invalid characters,
            unmatched parentheses, missing operands, division by zero, etc.)
    """
    # ---------- Tokenization ----------
    tokens = []
    i = 0
    n = len(expression)
    while i < n:
        ch = expression[i]
        if ch.isspace():
            i += 1
            continue
        if ch.isdigit() or ch == '.':
            start = i
            while i < n and (expression[i].isdigit() or expression[i] == '.'):
                i += 1
            num_str = expression[start:i]
            try:
                num = float(num_str)
            except ValueError:
                raise ValueError(f"Invalid number: {num_str}")
            tokens.append(('NUM', num))
            continue
        if ch in '+-*/':
            tokens.append(('OP', ch))
            i += 1
            continue
        if ch == '(':
            tokens.append(('LPAREN',))
            i += 1
            continue
        if ch == ')':
            tokens.append(('RPAREN',))
            i += 1
            continue
        raise ValueError(f"Invalid character: {ch}")
    tokens.append(('EOF',))          # sentinel

    # ---------- Recursive descent parser ----------
    pos = 0
    token_count = len(tokens)

    def current():
        return tokens[pos]

    def advance():
        nonlocal pos
        pos += 1

    def parse_expression() -> float:
        left = parse_term()
        while current()[0] == 'OP' and current()[1] in ('+', '-'):
            op = current()[1]
            advance()
            right = parse_term()
            if op == '+':
                left += right
            else:
                left -= right
        return left

    def parse_term() -> float:
        left = parse_factor()
        while current()[0] == 'OP' and current()[1] in ('*', '/'):
            op = current()[1]
            advance()
            right = parse_factor()
            if op == '*':
                left *= right
            else:
                if right == 0.0:
                    raise ValueError("Division by zero")
                left /= right
        return left

    def parse_factor() -> float:
        tok = current()
        if tok[0] == 'NUM':
            val = tok[1]
            advance()
            return val
        elif tok[0] == 'LPAREN':
            advance()
            val = parse_expression()
            if current()[0] != 'RPAREN':
                raise ValueError("Missing closing parenthesis")
            advance()
            return val
        elif tok[0] == 'OP' and tok[1] == '-':
            advance()
            return -parse_factor()
        else:
            raise ValueError("Invalid expression: expected number, '(' or unary minus")

    result = parse_expression()
    if current()[0] != 'EOF':
        raise ValueError("Extra tokens after expression")
    return result