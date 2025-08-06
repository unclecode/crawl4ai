<!-- ---
!-- Timestamp: 2025-05-21 02:22:31
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/IMPORTANT-guidelines-programming-Cleanup-Rules.md
!-- --- -->

# Cleanup Guidelines

Follow these guidelines when preparing the codebase for production. The goal is to achieve product-ready quality.

## Table of Contents
- [Setup Safety Mechanisms](#setup-safety-mechanisms)
- [Review Code Quality Standards](#review-code-quality-standards)
- [Inventory Project Structure](#inventory-project-structure)
- [Develop a Cleanup Plan](#develop-a-cleanup-plan)
- [Clean Project Directories](#clean-project-directories)
- [Handle File Removal Safely](#handle-file-removal-safely)
- [Standardize File Naming](#standardize-file-naming)
- [Complete the Process](#complete-the-process)
- [Examples](#examples)
  - [Branch Creation Examples](#branch-creation-examples)
  - [File Naming Examples](#file-naming-examples)
  - [Safe Removal Examples](#safe-removal-examples)

## Setup Safety Mechanisms
1. Create a feature branch: `feature/cleanup-YYYY-MMDD-HHmmss`
2. Create a checkpoint branch: `checkpoint/before-cleanup-YYYY-MMDD-HHmmss`
3. In the checkpoint branch, save ALL FILES (including uncommitted and hidden files)

## Review Code Quality Standards
1. Review Clean Code Rules: `./docs/to_claude/guidelines/IMPORTANT-guidelines-programming-Clean-Code-Rules.md`
2. Review Readable Code: `./docs/to_claude/guidelines/the-art-of-readable-code.pdf`

## Inventory Project Structure
1. Run `tree -a` to view all the files
2. Document the current state before cleanup

## Develop a Cleanup Plan
1. Prioritize tasks
2. Set clear acceptance criteria
3. Create a cleanup checklist

## Clean Project Directories
1. Source code: `./src`, `./scripts`
2. Documentation: `./docs/`
3. Examples: `./examples`
4. Project management: `./project_management`
5. Tests: `./tests`

## Handle File Removal Safely
1. Never use `rm` directly
2. Use `./docs/to_claude/bin/safe_rm.sh` to move obsolete files to `.old` directories
3. Reference `./docs/to_claude/guidelines/guidelines-command-rm.md`

## Standardize File Naming
1. Eliminate development patterns such as `-v01`, `-fix`, `-improved`, `-consolidated`, `-enhanced`
2. Use clean production names: `filename.ext`

## Complete the Process
1. Verify all tests pass
2. Merge `feature/cleanup-YYYY-MMDD-HHmmss` back to the original branch

## Examples

### Branch Creation Examples

| ❌ DO NOT | ✅ DO |
|-----------|------|
| ```bash
# Directly making changes on main/develop branch
git checkout develop
# Start editing files directly
``` | ```bash
# Create feature and checkpoint branches
git checkout develop
git checkout -b feature/cleanup-2025-0521-022230
git checkout -b checkpoint/before-cleanup-2025-0521-022230
# Make a complete backup
git add -A
git commit -m "Complete checkpoint before cleanup"
git checkout feature/cleanup-2025-0521-022230
``` |
| ```bash
# Using ambiguous branch names
git checkout -b cleanup
git checkout -b backup
``` | ```bash
# Using specific timestamped branch names
git checkout -b feature/cleanup-2025-0521-022230
git checkout -b checkpoint/before-cleanup-2025-0521-022230
``` |

### File Naming Examples

| ❌ DO NOT | ✅ DO |
|-----------|------|
| ```
utils-v01.py
utils-v02.py
utils-improved.py
utils-new.py
utils-final.py
utils-final-v2.py
``` | ```
utils.py
``` |
| ```
data_processor-initial.py
data_processor-with-fix.py
data_processor-optimized.py
data_processor-production.py
``` | ```
data_processor.py
``` |
| ```
# Multiple files with similar functionality
user_validator.py
validate_user.py
user_validation_improved.py
``` | ```
# Single consolidated file
user_validation.py
``` |

### Safe Removal Examples

| ❌ DO NOT | ✅ DO |
|-----------|------|
| ```bash
# Directly removing files
rm obsolete_script.py
rm -rf old_directory
``` | ```bash
# Using safe_rm.sh for removal
./docs/to_claude/bin/safe_rm.sh obsolete_script.py
./docs/to_claude/bin/safe_rm.sh old_directory
``` |
| ```bash
# Hard-deleting configuration files
rm config-old.json
rm config-backup.json
``` | ```bash
# Safely moving old config files
./docs/to_claude/bin/safe_rm.sh config-old.json
./docs/to_claude/bin/safe_rm.sh config-backup.json
# Creates:
# .old/config-old.json
# .old/config-backup.json
``` |
| ```bash
# Mass deletion without review
rm *.tmp
rm *-old.*
rm -rf __pycache__
``` | ```bash
# Review and use safe removal
find . -name "*.tmp" -type f > to_remove.txt
# Review to_remove.txt carefully
cat to_remove.txt | xargs -I{} ./docs/to_claude/bin/safe_rm.sh {}
``` |

<!-- EOF -->