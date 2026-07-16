---
description: "Test current changes with adversarial tests, then run full regression suite"
arguments:
  - name: changes
    description: "Description of what changed (e.g. 'fixed URL normalization to preserve trailing slashes')"
    required: true
---

# Crawl4AI Change Verification (c4ai-check)

You are verifying that recent code changes work correctly AND haven't broken anything else. This is a two-phase process.

**Input:** $ARGUMENTS

## PHASE 1: Adversarial Testing of Current Changes

Based on the change description above:

1. **Understand the change**: Read the relevant files that were modified. Use `git diff` to see exactly what changed.

2. **Write targeted adversarial tests**: Create a temporary test file at `tests/regression/test_tmp_changes.py` that HEAVILY tests the specific changes:
   - Normal cases (does it work as intended?)
   - Edge cases (boundary values, empty inputs, None, huge inputs)
   - Regression cases (does the OLD bug still occur? it shouldn't)
   - Interaction cases (does it break anything it touches?)
   - Adversarial cases (weird inputs that could expose issues)
   - At least 10-15 focused tests per change area

   Rules for the temp test file:
   - Use `@pytest.mark.asyncio` for async tests
   - Use real browser crawling where needed (`async with AsyncWebCrawler()`)
   - Use the `local_server` fixture from conftest.py when needed
   - NO mocking - test real behavior
   - Each test must have a clear docstring explaining what it verifies

3. **Run the targeted tests**:
   ```bash
   .venv/bin/python -m pytest tests/regression/test_tmp_changes.py -v --tb=short
   ```

4. **Report results**: Show pass/fail summary. If any fail, investigate and determine if it's a real bug in the changes or a test issue. Fix the tests if needed, fix the code if there's a real bug.

## PHASE 2: Full Regression Suite

After Phase 1 passes:

1. **Run the full regression suite** (skip network tests for speed):
   ```bash
   .venv/bin/python -m pytest tests/regression/ -v -m "not network" --tb=short -q
   ```

2. **Analyze failures**: For any failures:
   - Determine if the failure is caused by the current changes (REGRESSION) or pre-existing
   - Regressions are blockers - report them clearly
   - Pre-existing failures should be noted but don't block

3. **Clean up**: Delete the temporary test file:
   ```bash
   rm tests/regression/test_tmp_changes.py
   ```

## PHASE 3: Report

Present a clear summary:

```
## c4ai-check Results

**Changes tested:** [brief description]

### Phase 1: Targeted Tests
- Tests written: X
- Passed: X / Failed: X
- [List any issues found]

### Phase 2: Regression Suite
- Total: X passed, X failed, X skipped
- Regressions caused by changes: [None / list]
- Pre-existing issues: [None / list]

### Verdict: PASS / FAIL
[If FAIL, explain what needs fixing]
```

IMPORTANT:
- Always delete `test_tmp_changes.py` when done, even if tests fail
- A PASS verdict means: all targeted tests pass AND no new regressions in the suite
- A FAIL verdict means: either targeted tests found bugs OR changes caused regressions
- Be honest about failures - don't hide issues
