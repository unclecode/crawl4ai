<!-- ---
!-- Timestamp: 2025-06-03 15:23:41
!-- Author: ywatanabe
!-- File: /ssh:ywatanabe@sp:/home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/python/IMPORTANT-general.md
!-- --- -->

## SCITEX Rule
**!!! IMPORATANT !!!**
**ANY PYTHON SCRIPTS MUST BE WRITTEN IN THE SCITEX FORMAT EXPLAINED BELOW.**
THE EXCEPTIONS ARE:
    - Pacakges authored by others
    - Source (`./src`) of pip packages to reduce dependency
THUS, SCITEX MUST BE USED IN:
- `./scripts`
- `./tests`
- `./examples`
For details, see the scitex guideline (`./TOP-MOST-IMPORTANT-scitex.md`).

## `chmod +x *.py`
Do not forget to add the executable permission (`chmod +x`) for `*.py` files.

## `matplotlib.use("Agtg")`
Use `Agg` for matplotlib backend. Do not show images but save to file.
    ``` python
    import matplotlib
    matplotlib.use("Agg")
    ```

## Lint with Black
IMPORTANT: LINT ALL .PY SCRIPTS USING `black` (`~/.env/bin/black`)

## Run scripts
Do not hesitate to run scripts as long as they are destructive.
Using timeout would be beneficial if scripts will take long time.

## Use CUDA
When a GPU can accelerate processing, we prioritize GPU over CPU. 
If GPU is not available and CPU processing will take a long time, please let us know.

## Plotting functions
Plotting functions should `return fig` for consistency
Save, show can be handled outside of plotting functions.
``` python
def plot_xxx(...):
    return fig
    
def main(args):
    fig = plot_xxx(...)
```

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->