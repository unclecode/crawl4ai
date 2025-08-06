<!-- ---
!-- Timestamp: 2025-05-30 08:21:58
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/elisp/IMPORTANT-ELISP-02-project-structure.md
!-- --- -->

# Elisp Project Structure Guidelines

## Umbrella Structure
- Use umbrella structure with up to 1 depth
- Each umbrella must have at least:
  - Entry point: e.g., `./src/<package-prefix>-<umbrella>/<package-prefix>-<umbrella>.el`
  - A dedicated variable file under the scope of the umbrella: 
    - e.g., `./src/<package-prefix>-<umbrella>/<package-prefix>-<umbrella>-variables.el`
  - Variables and functions in an umbrella should be named as:
    - `<package-prefix>-<umbrella>-...`
- Entry script should add load-path to child directories
- Entry file should be `project-name.el`
- <project-name> is the same as the directory name of the repository root

## Directory Layout
1. Place entry point: `./<package-name>.el`
   This allows to `(require 'package-name)` outside of the pacakge as long as path is added.
2. Adopt umbrella design as follows:

```plaintext
./package-name/
├── package-name.el                 # Entry point, allows (require 'package-name)
│   # Contents:
│   # Add loadpath to umbrella entry points
│   # (require 'umbrella-xxx)
│   # (require 'umbrella-yyy)
│   # (provide 'package-name)
├── src
|   ├── umbrella-xxx/                   # First functional grouping
|   │   ├── umbrella-xxx.el             # Submodule integrator 
|   │   │   # Contents:
|   │   │   # (require 'umbrella-xxx-aab)
|   │   │   # (require 'umbrella-xxx-bbb) 
|   │   │   # (provide 'umbrella-xxx)
|   │   ├── umbrella-xxx-aab.el         # Component A functionality
|   │   └── umbrella-xxx-bbb.el         # Component B functionality
|   └── umbrella-yyy/                   # Second functional grouping
|       ├── umbrella-yyy.el             # Submodule integrator
|       │   # Contents:
|       │   # (require 'umbrella-yyy-ccc)
|       │   # (require 'umbrella-yyy-ddd)
|       │   # (provide 'umbrella-yyy)
|       ├── umbrella-yyy-ccc.el         # Component C functionality
|       └── umbrella-yyy-ddd.el         # Component D functionality
└── tests/                          # Test suite directory
    ├── test-package-name.el        # Tests for main package
    │   # Contents:
    │   # Loadability check
    ├── test-umbrella-xxx/          # Tests for xxx component
    │   ├── test-umbrella-xxx.el    # Tests for xxx integration
    │   │   # Loadability check
    │   ├── test-umbrella-xxx-aab.el # Tests for aab functionality
    │   │   # Contents:
    │   │   # (ert-deftest test-umbrella-xxx-aab-descriptive-test-name-1 ...)
    │   │   # (ert-deftest test-umbrella-xxx-aab-descriptive-test-name-2 ...)
    │   └── test-umbrella-xxx-bbb.el # Tests for bbb functionality
    │       # Contents:
    │       # (ert-deftest test-umbrella-xxx-bbb-descriptive-test-name-1 ...)
    │       # (ert-deftest test-umbrella-xxx-bbb-descriptive-test-name-2 ...)
    └── test-umbrella-yyy/          # Tests for yyy component
        ├── test-umbrella-yyy.el    # Tests for yyy integration
        │   # Contents:
        │   # Loadability check
        ├── test-umbrella-yyy-ccc.el # Tests for ccc functionality
        │   # (ert-deftest test-umbrella-yyy-ccc-descriptive-test-name-1 ...)
        │   # (ert-deftest test-umbrella-yyy-ccc-descriptive-test-name-2 ...)
        └──test-umbrella-yyy-ddd.el # Tests for ddd functionality
            # (ert-deftest test-umbrella-yyy-ddd-descriptive-test-name-1 ...)
            # (ert-deftest test-umbrella-yyy-ddd-descriptive-test-name-2 ...)
└.playground
```

**IMPORTANT**: 
- DO NOT CREATE DIRECTORIES IN PROJECT ROOT  
- Create child directories under predefined directories instead

## Temporal Working Space: `./.playground`
- For your temporally work, use `./.playground`
  - Organize playground with categoris: 
    `./.playground/category-name-1/...`
    `./.playground/category-name-2/...`

## Test Run Script
Use `./run_tests_elisp.sh` in the project root
- It creates detailed `LATEST-ELISP-REPORT.org` with metrics

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->