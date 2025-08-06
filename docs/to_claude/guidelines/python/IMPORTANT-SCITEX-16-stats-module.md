<!-- ---
!-- Timestamp: 2025-06-14 06:44:32
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/python/IMPORTANT-SCITEX-16-stats-module.md
!-- --- -->

## `scitex.stats`

- `scitex.stats` is a module for statistical tests

```python
# Format p-values with stars
stars = stc.stats.p2stars(0.001)  # '***'

# Apply multiple comparison correction
corrected = stc.stats.fdr_correction(results_df)

# Correlation tests
r, p = stc.stats.tests.corr_test(x, y, method='pearson')
```

## Statistical Reporting

Report statistical results with:
- p-value
- Significance stars
- Sample size
- Effect size
- Test name
- Statistic value
- Null hypothesis

```python
# Example results dictionary
results = {
    "p_value": pval,
    "stars": stc.stats.p2stars(pval),  # Format: 0.02 -> "*", 0.009 -> "**"
    "n1": n1,
    "n2": n2,
    "dof": dof,
    "effsize": effect_size,
    "test_name": test_name_text,
    "statistic": statistic_value,
    "H0": null_hypothesis_text,
}
```

### Using p2stars

```python
>>> stc.stats.p2stars(0.0005)
'***'
>>> stc.stats.p2stars("0.03")
'*'
>>> stc.stats.p2stars("1e-4")
'***'
>>> df = pd.DataFrame({'p_value': [0.001, "0.03", 0.1, "NA"]})
>>> stc.stats.p2stars(df)
   p_value
0  0.001 ***
1  0.030   *
2  0.100
3     NA  NA
```

### Multiple Comparisons Correction

Always use FDR correction for multiple comparisons:

```python
# Apply FDR correction to DataFrame with p_value column
corrected_results = stc.stats.fdr_correction(results_df)
```

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->