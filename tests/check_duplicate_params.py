#!/usr/bin/env python3
"""
Function to find duplicate entries at the same level/scope in a YAML file.
This version catches duplicates during parsing before they are overwritten.
"""

import yaml
import re
import argparse
from collections import defaultdict


def find_yaml_duplicates_raw(yaml_file_path):
    """
    Find duplicate keys by parsing the raw YAML text line by line.
    
    Parameters
    ----------
    yaml_file_path : str
        Path to the YAML file to check
        
    Returns
    -------
    dict
        Dictionary with scope/path as key and duplicate info as value
    """
    
    def get_indentation_level(line):
        """Get the indentation level of a line."""
        return len(line) - len(line.lstrip())
    
    def extract_key_from_line(line):
        """Extract YAML key from a line."""
        stripped = line.strip()
        if ':' in stripped and not stripped.startswith('#'):
            # Handle different YAML key formats
            key_part = stripped.split(':')[0].strip()
            # Remove quotes if present
            key_part = key_part.strip('"\'')
            return key_part
        return None
    
    def is_multiline_string_start(line):
        """Check if this line starts a multiline string (| or >)."""
        stripped = line.strip()
        return ':' in stripped and (stripped.endswith('|') or stripped.endswith('>'))
    
    try:
        with open(yaml_file_path, 'r') as file:
            lines = file.readlines()
        
        # Track keys at each indentation level
        keys_by_level = defaultdict(lambda: defaultdict(list))  # {scope: {key: [line_numbers]}}
        scope_stack = []  # Track nested scope path
        
        # State tracking for multiline strings
        in_multiline_string = False
        multiline_string_indent = 0
        
        for line_num, line in enumerate(lines, 1):
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                continue
            
            indent = get_indentation_level(line)
            
            # Check if we're currently in a multiline string
            if in_multiline_string:
                # We're in a multiline string if the current line is indented more than the string start
                # OR if it's at the same level but doesn't contain a colon (continuation of string)
                if indent > multiline_string_indent:
                    # Still inside multiline string, skip this line
                    continue
                elif indent <= multiline_string_indent:
                    # Check if this line starts a new key at same or higher level
                    key = extract_key_from_line(line)
                    if key is not None:
                        # This is a new key, multiline string has ended
                        in_multiline_string = False
                    else:
                        # This might be a continuation line, skip it
                        continue
            
            # If we reach here, we're not in a multiline string (or just exited one)
            key = extract_key_from_line(line)
            
            if key is None:
                continue
            
            # Check if this line starts a multiline string
            if is_multiline_string_start(line):
                in_multiline_string = True
                multiline_string_indent = indent
            
            # Update scope stack based on indentation
            # Remove scopes that are at same or deeper level
            while scope_stack and scope_stack[-1][1] >= indent:
                scope_stack.pop()
            
            # Add current key to scope
            current_scope = '.'.join([item[0] for item in scope_stack])
            
            # Track this key at current scope
            keys_by_level[current_scope][key].append(line_num)
            
            # Add to scope stack for nested items (only if not a multiline string value)
            if not is_multiline_string_start(line):
                scope_stack.append((key, indent))
        
        # Find duplicates
        duplicates = {}
        for scope, keys_dict in keys_by_level.items():
            scope_duplicates = {}
            for key, line_numbers in keys_dict.items():
                if len(line_numbers) > 1:
                    scope_duplicates[key] = line_numbers
            
            if scope_duplicates:
                scope_name = scope if scope else "root"
                duplicates[scope_name] = scope_duplicates
        
        return duplicates
        
    except FileNotFoundError:
        print(f"Error: File '{yaml_file_path}' not found.")
        return {}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}


def print_duplicates_detailed(duplicates, yaml_file_path=None, show_lines=True):
    """
    Pretty print the duplicates found with line numbers.
    
    Parameters
    ----------
    duplicates : dict
        Dictionary returned by find_yaml_duplicates_raw()
    yaml_file_path : str, optional
        Path to YAML file to show actual lines
    show_lines : bool
        Whether to show actual line content
    """
    if not duplicates:
        print("No duplicate keys found at any level.")
        return
    
    # Read file content if path provided and lines should be shown
    file_lines = []
    if yaml_file_path and show_lines:
        try:
            with open(yaml_file_path, 'r') as f:
                file_lines = f.readlines()
        except:
            pass
    
    print("Duplicate keys found:")
    print("=" * 60)
    
    for scope, scope_duplicates in duplicates.items():
        print(f"Scope: {scope}")
        print("-" * 40)
        
        for key, line_numbers in scope_duplicates.items():
            print(f"  Duplicate key: '{key}'")
            print(f"  Found on lines: {', '.join(map(str, line_numbers))}")
            
            # Show actual lines if file content available and requested
            if file_lines and show_lines:
                for line_num in line_numbers:
                    if 1 <= line_num <= len(file_lines):
                        line_content = file_lines[line_num - 1].rstrip()
                        print(f"    Line {line_num}: {line_content}")
            print()
        
        print()


def main():
    """Main function with argparse CLI."""
    parser = argparse.ArgumentParser(
        description='Find duplicate keys at the same scope/level in YAML files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s MOM_input.yaml                    # Check MOM_input.yaml
  %(prog)s -f input.yaml                     # Check input.yaml
  %(prog)s --no-lines MOM_input.yaml         # Don't show line content
  %(prog)s --quiet MOM_input.yaml            # Only show summary
        """
    )
    
    parser.add_argument(
        'file',
        nargs='?',
        default='MOM_input.yaml',
        help='YAML file to check for duplicates (default: MOM_input.yaml)'
    )
    
    parser.add_argument(
        '-f', '--file',
        dest='yaml_file',
        help='YAML file to check (alternative to positional argument)'
    )
    
    parser.add_argument(
        '--no-lines',
        action='store_true',
        help='Do not show actual line content, only line numbers'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Only show summary count of duplicates found'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.1'
    )
    
    args = parser.parse_args()
    
    # Determine which file to use
    yaml_file = args.yaml_file if args.yaml_file else args.file
    
    if not args.quiet:
        print(f"Checking for duplicates in: {yaml_file}")
        print()
    
    duplicates = find_yaml_duplicates_raw(yaml_file)
    
    if args.quiet:
        # Just show summary
        total_duplicates = sum(len(scope_dups) for scope_dups in duplicates.values())
        if total_duplicates > 0:
            print(f"Found {total_duplicates} duplicate keys in {len(duplicates)} scopes")
            return 1  # Exit code 1 indicates duplicates found
        else:
            print("No duplicates found")
            return 0
    else:
        # Show detailed output
        show_lines = not args.no_lines
        print_duplicates_detailed(duplicates, yaml_file, show_lines)
        
        # Return appropriate exit code
        return 1 if duplicates else 0


if __name__ == "__main__":
    exit(main())
