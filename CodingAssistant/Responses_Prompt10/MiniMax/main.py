def parse_config(text: str) -> dict:
    """Parse a simple configuration language into a nested dictionary."""
    result = {}
    pending_inheritances = []  # (section_dict, parent_name)
    section_dicts = {}  # section_name -> dict for inheritance tracking

    current_section = None  # Reference to the actual section dict

    for line in text.split('\n'):
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue

        # Check for section header
        if line.startswith('[') and line.endswith(']'):
            section_content = line[1:-1].strip()

            # Parse inheritance and nested path
            # Format: [section_path : parent] or just [section_path]
            parent = None
            if ':' in section_content:
                # Use rsplit to handle nested paths with inheritance correctly
                # e.g., "a.b : parent" -> base_path="a.b", parent="parent"
                parts = section_content.rsplit(':', 1)
                section_path_str = parts[0].strip()
                parent = parts[1].strip() if len(parts) > 1 else None
            else:
                section_path_str = section_content

            # Split nested path - use rsplit with maxsplit=1
            # "a.b" -> base_path=["a"], final="b"
            # "a.b.c" -> base_path=["a", "b"], final="c"
            path_parts = section_path_str.rsplit('.', 1)
            if len(path_parts) == 2:
                base_path = path_parts[0].split('.') if '.' in path_parts[0] else [path_parts[0]]
                final = path_parts[1]
            else:
                base_path = []
                final = path_parts[0]

            # Create or get the section dict at the full path
            section_dict = _get_or_create_nested(result, base_path + [final])

            # Handle inheritance
            if parent:
                if parent in section_dicts:
                    # Parent already defined - copy its values
                    for k, v in section_dicts[parent].items():
                        if k not in section_dict:
                            section_dict[k] = v
                else:
                    # Parent not yet defined - track for later
                    pending_inheritances.append((section_dict, parent))
            # else:
            #     # No inheritance needed

            # Track section by name for inheritance lookup
            section_name = final
            if base_path:
                section_name = '.'.join(base_path) + '.' + final
            section_dicts[section_name] = section_dict

            current_section = section_dict
            continue

        # Parse key-value pair
        if '=' in line:
            key_val = line.split('=', 1)
            key = key_val[0].strip()
            value = key_val[1].strip()

            # Auto-convert value
            converted = _convert_value(value)

            if current_section is not None:
                # We're in a section - add to current section
                current_section[key] = converted
            else:
                # Top-level key
                result[key] = converted

    # Resolve any remaining pending inheritances (forward references)
    for section_dict, parent in pending_inheritances:
        if parent in section_dicts:
            for k, v in section_dicts[parent].items():
                if k not in section_dict:
                    section_dict[k] = v

    return result


def _convert_value(value: str):
    """Convert string value to appropriate type."""
    # Boolean (case-insensitive)
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False

    # Null (case-insensitive)
    if value.lower() == 'null':
        return None

    # Integer (all digits, possibly leading minus)
    if value and (value.isdigit() or (value.startswith('-') and value[1:].isdigit())):
        return int(value)

    # Float (simple decimal number)
    try:
        if '.' in value:
            return float(value)
    except ValueError:
        pass

    return value


def _get_or_create_nested(d, path):
    """Get or create a nested dict following the path.

    Args:
        d: The root dict
        path: List of keys like ["a", "b"]

    Returns:
        The dict at the end of the path, creating intermediates as needed.
    """
    current = d
    for key in path:
        if key not in current:
            current[key] = {}
        current = current[key]
    return current


# Run tests
if __name__ == "__main__":
    # Test 1: Basic sections
    config1 = """
    # Database settings
    [database]
    host = localhost
    port = 5432
    debug = true

    [server]
    host = 0.0.0.0
    port = 8080
    """
    result = parse_config(config1)
    assert result == {
        "database": {"host": "localhost", "port": 5432, "debug": True},
        "server": {"host": "0.0.0.0", "port": 8080},
    }, f"Test 1 failed: {result}"
    print("Test 1 passed!")

    # Test 2: Global keys with type conversion
    config2 = """
    name = MyApp
    version = 2.5
    verbose = FALSE
    """
    result = parse_config(config2)
    assert result == {"name": "MyApp", "version": 2.5, "verbose": False}
    print("Test 2 passed!")

    # Test 3: Section inheritance
    config3 = """
    [defaults]
    timeout = 30
    retries = 3
    log = true

    [production : defaults]
    timeout = 60
    host = prod.example.com

    [staging : defaults]
    host = staging.example.com
    debug = true
    """
    result = parse_config(config3)
    expected = {
        "defaults": {"timeout": 30, "retries": 3, "log": True},
        "production": {"timeout": 60, "retries": 3, "log": True, "host": "prod.example.com"},
        "staging": {"timeout": 30, "retries": 3, "log": True, "host": "staging.example.com", "debug": True},
    }
    assert result == expected, f"Test 3 failed: {result}"
    print("Test 3 passed!")

    # Test 4: Nested sections
    config4 = """
    [a.b]
    x = 1

    [a.b.c]
    y = 2
    """
    result = parse_config(config4)
    assert result == {"a": {"b": {"x": 1, "c": {"y": 2}}}}, f"Test 4 failed: {result}"
    print("Test 4 passed!")

    # Test 5: Various value types
    config5 = """
    key = null
    empty =
    num = -42
    pi = 3.14
    """
    result = parse_config(config5)
    assert result == {"key": None, "empty": "", "num": -42, "pi": 3.14}
    print("Test 5 passed!")

    # Test 6: Duplicate key - last wins
    config6 = """
    [s]
    a = 1
    a = 2
    """
    result = parse_config(config6)
    assert result == {"s": {"a": 2}}, f"Test 6 failed: {result}"
    print("Test 6 passed!")

    # Test 7: Empty input
    assert parse_config("") == {}
    assert parse_config("   \n\n  # just comments\n") == {}
    print("Test 7 passed!")

    print("\nAll tests passed!")
