---
name: python-type-check
description: Guide for fixing Python strict type checking errors (Pylance/MyPy). Use this skill when resolving unknown type, missing import, or type mismatch errors in Python files. Covers common patterns for TypedDict, generics, casting, and protocol alignment.
---

# Python Type Check Skill

This skill helps you resolve strict type checking errors in Python codebases, specifically targeting Pylance (VS Code's Python language server) and MyPy strict mode requirements.

## When to Use This Skill

Use this skill when you encounter:
- "Unknown type" or "Partially unknown type" errors
- "Missing import" or "Module not found" errors
- "Type mismatch" or "Incompatible type" assignments
- Strict type checking failures in `server.py`, `protocol.py`, or utility modules
- Need to refactor untyped dictionaries into `TypedDict` or `Pydantic` models

## General Workflow

1.  **Identify Errors**: Use `get_errors` on the target file(s) to list all type issues.
2.  **Analyze Dependencies**: Check if missing types are due to uninstalled packages or missing imports.
3.  **Apply Fixes**:
    *   **Imports**: Add missing `import` statements or install packages.
    *   **Return Types**: Add return type annotations (e.g., `-> None`, `-> Dict[str, Any]`).
    *   **Variable Types**: Annotate variables explicitly (e.g., `x: int = 1`).
    *   **Generics**: Replace raw `list` or `dict` with `List[type]` or `Dict[key_type, val_type]`.
    *   **Complex Dicts**: Convert widely used dict structures to `TypedDict` or `Pydantic` models.
    *   **Casting**: Use `typing.cast` for unavoidably dynamic data (like JSON).
4.  **Verify**: Run `get_errors` again to confirm the fixes worked.

## Common Fix Patterns

### 1. Handling "Unknown Type" / "Partially Unknown"

**Problem**: Pylance infers a type as `Unknown` because the source is dynamic (e.g., JSON, external library without stubs).
**Fix**: Explicitly annotate the variable or cast it.

```python
from typing import Any, Dict, cast

# Bad
data = json.load(f)
name = data["name"] # Pylance: data is Unknown

# Good (Annotation)
data: Dict[str, Any] = json.load(f)
name = data.get("name")

# Good (Casting for specific structures)
data = cast(Dict[str, Any], json.load(f))
```

### 2. Fixing Generic Types

**Problem**: Using raw container types like `list` or `dict` causes "Expected type arguments" errors.
**Fix**: Use standard typing generics (or built-in generics in Python 3.9+).

```python
from typing import Dict, List, Any

# Bad
def process_items(items: list) -> dict: ...

# Good
def process_items(items: List[str]) -> Dict[str, Any]: ...
```

### 3. Untyped Dictionaries -> TypedDict

**Problem**: Passing dictionaries with specific keys around without validation causes "Potential key error" or "Unknown type" access.
**Fix**: Define a `TypedDict`.

```python
from typing import TypedDict, List

# Bad
res = {"valid_ids": set(), "map": {}}

# Good
class CategoryData(TypedDict):
    valid_ids: set[str]
    map: dict[str, List[str]]

res: CategoryData = {
    "valid_ids": set(),
    "map": {}
}
```

### 4. Pydantic Models (Preferred for Protocol)

For data structures shared across the application (especially API contracts), prefer `Pydantic` models over `TypedDict`.

```python
from pydantic import BaseModel

class Item(BaseModel):
    id: str
    quantity: int = 1
```

### 5. Handling `Optional` and `None` checks

**Problem**: "Item 'None' has no attribute 'x'"
**Fix**: Explicitly check for None before access.

```python
from typing import Optional

def get_name(item: Optional[Item]) -> str:
    # return item.name  # Error: item could be None
    if item is None:
        return "Unknown"
    return item.name
```

## Project Specific Guidelines (BackroomAgent)

-   **`PROTOCOL.md` Alignment**: Ensure type definitions in `protocol.py` match `PROTOCOL.md`.
-   **LangGraph State**: `State` objects in `graph.py` files should match the structure defined in `state.py`.
-   **Imports**: Use `from typing import ...` for compatibility (even if Python 3.12+ supports `list[]`, some older tools might prefer `List[]`).
-   **Dependency Management**: If an import fails, check `requirements.txt` and install the package using `install_python_packages`.

## Troubleshooting

-   **"Module not found"**: Did you configure the python environment? Did you install the package?
-   **"Result is not a Pydantic model"**: Ensure you are calling `.model_dump()` or `.dict()` when necessary, or passing the correct object type.
-   **Persistent Errors**: Sometimes Pylance caches errors. Try making a small edit or reopening the file (conceptually) by re-running the tool.
