<!-- ---
!-- Timestamp: 2025-05-29 20:33:05
!-- Author: ywatanabe
!-- File: /ssh:ywatanabe@sp:/home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/python/SCITEX-04-scitex-coding-style.md
!-- --- -->

## Python Coding Style

## Path management
- ALL PATH MUST BE WRITTEN IN RELATIVE PATH
- ALL RELATIVE PATHS MUST START FROM DOT: (e.g., `./target`, `../target`, `../../target`)
- Relative from:
    - **For SAVING, starts from the script path instead of cwd**
    - **For other cases, starts from the current working directory**
- Scripts MUST BE RUNfrom project root
- Centralize path definitions in `./config/PATH.yaml`

For scitex package development:
- Use underscore prefix for imports (e.g., `import numpy as _np`)
- Use relative imports (e.g., `from ..io._load import load`)

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variable names | snake_case | `data_frame`, `patient_id` |
| Load paths | `lpath(s)` | `lpath = './data/input.csv'` |
| Save paths | `spath(s)` | `spath = './data/output.csv'` |
| Directory names | Noun form | `mnist-creation/`, `data-analysis/` |
| Script files | Verb first (for actions) | `classify_mnist.py`, `preprocess_data.py` |
| Class files | CapitalCase | `ClassName.py` |
| Constants | UPPERCASE | `MAX_ITERATIONS = 100` |

### Type Hints

```python
from typing import Union, Tuple, List, Dict, Any, Optional, Callable
from collections.abc import Iterable

# Define custom type aliases
ArrayLike = Union[List, Tuple, np.ndarray, pd.Series, pd.DataFrame, xr.DataArray, torch.Tensor]

def process_data(data: ArrayLike, factor: float = 1.0) -> np.ndarray:
    """Process the input data."""
    return np.array(data) * factor
```

### Docstring Format (NumPy Style)

```python
def func(arg1: int, arg2: str) -> bool:
    """Summary line.

    Extended description of function.

    Example
    ----------
    >>> xx, yy = 1, "test"
    >>> out = func(xx, yy)
    >>> print(out)
    True

    Parameters
    ----------
    arg1 : int
        Description of arg1
    arg2 : str
        Description of arg2

    Returns
    -------
    bool
        Description of return value
    """
    return True
```

For simple functions, one-line docstrings are acceptable:

```python
def add(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    return a + b
```

### Function Organization

Organize functions hierarchically:

```python
# 1. Main entry point
# ---------------------------------------- 
def main():
    """Main function that coordinates the workflow."""
    data = load_data()
    processed = process_data(data)
    save_results(processed)


# 2. Core functions
# ---------------------------------------- 
def load_data():
    """Load and prepare input data."""
    pass

def process_data(data):
    """Process the data."""
    pass

def save_results(results):
    """Save processing results."""
    pass


# 3. Helper functions
# ---------------------------------------- 
def validate_inputs(data):
    """Validate input data."""
    pass
```

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->