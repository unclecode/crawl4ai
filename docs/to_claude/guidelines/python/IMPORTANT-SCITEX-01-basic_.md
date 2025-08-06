<!-- ---
!-- Timestamp: 2025-06-14 06:38:24
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/python/IMPORTANT-SCITEX-01-basic.md
!-- --- -->

# SCITEX Basic Guidelines

**!!! IMPORATANT !!!**
**ANY PYTHON SCRIPTS MUST BE WRITTEN IN THE SCITEX FORMAT EXPLAINED BELOW.**
THE EXCEPTIONS ARE:
    - Pacakges authored by others
    - Source (`./src` and `./tests`) of pip packages to reduce dependency
IN OTHER WORDS, IN ANY PYTHON PROJECT, SCITEX MUST BE USED AT LEAST IN:
- `./scripts`
- `./examples`

## Feature Request
When SCITEX does not work, create a bug-report under `~/proj/scitex_repo/project_management/bug-reports/bug-report-<title>.md`, just like creating an issue ticket on GitHub

## What is SCITEX?
- `scitex` is:
    - A Python utility package
    - Designed to standardize scientific analyses and applications
    - Maintained by the user and installed via editable mode.
    - Located in `~/proj/scitex_repo/src/scitex`
    - Remote repository: `git@github.com:ywatanabe1989:SciTeX-Code`
    - Installed via pip in development mode: `pip install -e ~/proj/scitex_repo`
- `scitex` MUST BE:
    - MAINTAINED AND UPDATED REGULARLY

## Bug Report
- Create a bug report when you encountered scitex-related problems
- The bug reprot should be written as a markdown file in the scitex local repository like on GitHub Issues
  `~/proj/scitex_repo/project_management/bug-report-<title>.md`
  - Follow the `./docs/to_claude/guidelines/guidelines-programming-Bug-Report-Rules.md`

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->