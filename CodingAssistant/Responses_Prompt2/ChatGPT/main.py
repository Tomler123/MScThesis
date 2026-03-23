def split_csv_line(line: str) -> list[str]:
    """
    Split a single RFC4180-like CSV line into fields.

    Rules supported:
    - Fields are separated by commas.
    - Fields may be quoted with double quotes.
    - Inside quoted fields, two consecutive double quotes represent one literal quote.
    - Commas inside quoted fields are treated as data, not separators.
    - Quotes are removed from quoted fields, and doubled quotes are unescaped.

    The parser does not use the csv module or any external libraries.
    """
    fields: list[str] = []
    field_chars: list[str] = []
    in_quotes = False
    i = 0
    n = len(line)

    while i < n:
        ch = line[i]

        if in_quotes:
            if ch == '"':
                if i + 1 < n and line[i + 1] == '"':
                    field_chars.append('"')
                    i += 2
                else:
                    in_quotes = False
                    i += 1
            else:
                field_chars.append(ch)
                i += 1
        else:
            if ch == ',':
                fields.append(''.join(field_chars))
                field_chars = []
                i += 1
            elif ch == '"' and not field_chars:
                in_quotes = True
                i += 1
            else:
                field_chars.append(ch)
                i += 1

    if in_quotes:
        raise ValueError("Unterminated quoted field")

    fields.append(''.join(field_chars))
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