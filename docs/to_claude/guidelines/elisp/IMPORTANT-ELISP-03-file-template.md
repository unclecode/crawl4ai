<!-- ---
!-- Timestamp: 2025-05-30 08:20:03
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/elisp/IMPORTANT-ELISP-03-file-template.md
!-- --- -->

# Elisp File Template Guidelines

## Elisp Header Rules

#### Required Header Format
DO INCLUDE headers like:
``` elisp
;;; -*- coding: utf-8; lexical-binding: t -*-
;;; Author: ywatanabe
;;; Timestamp: <2025-05-12 21:39:05>
;;; File: /home/ywatanabe/.emacs.d/lisp/sample-package/hw-utils/hw-utils.el

;;; Copyright (C) 2025 Yusuke Watanabe (ywatanabe@alumni.u-tokyo.ac.jp)
```

#### Headers We Do Not Use
On the other hand, we DO NOT FOLLOW THIS KINDS OF HEADERS THOUGH THEY ARE ELISP CONVENTIONS:
``` elisp
;;; hw-utils.el --- Utility functions for emacs-hello-world  -*- lexical-binding: t; -*-

;;; Commentary:
;; This file provides utility functions for the emacs-hello-world package.

;;; Code:
```

## Elisp Footer Rules

Do not remove this kind of footer. This is useful when evaluate the buffer to confirm no problem found in the file.
In general, they are handled by an automatic script by the `ehf-update-header-and-footer` function from `emacs-header-footer-manager package. So they will not have syntax errors.
``` elisp
(when
    (not load-file-name)
  (message "ecc-vterm-yank-as-file.el loaded."
           (file-name-nondirectory
            (or load-file-name buffer-file-name))))
```

## Elisp In-File Hierarchy and Sorting Rules

- Functions must be sorted considering their hierarchy.
- Upstream functions should be placed in upper positions
  - from top (upstream functions) to down (utility functions)
- Do not change any code contents during sorting
- Includes comments to show hierarchy

```elisp
;; 1. Main entry point
;; ---------------------------------------- 


;; 2. Core functions
;; ---------------------------------------- 


;; 3. Helper functions
;; ---------------------------------------- 
```

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->