def format_user_line(name: str, age: int, city: str) -> str:
    """
    Formats user details into a specific string format.

    Validates the input name and age. Returns "Invalid user" if the name is
    None, empty, or whitespace-only, or if the age is None, not an integer,
    or negative. Handles missing or empty cities by defaulting to "Unknown".

    Args:
        name: The user's name.
        age: The user's age (must be a non-negative integer).
        city: The user's city.

    Returns:
        A formatted string "Name (Age) - City" or "Invalid user".
    """
    # Validate name: check for None, empty string, or whitespace-only string
    if name is None or name.strip() == "":
        return "Invalid user"

    # Validate age: check for None, incorrect type, or negative value
    if age is None or not isinstance(age, int) or age < 0:
        return "Invalid user"

    # Normalize city: default to "Unknown" if None, empty, or whitespace-only
    if city is None or city.strip() == "":
        city = "Unknown"

    clean_name = name.strip()
    clean_city = city.strip()

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