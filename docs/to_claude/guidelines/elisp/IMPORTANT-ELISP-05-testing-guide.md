<!-- ---
!-- Timestamp: 2025-05-30 08:20:45
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/elisp/IMPORTANT-ELISP-05-testing-guide.md
!-- --- -->

# Elisp Testing Guidelines

## Elisp Testing Rules

#### Test Structure and Location
- Test code should be located as `./tests/test-*.el` or `./tests/sub-directory/test-*.el`
- `./tests` directory should mirror the source code in their structures
- Source file and test file must be in one-on-one relationships
- Test files should be named as `test-*.el`

#### Test Code Execution Rules
- Test codes will be executed in runtime environment
  - Therefore, do not change variables for testing purposes
  - DO NOT SETQ/DEFVAR/DEFCUSTOM ANYTHING
  - DO NOT LET/LET* TEST VARIABLES
  - TEST FUNCTION SHOULD BE SMALLEST AND ATOMIC
    - EACH `ERT-DEFTEST` MUST INCLUDE ONLY ONE assertion statement such sa `should`, `should-not`, `should-error`.
      - Small `ERT-DEFTEST` with PROPER NAME makes testing much easier
  - !!! IMPORTANT !!! Test codes MUST BE MEANINGFUL 
    1. TO VERIFY FUNCTIONALITY OF THE CODE,
    2. GUARANTEE CODE QUALITIES, and
    3. RELIABILITY OF CODEBASE
  - WE ADOPT THE `TEST-DRIVE DEVELOPMENT (TDD)` STRATEGY
    - Thus, the quality of test code defines the quality of the project

#### Loadability Testing
Check loadability in THE ENTRY FILE OF THE ENTRY OF UMBRELLA DIRECTORY.
- Note that same name of `ert-deftest` is not acceptable so that loadability check should be centralized in umbrella entry file

``` elisp
;;; -*- coding: utf-8; lexical-binding: t -*-
;;; Author: ywatanabe
;;; Timestamp: <2025-02-10 20:39:59>
;;; File: /home/ywatanabe/proj/llemacs/llemacs.el/tests/01-01-core-base/test-lle-base.el
;;; Copyright (C) 2024-2025 Yusuke Watanabe (ywatanabe@alumni.u-tokyo.ac.jp)

(ert-deftest test-lle-base-loadable
    ()
  "Tests if lle-base is loadable."
  (require 'lle-base)
  (should
   (featurep 'lle-base)))

(ert-deftest test-lle-base-restart-loadable
    ()
  "Tests if lle-base-restart is loadable."
  (require 'lle-base-restart)
  (should
   (featurep 'lle-base-restart)))

(ert-deftest test-lle-base-utf-8-loadable
    ()
  "Tests if lle-base-utf-8 is loadable."
  (require 'lle-base-utf-8)
  (should
   (featurep 'lle-base-utf-8)))

...

(provide 'test-lle-base)
```

#### Test Writing Guidelines
- In each file, `ert-deftest` MUST BE MINIMAL, MEANING, and SELF-EXPLANATORY.
- Loadable tests should not be split across files but concentrate on central entry file (`./tests/test-<package-name>.el`); otherwise, duplicated error raised.
- Ensure the codes identical between before and after testing; implement cleanup process
- DO NOT ALLOW CHANGE DUE TO TEST
- When edition is required for testing, first store original information and revert in the cleanup stage

## Example of Elisp Test Files

#### Basic Function Testing
```elisp
;;; -*- coding: utf-8; lexical-binding: t -*-
;;; Author: ywatanabe
;;; Timestamp: <2025-05-10 17:02:51>
;;; File: /home/ywatanabe/proj/llemacs/llemacs.el/tests/01-01-core-base/test-lle-base-restart.el

;;; Copyright (C) 2025 Yusuke Watanabe (ywatanabe@alumni.u-tokyo.ac.jp)

(require 'ert)

;; Now skip loadable check as it is peformed in the dedicated entry file 
(require 'lle-base-restart) 

(ert-deftest test-lle-restart-is-function
    ()
  (should
   (functionp 'lle-restart)))

(ert-deftest test-lle-restart-is-interactive
    ()
  (should
   (commandp 'lle-restart)))

(ert-deftest test-lle-restart-filters-lle-features
    ()
  (let
      ((features-before features)
       (result nil))
    (cl-letf
        (((symbol-function 'load-file)
          (lambda
            (_)
            (setq result t)))
         ((symbol-function 'unload-feature)
          (lambda
            (_ _)
            t))
         ((symbol-function 'features)
          (lambda
            ()
            '(lle-test other-feature lle-another llemacs))))
      (lle-restart)
      (should result))
    (setq features features-before)))


(provide 'test-lle-base-restart)
```

#### Buffer Checking Tests
``` elisp
;;; -*- coding: utf-8; lexical-binding: t -*-
;;; Author: ywatanabe
;;; Timestamp: <2025-02-13 15:29:49>
;;; File: /home/ywatanabe/.dotfiles/.emacs.d/lisp/emacs-tab-manager/tests/test-etm-buffer-checkers.el

(require 'ert)
(require 'etm-buffer-checkers)

(ert-deftest test-etm-buffer-registered-p-with-name-only
    ()
  (let
      ((etm-registered-buffers
        '(("tab1" .
           (("home" . "buffer1"))))))
    (should
     (--etm-buffer-registered-p "buffer1"))))

(ert-deftest test-etm-buffer-registered-p-with-type
    ()
  (let
      ((etm-registered-buffers
        '(("tab1" .
           (("home" . "buffer1"))))))
    (should
     (--etm-buffer-registered-p "buffer1" "home"))
    (should-not
     (--etm-buffer-registered-p "buffer1" "results"))))

(ert-deftest test-etm-buffer-registered-p-with-tab
    ()
  (let
      ((etm-registered-buffers
        '(("tab1" .
           (("home" . "buffer1")))
          ("tab2" .
           (("home" . "buffer2"))))))
    (should
     (--etm-buffer-registered-p "buffer1" nil
                                '((name . "tab1"))))
    (should-not
     (--etm-buffer-registered-p "buffer1" nil
                                '((name . "tab2"))))))

(ert-deftest test-etm-buffer-protected-p
    ()
  (let
      ((etm-protected-buffers
        '("*scratch*" "*Messages*")))
    (should
     (--etm-buffer-protected-p "*scratch*"))
    (should-not
     (--etm-buffer-protected-p "regular-buffer"))))

(provide 'test-etm-buffer-checkers)
```

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->