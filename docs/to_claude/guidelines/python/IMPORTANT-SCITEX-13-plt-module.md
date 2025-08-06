<!-- ---
!-- Timestamp: 2025-06-14 06:43:44
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/python/IMPORTANT-SCITEX-13-plt-module.md
!-- --- -->

## `scitex.plt`

- `scitex.plt` is a module for enhancing matplotlib for scientific purposes

### `scitex.plt.subplots`
- `scitex.plt.subplots` is a wrapper for `matplotlib.pyplot.plt.subplots`
- However, it is not perfectly compatible
- When problem found, create a bug-report to:
  `~/proj/scitex_repo/project_management/bug-report-<title>.md`

Features of `scitex.plt.subplots`:
- Track plotted data
- `stx.io.save(fig, "./path/to/image.jpg", symlink_from_cwd=True)` creates
  - 1. `./path/to/image.jpg` (as described in the `scitex.io.save` block)
  - 2. `./path/to/image.csv` <- Plotted data. IMPORTANT FOR CODE UNDERSTANDING AND REPRODUCIBILITY
  - 3. Symlinks to both the jpg and csv files

###### Basic Usage
```python
# Create trackable plots
fig, axes = stx.plt.subplots(ncols=2)   # Returns wrapper objects that track plotting data

# Set axis properties with combined method
ax.set_xyt('X-axis', 'Y-axis', 'Title')  # ALWAYS use scitex wrappers instead of matplotlib methods
```
#### Creating Plots

```python
# Create a figure with tracked axes
fig, axes = stx.plt.subplots(ncols=2, figsize=(10, 5))

# Plot data
axes[0].plot(x, y, label='Data')
axes[1].scatter(x, z, label='Scatter')

# Set labels and title using scitex wrapper method (PREFERRED WAY)
axes[0].set_xyt('X-axis', 'Y-axis', 'Data Plot')
axes[1].set_xyt('X-axis', 'Y-axis', 'Scatter Plot')

# Add legend
for ax in axes:
    ax.legend()
```

#### Exporting Plot Data

```python
# Automatically export to CSV when saving figure
stx.io.save(fig, './data/figures/plot.png', symlink_from_cwd=True)
# Creates:
# - /path/to/script_out/data/figures/plot.png
# - /path/to/script_out/data/figures/plot.csv
# - ./data/figures/plot.png -> /path/to/script_out/data/figures/plot.png
# - ./data/figures/plot.csv -> /path/to/script_out/data/figures/plot.csv
```

## Example: Plot with CSV Export

```python
import numpy as np
import scitex

# Create data
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)

# Create figure with scitex
fig, axes = stx.plt.subplots(ncols=2, figsize=(10, 5))

# Plot data
axes[0].plot(x, y1, label='sin(x)')
axes[1].plot(x, y2, label='cos(x)')

# Use scitex wrapper methods for labels and titles
axes[0].set_xyt('x', 'y', 'Sine Function')
axes[1].set_xyt('x', 'y', 'Cosine Function')

# Add legends
for ax in axes:
    ax.legend()

# Save figure - CSV automatically exported with the same basename
stx.io.save(fig, './data/figures/trig_functions.png', symlink_from_cwd=True)
```

This creates:
- `./data/figures/trig_functions.png` (the figure)
- `./data/figures/trig_functions.csv` (the data in CSV format)

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->