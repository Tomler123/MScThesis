def format_dict(name: str, age: int, city: str) -> str:
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