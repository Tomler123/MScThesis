def parse_config(text: str) -> dict:
    """Parse a simple configuration language into a nested dictionary."""
    
    def convert_value(value: str):
        """Auto-convert string value to appropriate type."""
        value = value.strip()
        
        # Check for null
        if value.lower() == 'null':
            return None
        
        # Check for boolean
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        
        # Check for integer (optional leading minus, then digits only)
        if value.lstrip('-').isdigit() and value != '-':
            return int(value)
        
        # Check for float (simple decimal: optional minus, digits, dot, digits)
        if '.' in value:
            parts = value.split('.')
            if len(parts) == 2:
                left, right = parts
                # Left: empty, "-", or digits (with optional leading -)
                # Right: must be digits
                if (left == '' or left == '-' or left.lstrip('-').isdigit()) and right.isdigit():
                    return float(value)
        
        # Default to string
        return value
    
    def get_nested(d: dict, keys: list):
        """Get a nested dictionary, returns None if path doesn't exist."""
        for key in keys:
            if key not in d or not isinstance(d[key], dict):
                return None
            d = d[key]
        return d
    
    result = {}
    current_section_dict = result  # Points to where current keys should go
    
    for line in text.split('\n'):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Section header
        if line.startswith('[') and line.endswith(']'):
            section_content = line[1:-1].strip()
            
            # Parse section name and optional inheritance
            if ':' in section_content:
                section_name, parent_name = section_content.split(':', 1)
                section_name = section_name.strip()
                parent_name = parent_name.strip()
            else:
                section_name = section_content
                parent_name = None
            
            # Navigate/create nested dict structure for section
            section_keys = section_name.split('.')
            temp = result
            for key in section_keys:
                if key not in temp:
                    temp[key] = {}
                temp = temp[key]
            current_section_dict = temp
            
            # Handle inheritance: copy parent's keys, then own keys override
            if parent_name:
                parent_keys = parent_name.split('.')
                parent_dict = get_nested(result, parent_keys)
                if parent_dict is None:
                    raise ValueError(f"Parent section '{parent_name}' not found")
                current_section_dict.update(parent_dict)
            
            continue
        
        # Key-value pair
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            current_section_dict[key] = convert_value(value)
    
    return result