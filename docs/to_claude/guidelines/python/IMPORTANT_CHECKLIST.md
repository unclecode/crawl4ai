<!-- ---
!-- Timestamp: 2025-06-01 03:30:44
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/python/IMPORTANT_CHECKLIST.md
!-- --- -->

# Checklist for project completion
  [ ] Are all matplotlib run in "Agg" mode and figures are saved instead of shown?
- [ ] Is the directory structure appropriate?
  - [ ] For scientific project:
    - [ ] `./scripts` instead of `./src`
  - [ ] For pip package:
    - [ ] `./src` instead of `./scripts`
    - [ ] `./pyproject.toml`
        - [ ] Does `uv pip install -e .` work?
    - [ ] `./MANIFEST.in`
  - [ ] Both types:
    - [ ] `./README.md`
    - [ ] `./CONTRIBUTING.md`
    - [ ] `./LICENSE`
    - [ ] `./docs`
    - [ ] `./examples`
      - [ ] Is the structure mirroring `./src`?
      - [ ] Are all example scripts strictly following the scitex framework?
      - [ ] Are all example scripts produces outputs and logs?
      - [ ] Are all example scripts successfully run?
      - [ ] Is there problems stem from external packages?
      - [ ] Used `./examples/run_examples.sh`
      - [ ] Used `./examples/sync_examples_with_source.sh`
      - [ ] Used `./run_examples.sh`
    - [ ] `./tests`
      - [ ] Is the structure mirroring `./src`?
      - [ ] Are all example scripts strictly following the scitex framework?
        - [ ] But to reduce dependency, non-scitex framework is acceptable for tests.
      - [ ] Are all example scripts produces outputs and logs?
      - [ ] Are all example scripts successfully run?
      - [ ] Is there problems stem from external packages?
      - [ ] Used `./examples/run_examples.sh`
      - [ ] Used `./examples/sync_examples_with_source.sh`
      - [ ] Used `./run_tests.sh`
    - [ ] `./project_management`
      - [ ] `./project_management/BULLETIN-BOARD.md`
        - [ ] Is obsolete information deleted?
      - [ ] `./project_management/bug-reports/{,solved}`
        - [ ] Are they updated?
      - [ ] `./project_management/feature-requests/{,solved}`
        - [ ] Are they updated?
    - [ ] pytest.ini
    - [ ] __init__.py

<!-- EOF -->