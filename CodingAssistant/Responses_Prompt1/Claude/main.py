def split_csv_line(line: str) -> list[str]:
    """
    Split a single CSV line into fields following RFC 4180-like rules.

    Rules:
    - Fields are separated by commas.
    - Fields may be optionally enclosed in double quotes.
    - A literal double quote inside a quoted field is represented as two
      consecutive double quotes ("").
    - Commas inside quoted fields are treated as part of the field value.
    - Whitespace is preserved exactly as it appears inside fields.

    Args:
        line: A single CSV line (no trailing newline expected, but tolerated).

    Returns:
        A list of decoded field strings with enclosing quotes removed and
        escaped double-quotes ("") replaced by a single double-quote (").
    """
    fields: list[str] = []
    current: list[str] = []
    i = 0
    n = len(line)

    while i <= n:
        # --- End of line: flush the current field and stop ---
        if i == n:
            fields.append("".join(current))
            break

        ch = line[i]

        # --- Start of a quoted field ---
        if ch == '"' and not current:
            i += 1  # skip the opening quote
            while i < n:
                c = line[i]
                if c == '"':
                    # Peek ahead: "" is an escaped quote, otherwise closing quote
                    if i + 1 < n and line[i + 1] == '"':
                        current.append('"')
                        i += 2  # consume both quote characters
                    else:
                        i += 1  # consume closing quote
                        break
                else:
                    current.append(c)
                    i += 1
            # After the closing quote the next character must be ',' or end-of-line
            # (malformed input is parsed leniently: any trailing chars are ignored)

        # --- Field separator: commit the current field ---
        elif ch == ',':
            fields.append("".join(current))
            current = []
            i += 1

        # --- Ordinary unquoted character ---
        else:
            current.append(ch)
            i += 1

    return fields

assert split_csv_line("a,b,c") == ["a", "b", "c"]
assert split_csv_line('a,"b,c",d') == ["a", "b,c", "d"]
assert split_csv_line('"a","b","c"') == ["a", "b", "c"]
assert split_csv_line('"a""b",c') == ['a"b', "c"]
assert split_csv_line(',"",') == ["", "", ""]
assert split_csv_line('"  spaced  ",x') == ["  spaced  ", "x"]
assert split_csv_line('"""",x') == ['"', "x"]
assert split_csv_line('a,"b""c,d""e",f') == ["a", 'b"c,d"e', "f"]
print("All tests passed.")