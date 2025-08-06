<!-- ---
!-- Timestamp: 2025-05-29 20:33:09
!-- Author: ywatanabe
!-- File: /ssh:ywatanabe@sp:/home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/python/SCITEX-05-scitex-testing-guide.md
!-- --- -->

## Testing Guidelines

- Use pytest (not unittest)
- Create small, focused test functions
- One test function per test file
- Define test classes in dedicated scripts

### Test File Structure

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-05-03 00:49:28 (ywatanabe)"
# File: ./tests/scitex/plt/test_function.py

import pytest
import numpy as np

def test_function():
    """Test specific functionality."""
    from scitex.module.path import function
    
    # Setup test data
    input_data = np.array([1, 2, 3])
    
    # Call function
    result = function(input_data)
    
    # Assert expected results
    assert isinstance(result, np.ndarray)
    assert result.shape == (3,)
    assert np.array_equal(result, np.array([2, 4, 6]))

if __name__ == "__main__":
    import os
    pytest.main([os.path.abspath(__file__)])
```

### Running Tests

Use the script in the project root:

```bash
./run_tests.sh
```
## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->