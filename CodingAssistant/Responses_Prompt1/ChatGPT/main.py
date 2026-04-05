from typing import Any


def flatten_dict(d: dict[str, Any], sep: str = ".") -> dict[str, Any]:
    """Flatten a nested dictionary by joining nested keys with `sep`.

    Nested dictionaries are recursively expanded so that each leaf value is
    stored under a single key composed of its parent keys joined by `sep`.
    Non-dictionary values are kept unchanged. Empty nested dictionaries are
    preserved as leaf values.

    Args:
        d: The dictionary to flatten.
        sep: The separator used to join parent and child keys.

    Returns:
        A new flattened dictionary.
    """
    def _flatten(current: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        flat: dict[str, Any] = {}

        for key, value in current.items():
            new_key = f"{prefix}{sep}{key}" if prefix else key

            if isinstance(value, dict):
                if value:
                    flat.update(_flatten(value, new_key))
                else:
                    flat[new_key] = {}
            else:
                flat[new_key] = value

        return flat

    return _flatten(d)