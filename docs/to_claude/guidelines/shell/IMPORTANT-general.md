<!-- ---
!-- Timestamp: 2025-05-17 07:14:15
!-- Author: ywatanabe
!-- File: /ssh:ywatanabe@sp:/home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/guidelines_programming_shell_scripting_rules.md
!-- --- -->

# Shell-specific Rules
================================================================================
## Shell Script General Rules

- Include one-line explanation for function, followed by example usage
- Ensure if-fi syntaxes are correct
- Include `argument parser` and `usage` function with `-h|--help` option
- Include logging functionality

## Shell Script Template
```bash
#!/bin/bash
# script-name.sh
# Author: ywatanabe (ywatanabe@alumni.u-tokyo.ac.jp)
# Date: $(date +"%Y-%m-%d-%H-%M")

LOG_FILE=".$0.log" # Hided and intensional extension of .sh.log

usage() {
    echo "Usage: $0 [-s|--subject <subject>] [-m|--message <message>] [-h|--help]"
    echo
    echo "Options:"
    echo "  -s, --subject   Subject of the notification (default: 'Subject')"
    echo "  -m, --message   Message body of the notification (default: 'Message')"
    echo "  -h, --help      Display this help message"
    echo
    echo "Example:"
    echo "  $0 -s \"About the Project A\" -m \"Hi, ...\""
    echo "  $0 -s \"Notification\" -m \"This is a notification from ...\""
    exit 1
}

my-echo() {
  while [[ $# -gt 0 ]]; do
      case $1 in
          -s|--subject)
              subject="$1"
              shift 1
              ;;
          -m|--message)
              shift
              message="$1"
              shift
              ;;
          -h|--help)
              usage
              ;;
          *)
              echo "Unknown option: $1"
              usage
              ;;
      esac
  done

  echo "${subject:-Subject}: ${message:-Message} (Yusuke Watanabe)"
}

main() {
    my-echo "$@"
}

main "$@" 2>&1 | tee "$LOG_FILE"

notify -s "$0 finished" -m "$0 finished"

# EOF
```

## Shell Script Template - run_all.sh
```bash
#!/bin/bash
# Timestamp: "2025-01-18 06:47:46 (ywatanabe)"
# File: ./scripts/<timestamp>-<title>/run_all.sh

LOG_FILE="$0%.log"

usage() {
    echo "Usage: $0 [-h|--help]"
    echo
    echo "Options:"
    echo " -h, --help   Display this help message"
    echo
    echo "Example:"
    echo " $0"
    exit 1
}

main() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help) usage ;;
              -) echo "Unknown option: $1"; usage ;;
        esac
    done
    
    commands=(
        "./scripts/<timestamp>-<title>/001_filename1.py"
        "./scripts/<timestamp>-<title>/002_filename2.py" 
        "./scripts/<timestamp>-<title>/003_filename3.py"
    )

    for command in "${commands[@]}"; do
        echo "$command"
        eval "$command"
        if [[ $? -ne 0 ]]; then
            echo "Error: $command failed."
            return 1
        fi
    done

    echo "All scripts finished successfully."
    return 0
}

{ main "$@"; } 2>&1 | tee "$LOG_FILE"
```

## Shell Slurm Example
- File name should `*_sbatch.sh`
- Use multiple nodes if possible
``` bash
#!/bin/bash
# -*- coding: utf-8 -*-
# Timestamp: "2025-04-23 12:53:36 (ywatanabe)"
# File: /ssh:sp:/home/ywatanabe/proj/neurovista/scripts/eda/plot_seizure_aligned_signals.sh

#SBATCH --job-name=plot_seizures
#SBATCH --time=12:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=1
#SBATCH --array=1-15

# Make sure we're reading just one line per task
patient_id=$(sed -n "${SLURM_ARRAY_TASK_ID}p" ./data/PATIENT_IDS.txt | tr -d '\n')

for seizure_type in seizure control; do
    for onset_or_offset in onset offset; do
        pre_sec=30
        post_sec=30

        # Run the Python script for this patient
        ./scripts/eda/plot_seizure_aligned_signals.py \
            --patient_id "$patient_id" \
            --seizure_or_control "$seizure_type" \
            --onset_or_offset "$onset_or_offset" \
            --pre_sec "$pre_sec" \
            --post_sec "$post_sec"
    done
done


# sbatch ./scripts/eda/plot_seizure_aligned_signals_sbatch.sh

# EOF
```

## Shell Hierarchy, Sorting Rules
- Functions must be sorted considering their hierarchy.
- Upstream functions should be placed in upper positions
  - from top (upstream functions) to down (utility functions)
- Do not change any code contents during sorting
- Includes comments to show hierarchy

  - For Shell scripts
  ```shell
  # 1. Main entry point
  # ---------------------------------------- 


  # 2. Core functions
  # ---------------------------------------- 


  # 3. Helper functions
  # ---------------------------------------- 
  ```

## Custom Bash commands and scripts
Agents can access `~/.bashrc`, `~/.bash.d/*.src`, `~/.bin/*/*.sh`
- All `*sh` files should have `-h|--help `option
  - If it is not the case, revise the file contents
- Run all tests: `PROJECT_ROOT/run-tests.sh`
- Run tests with debug output: `./run-tests.sh -d` 
- Run a single test: `./run-tests.sh -s tests/test-ecc-variables.el`

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->