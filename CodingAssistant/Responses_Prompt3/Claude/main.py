def format_user_line(name: str | None, age: int | None, city: str | None) -> str:
    """
    Format a user record as a display string.

    Args:
        name: The user's name. Must be a non-empty, non-blank string.
        age:  The user's age. Must be a non-negative integer.
        city: The user's city. Defaults to "Unknown" if missing or blank.

    Returns:
        A formatted string like "Anna (20) - Budapest",
        or "Invalid user" if name or age are invalid.
    """
    INVALID = "Invalid user"
    DEFAULT_CITY = "Unknown"

    is_invalid_name = not name or not isinstance(name, str)
    if is_invalid_name:
        return INVALID

    is_invalid_age = age is None or not isinstance(age, int) or age < 0
    if is_invalid_age:
        return INVALID

    clean_name = name.strip()
    if not clean_name:
        return INVALID

    clean_city = city.strip() if isinstance(city, str) else ""
    resolved_city = clean_city if clean_city else DEFAULT_CITY

    return f"{clean_name} ({age}) - {resolved_city}"

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