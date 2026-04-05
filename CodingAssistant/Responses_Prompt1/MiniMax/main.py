def flatten_dict(d: dict, sep: str = ".") -> dict:
    """Flatten a nested dictionary by joining keys with `sep`.

    Recursively flattens nested dictionaries, joining parent and child keys
    with the specified separator. Non-dict values (ints, strings, lists, None, etc.)
    are kept as-is. Empty nested dicts are preserved with empty dict values.

    Args:
        d: The dictionary to flatten.
        sep: The separator to use for joining keys (default: ".").

    Returns:
        A flattened dictionary with joined keys.
    """
    result = {}

    for key, value in d.items():
        if isinstance(value, dict):
            # Recursively flatten the nested dict
            nested = flatten_dict(value, sep)
            for nested_key, nested_value in nested.items():
                result[key + sep + nested_key] = nested_value
            # Handle empty dict case: {"a": {}} should become {"a": {}}
            if not nested:
                result[key] = {}
        else:
            # Non-dict values are kept as-is
            result[key] = value

    return result


if __name__ == "__main__":
    # Run the tests
    assert flatten_dict({"a": 1, "b": 2}) == {"a": 1, "b": 2}
    assert flatten_dict({"a": {"b": 1, "c": 2}}) == {"a.b": 1, "a.c": 2}
    assert flatten_dict({"a": {"b": {"c": 3}}}) == {"a.b.c": 3}
    assert flatten_dict({"a": {"b": 1}, "c": 2}) == {"a.b": 1, "c": 2}
    assert flatten_dict({}) == {}
    assert flatten_dict({"a": {"b": {"c": {"d": 4}}}}, sep="/") == {"a/b/c/d": 4}
    assert flatten_dict({"a": [1, 2], "b": {"c": None}}) == {"a": [1, 2], "b.c": None}
    assert flatten_dict({"a": {}}) == {"a": {}}
    assert flatten_dict({"x": {"": 1}}) == {"x.": 1}
    assert flatten_dict({"a": {"b": 1, "c": {"d": 2, "e": 3}}, "f": 4}) == {"a.b": 1, "a.c.d": 2, "a.c.e": 3, "f": 4}

    print("All tests passed!")
