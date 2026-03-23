def split_csv_line(line: str) -> list[str]:
    """Split a single CSV line into fields according to RFC4180-like rules.

    Fields are separated by commas. Fields may be quoted with double quotes.
    Inside quoted fields, a double quote is escaped as two double quotes.
    Commas inside quoted fields do not split fields. Whitespace is preserved exactly.
    Returns a list of field strings with quotes removed and escaped quotes unescaped.
    """
    fields: list[str] = []
    current: list[str] = []
    in_quotes = False
    i = 0
    n = len(line)

    while i < n:
        ch = line[i]
        if not in_quotes:
            if ch == ',':
                fields.append(''.join(current))
                current = []
                i += 1
            elif ch == '"':
                in_quotes = True
                i += 1
            else:
                current.append(ch)
                i += 1
        else:  # inside a quoted field
            if ch == '"':
                # Look ahead for escaped double quote
                if i + 1 < n and line[i + 1] == '"':
                    current.append('"')
                    i += 2
                else:
                    # Closing quote
                    in_quotes = False
                    i += 1
            else:
                current.append(ch)
                i += 1

    # Append the last field
    fields.append(''.join(current))
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