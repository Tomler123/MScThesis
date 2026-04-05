def evaluate(expression: str) -> float:
    """
    Evaluate a mathematical expression string respecting operator precedence.
    
    Supports +, -, *, /, (), and unary -. 
    Raises ValueError for malformed expressions or division by zero.
    """
    # 1. Lexical Analysis (Tokenization)
    tokens = []
    i = 0
    length = len(expression)
    
    while i < length:
        char = expression[i]
        
        if char.isspace():
            i += 1
            continue
            
        if char in "+-*/()":
            tokens.append(char)
            i += 1
        elif char.isdigit() or char == '.':
            start = i
            dot_count = 0
            while i < length and (expression[i].isdigit() or expression[i] == '.'):
                if expression[i] == '.':
                    dot_count += 1
                i += 1
            if dot_count > 1:
                raise ValueError("Invalid number format")
            # Convert the matched substring directly to a float
            try:
                tokens.append(float(expression[start:i]))
            except ValueError:
                raise ValueError(f"Invalid numeric sequence: {expression[start:i]}")
        else:
            raise ValueError(f"Invalid character encountered: {char}")

    if not tokens:
        raise ValueError("Empty expression")

    # 2. Syntax Analysis & Evaluation (Parser)
    pos = 0
    
    def peek():
        """Return the current token without consuming it."""
        if pos < len(tokens):
            return tokens[pos]
        return None

    def consume():
        """Consume and return the current token, advancing the position."""
        nonlocal pos
        token = peek()
        pos += 1
        return token

    def parse_factor() -> float:
        """Parse numbers, unary operators, and parentheses (highest precedence)."""
        token = consume()
        if token is None:
            raise ValueError("Unexpected end of expression")
            
        if token == '+':
            return parse_factor()
        if token == '-':
            return -parse_factor()
        if token == '(':
            val = parse_expression()
            if consume() != ')':
                raise ValueError("Unmatched parenthesis")
            return val
        if isinstance(token, float):
            return token
            
        raise ValueError(f"Unexpected token: {token}")

    def parse_term() -> float:
        """Parse multiplication and division (medium precedence)."""
        val = parse_factor()
        while peek() in ('*', '/'):
            op = consume()
            right = parse_factor()
            if op == '*':
                val *= right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                val /= right
        return val

    def parse_expression() -> float:
        """Parse addition and subtraction (lowest precedence)."""
        val = parse_term()
        while peek() in ('+', '-'):
            op = consume()
            right = parse_term()
            if op == '+':
                val += right
            else:
                val -= right
        return val

    # Start evaluation
    result = parse_expression()
    
    # If we have successfully parsed an expression but there are still tokens left,
    # it means the expression was malformed (e.g., "2 + 3 4" or trailing operators)
    if pos < len(tokens):
        raise ValueError("Trailing characters or malformed expression")
        
    return result