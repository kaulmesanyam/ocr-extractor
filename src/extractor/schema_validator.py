"""JSON schema validation for extracted policy data"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of schema validation"""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, missing_fields: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.missing_fields = missing_fields or []
    
    def __bool__(self):
        return self.is_valid


def _load_schema() -> Dict[str, Any]:
    """Load JSON schema from validator.json file"""
    schema_path = Path(__file__).parent.parent.parent / "validator.json"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return json.load(f)


def validate_extracted_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], ValidationResult]:
    """
    Validate extracted data against the JSON schema.
    
    Args:
        data: Dictionary containing extracted policy data
        
    Returns:
        Tuple of (validated data dict, ValidationResult)
    """
    errors = []
    missing_fields = []
    
    try:
        schema = _load_schema()
        
        # Validate against JSON schema
        validate(instance=data, schema=schema)
        
        # Check for missing required fields
        _check_missing_fields(data, schema, missing_fields)
        
        return data, ValidationResult(is_valid=True, missing_fields=missing_fields)
    
    except ValidationError as e:
        # Extract validation errors
        error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
        error_msg = f"{error_path}: {e.message}"
        errors.append(error_msg)
        logger.warning(f"Validation error: {error_msg}")
        
        # Also check for missing fields
        try:
            schema = _load_schema()
            _check_missing_fields(data, schema, missing_fields)
        except Exception:
            pass
        
        return data, ValidationResult(is_valid=False, errors=errors, missing_fields=missing_fields)
    
    except Exception as e:
        error_msg = f"Unexpected validation error: {str(e)}"
        errors.append(error_msg)
        logger.error(error_msg)
        return data, ValidationResult(is_valid=False, errors=errors)


def _check_missing_fields(data: Dict[str, Any], schema: Dict[str, Any], missing_fields: List[str], prefix: str = ""):
    """
    Recursively check for missing required fields based on the schema.
    
    Args:
        data: The data dictionary to check
        schema: The JSON schema
        missing_fields: List to append missing field paths to
        prefix: Current path prefix for nested fields
    """
    if "properties" not in schema:
        return
    
    required = schema.get("required", [])
    
    for prop_name, prop_schema in schema["properties"].items():
        current_path = f"{prefix}.{prop_name}" if prefix else prop_name
        
        # Check if required
        if prop_name in required:
            if prop_name not in data or data[prop_name] is None:
                missing_fields.append(current_path)
        
        # Recursively check nested objects
        if prop_name in data and isinstance(data[prop_name], dict):
            if "properties" in prop_schema:
                _check_missing_fields(data[prop_name], prop_schema, missing_fields, current_path)
            elif "type" in prop_schema and prop_schema["type"] == "object":
                # Handle nested objects that might have properties defined elsewhere
                if "properties" in prop_schema:
                    _check_missing_fields(data[prop_name], prop_schema, missing_fields, current_path)


def validate_and_format(data: Dict[str, Any]) -> Tuple[Dict[str, Any], ValidationResult]:
    """
    Validate data and return as dictionary with validation result.
    
    Args:
        data: Dictionary containing extracted policy data
        
    Returns:
        Tuple of (validated data dict, ValidationResult)
    """
    validated_data, validation_result = validate_extracted_data(data)
    return validated_data, validation_result
