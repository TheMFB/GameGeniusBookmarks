#!/usr/bin/env python3
"""
Convert flat Redis JSON exports into hierarchical "friendly" JSON structure
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

IS_DEBUG = False


def set_nested_value(nested_dict: Dict[str, Any], key_parts: List[str], value: Any) -> None:
    """
    Set a value in a nested dictionary using a list of key parts

    Args:
        nested_dict: The dictionary to modify
        key_parts: List of key parts (e.g., ['game', 'marvel_rivals', 'folder'])
        value: The value to set
    """
    current = nested_dict

    # Navigate/create the nested structure
    for part in key_parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    # Set the final value
    current[key_parts[-1]] = value


def convert_redis_to_friendly(redis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert flat Redis key-value pairs to hierarchical structure

    Args:
        redis_data: Dictionary with Redis keys as flat strings

    Returns:
        Dictionary with hierarchical structure
    """
    friendly_data: Dict[str, Any] = {}

    for redis_key, value in redis_data.items():
        # Split the Redis key by colons
        key_parts = redis_key.split(':')

        # Handle single-level keys (no colons)
        if len(key_parts) == 1:
            friendly_data[redis_key] = value
        else:
            # Create nested structure
            set_nested_value(friendly_data, key_parts, value)

    return friendly_data


def convert_redis_state_file_to_friendly_and_save(input_file_path: str, output_file_path: Optional[str] = None) -> bool:
    """
    Convert a Redis JSON export file to friendly format

    Args:
        input_file_path: Path to the flat Redis JSON file
        output_file_path: Path for the friendly output file (optional)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read the flat Redis JSON
        with open(input_file_path, 'r') as f:
            redis_data = json.load(f)

        # Convert to friendly format
        friendly_data = convert_redis_to_friendly(redis_data)

        # Determine output path
        if output_file_path is None:
            input_path = Path(input_file_path)
            if input_path.stem.endswith('_before'):
                output_file_path = str(input_path.with_name('friendly_redis_before.json'))
            elif input_path.stem.endswith('_after'):
                output_file_path = str(input_path.with_name('friendly_redis_after.json'))
            else:
                output_file_path = str(input_path.with_name(f'friendly_{input_path.name}'))

        # Write the friendly JSON
        with open(output_file_path, 'w') as f:
            json.dump(friendly_data, f, indent=2)

        if IS_DEBUG:
            print(f"✅ Converted {input_file_path} → {output_file_path}")
        return True

    except FileNotFoundError:
        print(f"❌ File not found: {input_file_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {input_file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error converting {input_file_path}: {e}")
        return False


def main() -> int:
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python redis_friendly_converter.py <input_file> [output_file]")
        print("  input_file:  Path to flat Redis JSON export")
        print("  output_file: Optional path for friendly output (default: auto-generated)")
        print("")
        print("Examples:")
        print("  python redis_friendly_converter.py redis_before.json")
        print("  python redis_friendly_converter.py redis_before.json friendly_before.json")
        return 1

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if convert_redis_state_file_to_friendly_and_save(input_file, output_file):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())