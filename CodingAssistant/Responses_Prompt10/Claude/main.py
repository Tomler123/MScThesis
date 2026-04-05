import re
import copy

def parse_config(text: str) -> dict:
    """Parse a simple configuration language into a nested dictionary."""

    def convert_value(raw: str):
        s = raw.strip()
        if s == "":
            return ""
        if s.lower() == "null":
            return None
        if s.lower() == "true":
            return True
        if s.lower() == "false":
            return False
        if re.fullmatch(r"-?\d+", s):
            return int(s)
        if re.fullmatch(r"-?\d+\.\d+", s):
            return float(s)
        return s

    def set_nested(d: dict, keys: list, value):
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value

    result = {}
    sections_flat = {}       # dotted section name → its dict in `result`
    current_section_keys = None
    current_flat = result

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Section header
        m = re.fullmatch(r"\[([^\]]+)\]", stripped)
        if m:
            header = m.group(1)
            parent_name = None
            if ":" in header:
                section_name, _, parent_name = header.partition(":")
                section_name = section_name.strip()
                parent_name = parent_name.strip()
            else:
                section_name = header.strip()

            current_section_keys = [k.strip() for k in section_name.split(".")]

            # Navigate/create nested dicts
            d = result
            for k in current_section_keys[:-1]:
                if k not in d or not isinstance(d[k], dict):
                    d[k] = {}
                d = d[k]

            last_key = current_section_keys[-1]
            if last_key not in d or not isinstance(d[last_key], dict):
                d[last_key] = {}

            if parent_name is not None:
                parent_flat = sections_flat.get(parent_name, {})
                d[last_key].update(copy.deepcopy(parent_flat))

            current_flat = d[last_key]
            sections_flat[section_name] = current_flat
            continue

        # Key-value pair
        if "=" in line:
            key, _, raw_val = line.partition("=")
            key = key.strip()
            value = convert_value(raw_val)
            current_flat[key] = value

    return result