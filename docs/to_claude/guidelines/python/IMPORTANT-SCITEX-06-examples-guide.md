<!-- ---
!-- Timestamp: 2025-06-01 03:18:02
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/python/IMPORTANT-SCITEX-06-examples-guide.md
!-- --- -->

# Example Guidelines

## MUST USE `SCITEX`
All example files MUST use `scitex` and follow the `scitex` framework
Understand all the `scitex` guidelines in this directory

## MUST HAVE CORRESPONDING OUTPUT DIRECTORY
- Output directory creation is handled by:
  - `scitex.gen.start`
  - `scitex.gen.close`
  - `scitex.io.save`
- If corresponding output directory is not created, that means:
  1. That script does not follow the `scitex` framework
  2. That script is not run yet
  3. The `scitex` package has problems
  You must investigate the root causes, share the information across agents, and fix problems

## MUST synchronize source directory structure
- `./examples` MUST mirror the structure of `./src` or `./scripts`
  `./src` for pip packages or 
  `./scripts` for scientific projects
- Update and Use `./examples/sync_examples_with_source.sh`
  - Options: `-m` (move stale files), `-c` (clear outputs), `-s` (source dir), `-e` (examples dir)

## Do not place files directory under `./examples`
Instead, prepare a sub directory `./examples/<descriptive-category>/xxx.ext`
Utility scripts like batch renaming, checking, and so on MUST be written under `./.playground` to keep `./examples` clean and tidy.

## MUST RUN AND PRODUCE EXPLANATORY RESULTS
- Implementing an example is not sufficient
- ALWAYS RUN IMPLEMENTED EXAMPLES AND PRODUCE EXPLANATORY RESULTS
  - Embrace figures for visual understanding
  - Logs created by the scitex framework is also valuable
- Examples can be run by:
  ```bash
  # Direct, one example
  ./examples/path/to/example_filename.py
  # Run all examples
  ./examples/run_examples.sh [DIRECTORY] [-c|--clear-outputs]
  ```
- `run_examples.sh` features:
  - Default directory: `./examples`
  - Optional output clearing with `-c` flag (default: preserve outputs)
  - Positional directory argument supported
  - IMPORTANT: Logs can be available: `./examples/.run_examples.sh.log`

## Start from small
1. Ensure each example works correctly one by one
   Before working on multiple example files, complete a specific example
   For example, if an issue found across multiple files, first, try to fix it on a file and run it to check the troubleshooting works.
2. Increment this step gradually until all examples are prepared correctly.


## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`
```

CLAUDE UNDERSTOOD: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/python/IMPORTANT-SCITEX-06-examples-guide.md

<!-- EOF -->