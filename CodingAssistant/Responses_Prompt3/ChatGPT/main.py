def format_user_line(name: str, age: int, city: str) -> str:
    """
    Format a user's information into a display string.

    Rules:
    - name must be a non-empty string (after stripping whitespace)
    - age must be a non-negative integer (strict type check)
    - city defaults to "Unknown" if None, empty, or whitespace-only

    Returns:
        A formatted string: "<name> (<age>) - <city>"
        or "Invalid user" if validation fails.
    """
    # Validate name
    if name is None or name == "":
        return "Invalid user"

    stripped_name = name.strip()
    if len(stripped_name) == 0:
        return "Invalid user"

    # Validate age (strict type check to match original behavior)
    if age is None or type(age) is not int or age < 0:
        return "Invalid user"

    # Normalize city
    if city is None or city == "":
        normalized_city = "Unknown"
    else:
        stripped_city = city.strip()
        normalized_city = stripped_city if len(stripped_city) > 0 else "Unknown"

    return f"{stripped_name} ({age}) - {normalized_city}"

assert format_user_line(None, 20, "Budapest") == "Invalid user"
assert format_user_line("", 20, "Budapest") == "Invalid user"
assert format_user_line("   ", 20, "Budapest") == "Invalid user"
assert format_user_line("Anna", None, "Budapest") == "Invalid user"
assert format_user_line("Anna", "20", "Budapest") == "Invalid user"
assert format_user_line("Anna", -1, "Budapest") == "Invalid user"
assert format_user_line(" Anna ", 20, " Budapest ") == "Anna (20) - Budapest"
assert format_user_line("Anna", 20, None) == "Anna (20) - Unknown"
assert format_user_line("Anna", 20, "") == "Anna (20) - Unknown"
assert format_user_line("Anna", 20, "   ") == "Anna (20) - Unknown"
print("All tests passed!")