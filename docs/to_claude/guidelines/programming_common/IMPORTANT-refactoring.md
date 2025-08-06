<!-- ---
!-- Timestamp: 2025-06-01 00:00:28
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/programming_common/IMPORTANT-refactoring.md
!-- --- -->

## Refactoring Rules
- During development, do not change names of files, variables, functions, and so on
- Refactoring will be separately requested
- Work in `feature/refactoring`

## Renaming
- Use `./docs/to_claude/bin/rename.sh`

## Refactoring Workflows
1. Commit the current status with appropriate chunks and comments
2. If `feature/refactor` already exits, determine if the current refactoring is in the step or just it is obsolete, already merged branch. In the latter case, please delete the existing `feature/refactor` branch to work on clean environment.
3. If current branch is not `feature/refactor`, create and switch to a new branch called `feature/refactor`.
4. Please try the followings as long as they will improve simplicity, readability, maintainability, while keeping original functionalities.
   - Prioritize incremental refactoring, starting with smaller, manageable changes that can be tested in isolation."
   - Re-organize project structure, standardize names of directories, files, variables, functions, classes/ and so on, move obsolete files under `.old` directory (e.g., `/path/to/obsolete/file.ext` -> `/path/to/obsolete/.old/file.ext`).
5. After refactoring, ensure functionalities are not changed by running tests
6. Once these steps are successfully completed, `git merge` the `feature/refactor` branch into the original branch.

## Useful Tools
See `~/.claude/bin`

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->