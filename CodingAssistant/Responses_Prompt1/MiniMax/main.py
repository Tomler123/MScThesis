def split_csv_line(line: str) -> list[str]:
    """
    Split a single CSV line into fields (RFC4180-like), without external libraries.

    Rules:
    - Fields are separated by commas.
    - Fields may be quoted with double quotes "...".
    - Inside quoted fields, a literal quote is escaped as "" (two quotes).
    - Commas inside quoted fields do not split fields.
    - Preserve whitespace exactly as it appears inside fields.
    - Return a list of strings (decoded field values, quotes removed, "" unescaped).

    Args:
        line: A single CSV line string.

    Returns:
        A list of field strings with quotes removed and escaped quotes decoded.
    """
    fields = []
    current_field = []
    in_quotes = False
    i = 0

    while i < len(line):
        char = line[i]

        if in_quotes:
            if char == '"':
                # Check if next char is also a quote (escaped quote "")
                if i + 1 < len(line) and line[i + 1] == '"':
                    # This is an escaped quote - add one " to the field
                    current_field.append('"')
                    i += 2  # Skip both quotes
                else:
                    # This is the end of the quoted field
                    in_quotes = False
                    i += 1
            else:
                # Any other character inside quotes is added verbatim
                current_field.append(char)
                i += 1
        else:
            if char == '"':
                # Start of a quoted field
                in_quotes = True
                i += 1
            elif char == ',':
                # Field separator
                fields.append(''.join(current_field))
                current_field = []
                i += 1
            else:
                # Regular character outside quotes
                current_field.append(char)
                i += 1

    # Append the last field (handles trailing comma cases)
    fields.append(''.join(current_field))

    return fields


# Run the test cases
if __name__ == "__main__":
    # Test 1: Simple fields
    assert split_csv_line("a,b,c") == ["a", "b", "c"], "Test 1 failed"

    # Test 2: Quoted field containing comma
    assert split_csv_line('a,"b,c",d') == ["a", "b,c", "d"], "Test 2 failed"

    # Test 3: All quoted fields
    assert split_csv_line('"a","b","c"') == ["a", "b", "c"], "Test 3 failed"

    # Test 4: Escaped quotes inside quoted field
    assert split_csv_line('"a""b",c') == ['a"b', "c"], "Test 4 failed"

    # Test 5: Empty fields with quoted empty string
    assert split_csv_line(',"",') == ["", "", ""], "Test 5 failed"

    # Test 6: Whitespace preservation
    assert split_csv_line('"  spaced  ",x') == ["  spaced  ", "x"], "Test 6 failed"

    # Test 7: Multiple escaped quotes ("""" = one literal quote)
    assert split_csv_line('"""",x') == ['"', "x"], "Test 7 failed"

    # Test 8: Complex case with mixed quotes and commas
    assert split_csv_line('a,"b""c,d""e",f') == ["a", 'b"c,d"e', "f"], "Test 8 failed"

    print("All tests passed!")
