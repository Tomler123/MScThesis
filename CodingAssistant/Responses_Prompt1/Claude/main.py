def flatten_dict(d: dict, sep: str = ".") -> dict:
    """Flatten a nested dictionary by joining keys with `sep`.

    Args:
        d: The (possibly nested) dictionary to flatten.
        sep: The separator used to join parent and child keys.

    Returns:
        A new flat dictionary with compound keys.
    """
    def _flatten(obj: dict, parent_key: str) -> dict:
        items: dict = {}
        for k, v in obj.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict) and v:  # non-empty dict → recurse
                items.update(_flatten(v, new_key))
            else:                           # leaf or empty dict → store as-is
                items[new_key] = v
        return items

    return _flatten(d, "")