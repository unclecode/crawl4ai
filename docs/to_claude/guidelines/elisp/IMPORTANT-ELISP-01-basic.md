<!-- ---
!-- Timestamp: 2025-05-30 08:19:08
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/elisp/IMPORTANT-ELISP-01-basic.md
!-- --- -->

# Elisp Troubleshooting Guidelines

## Parentheses Mismatch
Use the following scripts for debugging:
  - `.claude/to_claude/bin/elisp_check_parens.sh`
  - `.claude/to_claude/bin/elisp-check-parens-lib.el`

## Require and Provide
- DO NEVER INCLUDE SLASH (`/`) in `require` and `provide` statements.
  The arguments to require and provide are called features. These are symbols, not file paths.
  When you want to use code from `./xxx/yyy.el`:
  In `./xxx/yyy.el`, use `(provide 'yyy)`. 
  The provided feature should EXACTLY MATCH THE FILENAME WITHOUT DIRECTORY OR EXTENSION.
  In other files, use `(require 'yyy)` to load it.
  If `./xxx` is not already in your `load-path`, add it:
  `(add-to-list 'load-path "./xxx")`
  Again, DO NOT USE `(require 'xxx/yyy)`—symbols with slashes will raise problems.
  ```elisp
  ;; ~/.emacs.d/lisp/xxx/yyy.el
  (provide 'yyy)
  
  ;; elsewhere
  (add-to-list 'load-path "~/.emacs.d/lisp/xxx")
  (require 'yyy)
  ```

## load-path
- Place the following block to the top of entry file
- This adds subdirectories recursively except for hidden files
- To add paths for source/test files, placing and calling this function in root will be useful.

```elisp
(defun --elisp-add-subdirs-to-loadpath-recursive (parent-dir)
  "Recursively add all visible subdirectories of PARENT-DIR to `load-path'.
Recursively adds all non-hidden subdirectories at all levels to the load path.
Hidden directories (starting with '.') are ignored.
Example:
(--elisp-add-subdirs-to-loadpath-recursive \"~/.emacs.d/lisp/\")"
  (let ((default-directory parent-dir))
    (add-to-list 'load-path parent-dir)
    (dolist (dir (directory-files parent-dir t))
      (when (and (file-directory-p dir)
                 (not (string-match-p "/\\.\\.?$" dir))
                 (not (string-match-p "/\\." dir)))
        (add-to-list 'load-path dir)
        (--elisp-add-subdirs-to-loadpath-recursive dir)))))

;; Usage: add ./src and ./tests directories to load-path
(let ((current-dir (file-name-directory (or load-file-name buffer-file-name))))
  (--elisp-add-subdirs-to-loadpath-recursive (concat current-dir "src"))
  (--elisp-add-subdirs-to-loadpath-recursive (concat current-dir "tests")))
```

## Your Understanding Check
========================================
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->