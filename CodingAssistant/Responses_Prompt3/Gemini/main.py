def format_user_line(name: str | None, age: int | None, city: str | None) -> str:
    """
    Formats user data into a string: 'Name (Age) - City'.
    
    Validates that name is a non-empty string and age is a non-negative integer.
    Returns 'Invalid user' if validation fails. Defaults empty cities to 'Unknown'.
    """
    # Validate name: ensure it is not None and contains non-whitespace characters
    if not name or not name.strip():
        return "Invalid user"

    # Validate age: must be exactly an int (not a bool or string) and >= 0
    if type(age) is not int or age < 0:
        return "Invalid user"

    # Normalize city: default to 'Unknown' if None, empty, or only whitespace
    if not city or not city.strip():
        clean_city = "Unknown"
    else:
        clean_city = city.strip()

    clean_name = name.strip()
    
    return f"{clean_name} ({age}) - {clean_city}"

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