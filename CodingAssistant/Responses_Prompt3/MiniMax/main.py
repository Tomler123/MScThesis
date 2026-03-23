def format_user_line(name: str | None, age: int | None, city: str | None) -> str:
    """
    Format a user line with name, age, and city.

    Args:
        name: The user's name (required, non-empty after stripping).
        age: The user's age (required, must be a positive integer).
        city: The user's city (optional, defaults to "Unknown").

    Returns:
        A formatted string "name (age) - city", or "Invalid user" if validation fails.
    """
    # Validate name: must exist and contain non-whitespace characters
    if not name or not name.strip():
        return "Invalid user"

    # Validate age: must be an integer and non-negative
    if not isinstance(age, int) or age < 0:
        return "Invalid user"

    # Handle city: default to "Unknown" if empty or whitespace
    if city and city.strip():
        city = city.strip()
    else:
        city = "Unknown"

    # Format and return the result
    return f"{name.strip()} ({age}) - {city}"

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