<!-- ---
!-- Timestamp: 2025-05-30 08:20:22
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/elisp/IMPORTANT-ELISP-04-coding-style.md
!-- --- -->

# Elisp Coding Style Guidelines

## Naming Conventions

#### General Naming Rules
- Use kebab-case for filenames, function names, and variable names
- Use acronym as prefix for non-entry files (e.g., `ecc-*.el`)
- Do not use acronym for exposed functions, variables, and package name
- Use `--` prefix for internal functions and variables (e.g., `--ecc-internal-function`, `ecc-internal-variable`)
- Function naming: `<package-prefix>-<category>-<verb>-<noun>` pattern
- Include comprehensive docstrings

## Elisp Docstring Example

```elisp
(defun elmo-load-json-file (json-path)
  "Load JSON file at JSON-PATH by converting to markdown first.

Example:
  (elmo-load-json-file \"~/.emacs.d/elmo/prompts/example.json\")
  ;; => Returns markdown content from converted JSON"
  (let ((md-path (concat (file-name-sans-extension json-path) ".md")))
    (when (elmo-json-to-markdown json-path)
      (elmo-load-markdown-file md-path))))
```

## Elisp Commenting Rules
- Keep comments minimal but meaningful
- Use comments for section separation and clarification
- Avoid redundant comments that just restate code

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->