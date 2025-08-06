<!-- ---
!-- Timestamp: 2025-06-14 06:44:49
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/python/IMPORTANT-SCITEX-17-other-modules.md
!-- --- -->

### Utility Functions
```python
# Colored console output with specified border
stx.str.printc("message here", c='blue', char="-", n=40)
# ----------------------------------------
# message here
# ----------------------------------------

# Convert p-values to significance stars (e.g., *)
stx.stats.p2stars(p_value)

# Apply FDR correction for multiple comparisons
stx.stats.fdr_correction(results_df)

# Round numeric values in dataframe
stx.pd.round(df, factor=3)
```

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->