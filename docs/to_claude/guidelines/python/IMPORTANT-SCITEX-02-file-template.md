<!-- ---
!-- Timestamp: 2025-06-14 06:40:13
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/python/IMPORTANT-SCITEX-02-file-template.md
!-- --- -->

## Script Template

SCITEX PYTHON SCRIPT MUST STRICTLY FOLLOW THIS STANDARD FORMAT:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-05-31 07:15:35 (ywatanabe)"
# File: ./relative/path/from/project/script.py
# ----------------------------------------
import os
__FILE__ = (
    "./relative/path/from/project/script.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

"""
Functionalities:
  - Does XYZ
  - Does XYZ
  - Does XYZ
  - Saves XYZ

Dependencies:
  - scripts:
    - /path/to/script1
    - /path/to/script2
  - packages:
    - package1, package2, ...
Input:
  - /path/to/input/file.xxx
  - /path/to/input/file.xxx

Output:
  - /path/to/input/file.xxx
  - /path/to/input/file.xxx

(Remove me: Please fill docstrings above, while keeping the bulette point style, and remove this instruction line)
"""

"""Imports"""
import argparse
import scitex as stx

"""Warnings"""
# stx.pd.ignore_SettingWithCopyWarning()
# warnings.simplefilter("ignore", UserWarning)
# with warnings.catch_warnings():
#     warnings.simplefilter("ignore", UserWarning)

"""Parameters"""
# from stx.io import load_configs
# CONFIG = load_configs()

"""Functions & Classes"""
def main(args):
    return 0


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="")
    # parser.add_argument(
    #     "--var",
    #     "-v",
    #     type=int,
    #     choices=None,
    #     default=1,
    #     help="(default: %(default)s)",
    # )
    # parser.add_argument(
    #     "--flag",
    #     "-f",
    #     action="store_true",
    #     default=False,
    #     help="(default: %%(default)s)",
    # )
    args = parser.parse_args()
    stx.str.printc(args, c="yellow")
    return args


def run_main() -> None:
    """Initialize scitex framework, run main function, and cleanup."""
    global CONFIG, CC, sys, plt

    import sys
    import matplotlib.pyplot as plt

    args = parse_args()

    CONFIG, sys.stdout, sys.stderr, plt, CC = stx.gen.start(
        sys,
        plt,
        args=args,
        file=__FILE__,
        verbose=False,
        agg=True,
    )

    exit_status = main(args)

    stx.gen.close(
        CONFIG,
        verbose=False,
        notify=False,
        message="",
        exit_status=exit_status,
    )


if __name__ == "__main__":
    run_main()

# EOF
```

**⚠️ DO NOT MODIFY THE `run_main()` FUNCTION**  
This handles stdout/stderr direction, logging, configuration, and more

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->