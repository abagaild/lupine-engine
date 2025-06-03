"""
json_utils.py

JSON utilities for handling custom objects like Vector2 in serialization.
"""

import json
from typing import Any


class LupineJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Lupine Engine objects like Vector2."""
    
    def default(self, obj: Any) -> Any:
        # Handle Vector2 objects
        if hasattr(obj, 'to_list') and callable(getattr(obj, 'to_list')):
            return obj.to_list()
        
        # Handle Vector2-like objects with x, y attributes
        if hasattr(obj, 'x') and hasattr(obj, 'y'):
            return [obj.x, obj.y]
        
        # Handle other custom objects that might have to_dict
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return obj.to_dict()
        
        # Handle sets
        if isinstance(obj, set):
            return list(obj)
        
        # Fall back to default behavior
        return super().default(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely serialize an object to JSON, handling Vector2 and other custom objects."""
    return json.dumps(obj, cls=LupineJSONEncoder, **kwargs)


def safe_json_dump(obj: Any, fp, **kwargs) -> None:
    """Safely serialize an object to a file, handling Vector2 and other custom objects."""
    return json.dump(obj, fp, cls=LupineJSONEncoder, **kwargs)


def convert_to_json_serializable(obj: Any) -> Any:
    """
    Recursively convert an object to be JSON serializable.
    This is useful for preparing data before serialization.
    """
    if obj is None:
        return None
    
    # Handle Vector2 objects
    if hasattr(obj, 'to_list') and callable(getattr(obj, 'to_list')):
        return obj.to_list()
    
    # Handle Vector2-like objects with x, y attributes
    if hasattr(obj, 'x') and hasattr(obj, 'y'):
        return [obj.x, obj.y]
    
    # Handle dictionaries
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    
    # Handle lists and tuples
    if isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    
    # Handle sets
    if isinstance(obj, set):
        return [convert_to_json_serializable(item) for item in obj]
    
    # Handle objects with to_dict method
    if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
        return convert_to_json_serializable(obj.to_dict())
    
    # Handle basic types
    if isinstance(obj, (str, int, float, bool)):
        return obj
    
    # For anything else, try to convert to string as fallback
    try:
        # Check if it's already JSON serializable
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        # Convert to string as last resort
        return str(obj)


def ensure_json_serializable(data: dict) -> dict:
    """
    Ensure all values in a dictionary are JSON serializable.
    This modifies the dictionary in place and also returns it.
    """
    for key, value in data.items():
        data[key] = convert_to_json_serializable(value)
    return data
