<!-- ---
!-- Timestamp: 2025-05-25 23:21:15
!-- Author: ywatanabe
!-- File: /ssh:sp:/home/ywatanabe/.claude/to_claude/guidelines/command/rm.md
!-- --- -->

# Safe File Removal Guidelines

## Policy
- ALWAYS KEEP REPOSITORY CLEAN
- For this, use `./docs/to_claude/bin/safe_rm.sh` to hide old/unrelated files with timestamp
- `rm` command is not allowed

## Table of Contents
- [Usage](#usage)
- [Examples](#examples)
- [Comparison of Approaches](#comparison-of-approaches)
- [Understanding Check](#your-understanding-check)

## Usage
`safe_rm.sh [-h|--help] file_or_directory [file_or_directory...]`

## Examples
- Remove a single file: `safe_rm.sh file1.txt`
- Remove a directory: `safe_rm.sh dir1`
- Remove multiple items: `safe_rm.sh file1.txt dir1 file2.py`
- Remove all text files: `safe_rm.sh *.txt`

## Comparison of Approaches

| ❌ DO NOT | ✅ DO |
|-----------|------|
| ```bash
# Permanently delete files
rm file.txt
``` | ```bash
# Safely move files to .old directory
./docs/to_claude/bin/safe_rm.sh file.txt
``` |
| ```bash
# Recursively remove directories
rm -rf directory/
``` | ```bash
# Safely preserve directory structure
./docs/to_claude/bin/safe_rm.sh directory/
``` |
| ```bash
# Mass deletion with glob patterns
rm *.bak
rm *_old*
``` | ```bash
# Safe removal with glob patterns
./docs/to_claude/bin/safe_rm.sh *.bak
./docs/to_claude/bin/safe_rm.sh *_old*
``` |
| ```bash
# Force deletion without confirmation
rm -f important_file.txt
``` | ```bash
# Files are preserved in .old directory
./docs/to_claude/bin/safe_rm.sh important_file.txt
# Can recover the file if needed
``` |

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/guidelines-command-rm.md`

<!-- EOF -->