<!-- ---
!-- Timestamp: 2025-06-14 06:44:21
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/python/IMPORTANT-SCITEX-15-pd-module.md
!-- --- -->

### `scitex.pd` Module (Pandas Utilities)

```python
# Round numeric values
rounded_df = stx.pd.round(df, factor=3)

# Enhanced DataFrame slicing
filtered = stx.pd.slice(df, {'column1': 'value', 'column2': [1, 2, 3]})

# Coordinate conversion
xyz_data = stx.pd.to_xyz(df)
```

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->