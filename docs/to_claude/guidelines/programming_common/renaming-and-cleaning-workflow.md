<!-- ---
!-- Timestamp: 2025-05-25 16:15:00
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/guidelines-programming-Renaming-and-Cleaning-Workflow.md
!-- --- -->

# Renaming and Cleaning Workflow Guidelines

## Overview
Systematic approach for refactoring duplicate functions, aliases, and inconsistent naming across codebases.

## Pre-requisites
- Version control (git) with clean working directory
- Comprehensive test suite
- Backup strategy

## Phase 1: Discovery and Analysis

### 1.1 Identify Duplicates
```bash
# Find duplicate function definitions
grep -r "^(defun\|^def\|^function\|^const.*=.*function" --include="*.el" --include="*.py" --include="*.js" src/ | sort | uniq -d

# Find aliases (language-specific)
grep -r "defalias\|alias\|=.*function" --include="*.el" --include="*.py" --include="*.js" src/
```

### 1.2 Analyze Patterns
- Functions with similar names (e.g., `start` vs `enable`)
- Deprecated names still in use
- Inconsistent naming conventions
- Module-specific vs global naming

### 1.3 Create Analysis Script
```bash
#!/bin/bash
# analyze-duplicates.sh
# Extract and compare duplicate definitions
# Show references and usage patterns
# Generate recommendations
```

## Phase 2: Planning

### 2.1 Categorize Changes
1. **Naming standardization**: Align with project conventions
2. **Alias removal**: Replace short/unclear aliases with descriptive names
3. **Duplicate elimination**: Keep most appropriate implementation
4. **Module consolidation**: Move functions to proper modules

### 2.2 Create Replacement Map
```bash
# Format: old_name → new_name (reason)
REPLACEMENTS=(
    "short-name:descriptive-name:Use descriptive naming"
    "old-func:new-func:Standardize naming convention"
    "duplicate-1:canonical-name:Remove duplicate"
)
```

## Phase 3: Implementation

### 3.1 Automated Renaming Script
```bash
#!/bin/bash
# refactor-aliases.sh

# Configuration
DRY_RUN=true  # Always start with dry run
RENAME_SCRIPT="./path/to/replace_and_rename.sh"

# Function to perform systematic renaming
rename_function() {
    local old="$1"
    local new="$2"
    local reason="$3"
    
    echo "Renaming: $old → $new"
    echo "Reason: $reason"
    
    if [ "$DRY_RUN" = true ]; then
        "$RENAME_SCRIPT" "$old" "$new" .
    else
        "$RENAME_SCRIPT" -n "$old" "$new" .
    fi
}

# Process replacements in phases
# Phase 1: Standardize naming
# Phase 2: Remove aliases
# Phase 3: Consolidate modules
```

### 3.2 Replace and Rename Tool
Essential features:
- Replace in file contents
- Rename files/directories
- Preserve git history
- Handle regex patterns
- Dry run capability

## Phase 4: Cleanup

### 4.1 Remove Duplicates
```bash
#!/bin/bash
# remove-duplicates.sh

# Create backup
BACKUP_DIR=".backup-$(date +%Y%m%d-%H%M%S)"

# Remove duplicate definitions
# Remove obsolete aliases
# Update provide/require statements
```

### 4.2 Manual Review Required
- Duplicate function definitions (decide which to keep)
- Module boundaries and dependencies
- Public API changes
- Documentation updates

## Phase 5: Validation

### 5.1 Testing
```bash
# Run all tests
./run_tests.sh

# Check for undefined references
grep -r "undefined.*function" test-output.log

# Verify module loading
find . -name "*.el" -exec emacs --batch -l {} \;
```

### 5.2 Linting
```bash
# Language-specific linting
# Python: black, flake8, mypy
# JavaScript: eslint
# Elisp: byte-compile warnings
```

## Phase 6: Documentation

### 6.1 Update References
- README files
- API documentation
- Code comments
- Configuration examples

### 6.2 Migration Guide
For public APIs, provide:
- Deprecation notices
- Migration timeline
- Compatibility shims

## Best Practices

### DO:
1. **Always dry run first**
2. **Work in phases** - don't change everything at once
3. **Create backups** before destructive operations
4. **Test after each phase**
5. **Document breaking changes**
6. **Use version control** - commit after each successful phase

### DON'T:
1. **Don't mix refactoring with feature changes**
2. **Don't ignore test failures**
3. **Don't rush cleanup** - careful analysis prevents mistakes
4. **Don't forget transitive dependencies**
5. **Don't rename without understanding usage**

## Common Patterns

### Naming Conventions
```
# Short alias → Descriptive name
start → module-feature-enable
stop → module-feature-disable
toggle → module-feature-toggle

# Module prefixing
generic-name → module-specific-name
```

### State Functions
```
# Consolidate state detection
detect-simple-state → detect-state
detect-enhanced-state → detect-state
get-state-property → state-get-property
```

### Notification/Event Patterns
```
# Standardize event naming
auto-notify-* → notification-*
on-* → handle-*
```

## Recovery Procedures

### If Something Goes Wrong:
1. **Stop immediately**
2. **Check backup directory**
3. **Use git to review changes**: `git diff`
4. **Restore from backup if needed**
5. **Analyze what went wrong**
6. **Adjust scripts and retry**

## Tooling Requirements

### Essential Tools:
- `grep` / `ripgrep` for searching
- `sed` / `awk` for text processing
- `find` for file operations
- Version control (git)
- Language-specific parsers for AST-based refactoring

### Global Helper Scripts:
Located in `~/.claude/to_claude/bin/`:

1. **`replace_and_rename.sh`** - Core renaming tool
   - Replaces text in files and renames files/directories
   - Supports dry run mode
   - Usage: `replace_and_rename.sh [-n] <search> <replace> [directory]`

2. **`analyze-duplicates.sh`** - Discovery and analysis
   - Auto-detects language (elisp, python, js)
   - Finds duplicate function definitions
   - Identifies aliases and naming inconsistencies
   - Usage: `analyze-duplicates.sh [directory] [language]`

3. **`refactor-rename.sh`** - Orchestration script
   - Processes rename mappings in phases
   - Creates backups automatically
   - Supports dry run mode
   - Usage: `DRY_RUN=false refactor-rename.sh [directory] [mappings.txt]`

4. **`cleanup-duplicates.sh`** - Cleanup script
   - Removes duplicate functions and obsolete aliases
   - Works with cleanup plan file
   - Generates summary report
   - Usage: `DRY_RUN=false cleanup-duplicates.sh [directory] [cleanup-plan.txt]`

### Quick Start:
```bash
# 1. Analyze current state
~/.claude/to_claude/bin/analyze-duplicates.sh ./src elisp

# 2. Create rename mappings file
cat > rename-mappings.txt << EOF
old-func:new-func:Reason for change
another-old:another-new:Different reason
EOF

# 3. Perform renaming (dry run first)
~/.claude/to_claude/bin/refactor-rename.sh ./src rename-mappings.txt

# 4. Apply changes
DRY_RUN=false ~/.claude/to_claude/bin/refactor-rename.sh ./src rename-mappings.txt

# 5. Create cleanup plan
cat > cleanup-plan.txt << EOF
remove-function:src/module.el:duplicate-func:Keep version in main module
remove-alias:src/api.el:old-alias:Replaced with new name
EOF

# 6. Clean up duplicates
DRY_RUN=false ~/.claude/to_claude/bin/cleanup-duplicates.sh ./src cleanup-plan.txt
```

## Language-Specific Considerations

### Emacs Lisp:
- Check `defalias` statements
- Update `provide`/`require` forms
- Handle autoloads
- Consider byte-compilation

### Python:
- Update `__all__` exports
- Fix import statements
- Handle `@property` decorators
- Update type hints

### JavaScript:
- Update export/import statements
- Handle default exports
- Fix destructuring assignments
- Update TypeScript definitions

## Checklist

- [ ] Clean git working directory
- [ ] All tests passing
- [ ] Duplicates identified and analyzed
- [ ] Replacement map created and reviewed
- [ ] Dry run completed successfully
- [ ] Backups created
- [ ] Live run executed
- [ ] Duplicates removed
- [ ] Tests passing after refactor
- [ ] Documentation updated
- [ ] Changes committed with clear message
- [ ] Team notified of breaking changes

<!-- EOF -->