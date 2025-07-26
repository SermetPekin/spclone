def parse_pyproject_manual(pyproject_path: Path) -> Dict[str, Any]:
    """
    Manual parsing of pyproject.toml for basic build-system section.
    
    Args:
        pyproject_path: Path to pyproject.toml file
        
    Returns:
        Dictionary with build system information
    """
    try:
        content = pyproject_path.read_text(encoding='utf-8')
        result = {}
        
        # Extract build-system section
        build_system_match = re.search(r'\[build-system\](.*?)(?=\n\[|\Z)', content, re.DOTALL)
        if build_system_match:
            build_system_content = build_system_match.group(1)
            
            # Extract requires - handle both single line and multi-line arrays
            requires_match = re.search(r'requires\s*=\s*\[(.*?)\]', build_system_content, re.DOTALL)
            if requires_match:
                requires_content = requires_match.group(1)
                requires = []
                
                # First try to split by commas, but be smart about it
                # Handle cases where commas might be inside quotes or conditions
                current_item = ""
                in_quotes = False
                quote_char = None
                bracket_depth = 0
                
                for char in requires_content:
                    if char in ['"', "'"] and not in_quotes:
                        in_quotes = True
                        quote_char = char
                        current_item += char
                    elif char == quote_char and in_quotes:
                        in_quotes = False
                        quote_char = None
                        current_item += char
                    elif char == '[' and not in_quotes:
                        bracket_depth += 1
                        current_item += char
                    elif char == ']' and not in_quotes:
                        bracket_depth -= 1
                        current_item += char
                    elif char == ',' and not in_quotes and bracket_depth == 0:
                        # This is a real separator
                        if current_item.strip():
                            requires.append(current_item.strip())
                        current_item = ""
                    else:
                        current_item += char
                
                # Don't forget the last item
                if current_item.strip():
                    requires.append(current_item.strip())
                
                # Now clean up each requirement
                cleaned_requires = []
                for req in requires:
                    # Skip empty requirements
                    if not req.strip():
                        continue
                    
                    # Process line by line if it contains newlines
                    for line in req.split('\n'):
                        line = line.strip()
                        
                        # Skip empty lines and comments
                        if not line or line.startswith('#'):
                            continue
                        
                        # Handle inline comments
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        
                        # Remove trailing comma
                        line = line.rstrip(',').strip()
                        
                        # Skip if empty after cleaning
                        if not line:
                            continue
                        
                        # Remove outer quotes
                        if (line.startswith('"') and line.endswith('"')) or \
                           (line.startswith("'") and line.endswith("'")):
                            line = line[1:-1]
                        
                        # Add to cleaned requirements if not empty
                        if line:
                            cleaned_requires.append(line)
                
                result['build-system'] = {'requires': cleaned_requires}
            
            # Extract build-backend
            backend_match = re.search(r'build-backend\s*=\s*["\']([^"\']+)["\']', build_system_content)
            if backend_match:
                if 'build-system' not in result:
                    result['build-system'] = {}
                result['build-system']['build-backend'] = backend_match.group(1)
        
        return result
    
    except Exception as e:
        print(f"Warning: Manual pyproject.toml parsing failed: {e}")
        return {}