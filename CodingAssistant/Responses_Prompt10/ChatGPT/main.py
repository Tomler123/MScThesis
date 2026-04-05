from __future__ import annotations

from copy import deepcopy
from typing import Any


def parse_config(text: str) -> dict:
    """Parse a simple configuration language into a nested dictionary.

    Supported features:
    - Comments: lines whose trimmed form starts with '#'
    - Blank lines
    - Key-value pairs: key = value
    - Sections: [section], nested sections: [parent.child]
    - Section inheritance: [child : parent]
    - Automatic value conversion for bool, null, int, and simple decimal float

    Notes:
    - Duplicate keys in the same section are overwritten by the last occurrence.
    - Repeated section headers continue updating the same section.
    - Inheritance supports forward references and detects cycles.
    """
    root_values: dict[str, Any] = {}
    sections: dict[tuple[str, ...], dict[str, Any]] = {}
    inherits: dict[tuple[str, ...], tuple[str, ...] | None] = {}

    current_section: tuple[str, ...] | None = None

    def parse_value(raw: str) -> Any:
        value = raw.strip()
        lower = value.lower()

        if lower == "true":
            return True
        if lower == "false":
            return False
        if lower == "null":
            return None

        if _is_int(value):
            return int(value)

        if _is_simple_float(value):
            return float(value)

        return value

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            inner = line[1:-1].strip()
            if not inner:
                raise ValueError(f"Empty section name on line {lineno}")

            if ":" in inner:
                left, right = inner.split(":", 1)
                section_name = left.strip()
                parent_name = right.strip()
                if not section_name or not parent_name:
                    raise ValueError(f"Invalid inheritance syntax on line {lineno}")
            else:
                section_name = inner
                parent_name = None

            section_path = _parse_section_path(section_name, lineno)
            parent_path = (
                _parse_section_path(parent_name, lineno) if parent_name is not None else None
            )

            sections.setdefault(section_path, {})
            if section_path in inherits:
                if inherits[section_path] != parent_path:
                    raise ValueError(
                        f"Conflicting inheritance for section "
                        f"'{'.'.join(section_path)}' on line {lineno}"
                    )
            else:
                inherits[section_path] = parent_path

            current_section = section_path
            continue

        if "=" not in line:
            raise ValueError(f"Invalid line {lineno}: {raw_line!r}")

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Empty key on line {lineno}")

        parsed_value = parse_value(value)

        if current_section is None:
            root_values[key] = parsed_value
        else:
            sections.setdefault(current_section, {})
            inherits.setdefault(current_section, None)
            sections[current_section][key] = parsed_value

    resolved_cache: dict[tuple[str, ...], dict[str, Any]] = {}
    resolving: set[tuple[str, ...]] = set()

    def resolve_section(path: tuple[str, ...]) -> dict[str, Any]:
        if path in resolved_cache:
            return deepcopy(resolved_cache[path])

        if path in resolving:
            raise ValueError(f"Cyclic inheritance detected for section '{'.'.join(path)}'")

        if path not in sections:
            raise ValueError(f"Undefined section referenced in inheritance: '{'.'.join(path)}'")

        resolving.add(path)

        base: dict[str, Any] = {}
        parent = inherits.get(path)
        if parent is not None:
            base = resolve_section(parent)

        base.update(sections[path])

        resolving.remove(path)
        resolved_cache[path] = deepcopy(base)
        return deepcopy(base)

    result: dict[str, Any] = dict(root_values)

    for path in sections:
        resolved = resolve_section(path)
        _assign_nested_section(result, path, resolved)

    return result


def _is_int(value: str) -> bool:
    """Return True if value is an integer like '42' or '-42'."""
    if not value:
        return False
    if value[0] == "-":
        return len(value) > 1 and value[1:].isdigit()
    return value.isdigit()


def _is_simple_float(value: str) -> bool:
    """Return True for simple decimal floats like '3.14' or '-0.5'."""
    if not value:
        return False

    if value[0] == "-":
        value = value[1:]
        if not value:
            return False

    if value.count(".") != 1:
        return False

    left, right = value.split(".", 1)
    return bool(left) and bool(right) and left.isdigit() and right.isdigit()


def _parse_section_path(name: str, lineno: int) -> tuple[str, ...]:
    """Parse a dotted section name into a tuple path."""
    parts = [part.strip() for part in name.split(".")]
    if not parts or any(part == "" for part in parts):
        raise ValueError(f"Invalid section name on line {lineno}: {name!r}")
    return tuple(parts)


def _assign_nested_section(result: dict[str, Any], path: tuple[str, ...], values: dict[str, Any]) -> None:
    """Insert section values into the final nested result dictionary."""
    node = result
    for part in path[:-1]:
        existing = node.get(part)
        if existing is None:
            node[part] = {}
            existing = node[part]
        elif not isinstance(existing, dict):
            # A scalar at an intermediate path is replaced so nested sections can exist.
            node[part] = {}
            existing = node[part]
        node = existing

    leaf = path[-1]
    existing_leaf = node.get(leaf)
    if isinstance(existing_leaf, dict):
        existing_leaf.update(values)
    else:
        node[leaf] = values