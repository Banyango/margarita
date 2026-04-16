_TYPE_MAP = {
    "str": "string",
    "string": "string",
    "int": "integer",
    "integer": "integer",
    "float": "number",
    "number": "number",
    "bool": "boolean",
    "boolean": "boolean",
    "list": "array",
    "array": "array",
    "dict": "object",
    "object": "object",
}


def map_type(t):
    """Map Python type names to JSON Schema types for tool parameters and return values."""
    if isinstance(t, type):
        t = t.__name__
    key = str(t).lower()
    return _TYPE_MAP.get(key, "string")
