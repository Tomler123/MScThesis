def parse_config(text: str) -> dict:
    def convert_value(val_str: str):
        val_lower = val_str.lower()
        if val_lower == 'true': return True
        if val_lower == 'false': return False
        if val_lower == 'null': return None
        
        # Check for integer (handles optional leading minus)
        if val_str.isdigit() or (val_str.startswith('-') and val_str[1:].isdigit()):
            return int(val_str)
            
        # Check for float (simple decimal check)
        if '.' in val_str:
            try:
                return float(val_str)
            except ValueError:
                pass
                
        return val_str

    # Intermediate storage
    flat_sections = {"": {}}
    inherit_map = {}
    current_section = ""

    # PASS 1: Parse lines into a flat structure of sections
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Handle Section Headers
        if line.startswith('[') and line.endswith(']'):
            header = line[1:-1].strip()
            if ':' in header:
                child, parent = header.split(':', 1)
                current_section = child.strip()
                inherit_map[current_section] = parent.strip()
            else:
                current_section = header
                
            if current_section not in flat_sections:
                flat_sections[current_section] = {}
                
        # Handle Key-Value pairs
        elif '=' in line:
            k, v = line.split('=', 1)
            flat_sections[current_section][k.strip()] = convert_value(v.strip())

    # PASS 2: Resolve inheritance 
    resolved_sections = {}
    
    def get_resolved(sec_name, seen):
        if sec_name in resolved_sections:
            return resolved_sections[sec_name]
        
        # Cycle detection
        if sec_name in seen:
            raise ValueError(f"Cyclic inheritance detected involving section: '{sec_name}'")
        
        seen.add(sec_name)
        
        # Get explicitly defined keys for this section
        base_kvs = flat_sections.get(sec_name, {}).copy()
        
        # If this section inherits from another, resolve the parent first
        if sec_name in inherit_map:
            parent_name = inherit_map[sec_name]
            parent_kvs = get_resolved(parent_name, seen)
            
            # Copy parent keys, then let the child's explicit keys override them
            merged = parent_kvs.copy()
            merged.update(base_kvs)
            base_kvs = merged
            
        resolved_sections[sec_name] = base_kvs
        seen.remove(sec_name)
        return base_kvs

    # Ensure all sections (even those only acting as parents) are resolved
    all_known_sections = set(flat_sections.keys()).union(inherit_map.keys())
    for sec in all_known_sections:
        if sec not in resolved_sections:
            get_resolved(sec, set())

    # PASS 3: Build the final nested dictionary tree
    result = {}
    
    # 1. Populate root elements
    if "" in resolved_sections:
        result.update(resolved_sections[""])
        
    # 2. Populate and nest named sections
    for sec, kvs in resolved_sections.items():
        if not sec:
            continue
            
        parts = sec.split('.')
        curr = result
        
        # Traverse and build nested dicts dynamically
        for i, p in enumerate(parts):
            # If the path doesn't exist, or a scalar value is blocking the path, create a dict
            if p not in curr or not isinstance(curr[p], dict):
                curr[p] = {}
                
            if i == len(parts) - 1:
                # Leaf node: apply all key-values
                curr[p].update(kvs)
            else:
                # Move deeper into the tree
                curr = curr[p]

    return result