def split_csv_line(line: str) -> list[str]:
    """
    Split a single CSV line into fields (RFC4180-like), without external libraries.
    
    Handles quoted fields, escaped double quotes (""), and literal commas 
    within quotes while preserving whitespace.
    """
    fields = []
    current_field = []
    in_quotes = False
    i = 0
    
    while i < len(line):
        char = line[i]
        
        if in_quotes:
            if char == '"':
                # Check if this is an escaped quote ("")
                if i + 1 < len(line) and line[i + 1] == '"':
                    current_field.append('"')
                    i += 1  # Skip the second quote
                else:
                    # Closing quote
                    in_quotes = False
            else:
                # Literal character inside quotes
                current_field.append(char)
        else:
            if char == '"':
                # Opening quote
                in_quotes = True
            elif char == ',':
                # Field delimiter
                fields.append("".join(current_field))
                current_field = []
            else:
                # Regular character outside quotes
                current_field.append(char)
        i += 1
        
    # Append the final field after the loop ends
    fields.append("".join(current_field))
    return fields

# Verification Tests
if __name__ == "__main__":
    assert split_csv_line("a,b,c") == ["a", "b", "c"]
    assert split_csv_line('a,"b,c",d') == ["a", "b,c", "d"]
    assert split_csv_line('"a","b","c"') == ["a", "b", "c"]
    assert split_csv_line('"a""b",c') == ['a"b', "c"]
    assert split_csv_line(',"",') == ["", "", ""]
    assert split_csv_line('"  spaced  ",x') == ["  spaced  ", "x"]
    assert split_csv_line('"""",x') == ['"', "x"]
    assert split_csv_line('a,"b""c,d""e",f') == ["a", 'b"c,d"e', "f"]
    print("All tests passed!")