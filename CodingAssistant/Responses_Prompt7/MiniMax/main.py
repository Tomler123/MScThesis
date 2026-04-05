"""Mathematical expression evaluator with operator precedence.

This module provides a recursive descent parser for evaluating mathematical
expressions supporting +, -, *, /, parentheses, and unary minus.
"""


def evaluate(expression: str) -> float:
    """Evaluate a mathematical expression string respecting operator precedence.

    Args:
        expression: A string containing a mathematical expression with support
                   for +, -, *, / operators, parentheses, and unary minus.

    Returns:
        The result of the evaluated expression as a float.

    Raises:
        ValueError: If the expression is malformed (unmatched parentheses,
                   empty input, trailing operators, or division by zero).
    """
    # Handle empty or whitespace-only input
    expression = expression.strip()
    if not expression:
        raise ValueError("Empty expression")

    # Tokenize the input
    tokens = _tokenize(expression)

    # Check for trailing operators
    if tokens and tokens[-1][0] in ('PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE'):
        raise ValueError("Trailing operator")

    # Parse and evaluate using recursive descent
    parser = _Parser(tokens)
    result = parser.parse()

    # Check if all tokens were consumed
    if parser.pos < len(tokens):
        raise ValueError("Invalid expression")

    return result


def _tokenize(expression: str) -> list[tuple[str, str]]:
    """Convert expression string into a list of tokens.

    Args:
        expression: The input expression string.

    Returns:
        List of tuples (token_type, token_value).

    Raises:
        ValueError: If an invalid character is encountered.
    """
    tokens = []
    i = 0
    n = len(expression)

    while i < n:
        char = expression[i]

        # Skip whitespace
        if char.isspace():
            i += 1
            continue

        # Numbers (including decimals)
        if char.isdigit() or (char == '.' and i + 1 < n and expression[i + 1].isdigit()):
            num_str = ''
            has_dot = False
            while i < n and (expression[i].isdigit() or expression[i] == '.'):
                if expression[i] == '.':
                    if has_dot:
                        raise ValueError("Invalid number format")
                    has_dot = True
                num_str += expression[i]
                i += 1
            tokens.append(('NUMBER', num_str))
            continue

        # Operators and parentheses
        if char == '+':
            tokens.append(('PLUS', '+'))
        elif char == '-':
            tokens.append(('MINUS', '-'))
        elif char == '*':
            tokens.append(('MULTIPLY', '*'))
        elif char == '/':
            tokens.append(('DIVIDE', '/'))
        elif char == '(':
            tokens.append(('LPAREN', '('))
        elif char == ')':
            tokens.append(('RPAREN', ')'))
        else:
            raise ValueError(f"Invalid character: {char}")

        i += 1

    return tokens


class _Parser:
    """Recursive descent parser for mathematical expressions.

    Grammar:
        expression  := term (('+' | '-') term)*
        term        := factor (('*' | '/') factor)*
        factor      := unary
        unary       := '-' unary | primary
        primary     := NUMBER | '(' expression ')'
    """

    def __init__(self, tokens: list[tuple[str, str]]):
        """Initialize the parser with tokens.

        Args:
            tokens: List of tokens from the tokenizer.
        """
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> float:
        """Parse and evaluate the expression.

        Returns:
            The result of evaluating the expression.
        """
        return self._expression()

    def _current(self) -> tuple[str, str] | None:
        """Get the current token without consuming it."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _consume(self, expected_type: str | None = None) -> tuple[str, str]:
        """Consume and return the current token.

        Args:
            expected_type: Optional token type to expect.

        Returns:
            The consumed token.

        Raises:
            ValueError: If the expected token type doesn't match.
        """
        token = self._current()
        if token is None:
            raise ValueError("Unexpected end of expression")

        if expected_type is not None and token[0] != expected_type:
            raise ValueError(f"Expected {expected_type}")

        self.pos += 1
        return token

    def _expression(self) -> float:
        """Parse an expression (lowest precedence: + and -).

        expression := term (('+' | '-') term)*
        """
        result = self._term()

        while True:
            token = self._current()
            if token is None:
                break

            if token[0] == 'PLUS':
                self._consume('PLUS')
                result = result + self._term()
            elif token[0] == 'MINUS':
                self._consume('MINUS')
                result = result - self._term()
            else:
                break

        return result

    def _term(self) -> float:
        """Parse a term (higher precedence than expression: * and /).

        term := factor (('*' | '/') factor)*
        """
        result = self._factor()

        while True:
            token = self._current()
            if token is None:
                break

            if token[0] == 'MULTIPLY':
                self._consume('MULTIPLY')
                result = result * self._factor()
            elif token[0] == 'DIVIDE':
                self._consume('DIVIDE')
                divisor = self._factor()
                if divisor == 0:
                    raise ValueError("Division by zero")
                result = result / divisor
            else:
                break

        return result

    def _factor(self) -> float:
        """Parse a factor (handles unary minus).

        factor := unary
        unary  := '-' unary | primary
        """
        return self._unary()

    def _unary(self) -> float:
        """Parse a unary expression (handles unary minus).

        unary := '-' unary | primary
        """
        token = self._current()

        if token is not None and token[0] == 'MINUS':
            self._consume('MINUS')
            return -self._unary()

        return self._primary()

    def _primary(self) -> float:
        """Parse a primary expression (number or parenthesized expression).

        primary := NUMBER | '(' expression ')'
        """
        token = self._current()

        if token is None:
            raise ValueError("Unexpected end of expression")

        if token[0] == 'NUMBER':
            self._consume('NUMBER')
            return float(token[1])

        if token[0] == 'LPAREN':
            self._consume('LPAREN')
            result = self._expression()
            self._consume('RPAREN')  # Will raise ValueError if not matched
            return result

        raise ValueError(f"Unexpected token: {token[1]}")


# Run tests if executed directly
if __name__ == "__main__":
    from math import isclose

    # Basic operations
    assert evaluate("2 + 3") == 5.0
    assert evaluate("2 + 3 * 4") == 14.0
    assert evaluate("(2 + 3) * 4") == 20.0
    assert evaluate("10 / 4") == 2.5
    assert evaluate("2 * 3 + 4 * 5") == 26.0
    assert evaluate(" 7 ") == 7.0
    assert evaluate("(((3)))") == 3.0

    # Unary minus
    assert evaluate("-3") == -3.0
    assert evaluate("-(2 + 3)") == -5.0
    assert evaluate("2 * -3") == -6.0

    # Mixed operations
    assert evaluate("1 + 2 * 3 - 4 / 2") == 5.0
    assert isclose(evaluate("10 / 3"), 10 / 3)
    assert evaluate("(1 + 2) * (3 + 4)") == 21.0
    assert evaluate("2 + 3 * 4 - 1") == 13.0
    assert evaluate("100") == 100.0
    assert evaluate("0 * 999") == 0.0

    # Error cases
    try:
        evaluate("")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    try:
        evaluate("2 +")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    try:
        evaluate("(2 + 3")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    try:
        evaluate("10 / 0")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("All tests passed!")
