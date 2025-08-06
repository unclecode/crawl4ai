<!-- ---
!-- Timestamp: 2025-05-29 02:32:43
!-- Author: ywatanabe
!-- File: /ssh:ywatanabe@sp:/home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/science/scientific-writing-general.md
!-- --- -->


# Scientific Guidelines

## Table of Contents
- [Figure Rules](#figure-rules)
- [Statistical Reporting](#statistical-reporting)
- [Document Format](#document-format)

## Figure Rules

| ❌ DO NOT | ✅ DO |
|-----------|------|
| ```python
# Missing axis labels
plt.plot(x, y)
plt.show()
``` | ```python
# Complete axis information
plt.plot(x, y)
plt.xlabel('Time (s)')
plt.ylabel('Amplitude (mV)')
plt.title('Signal Measurement')
plt.show()
``` |
| ```python
# Bar graph not starting from 0
plt.bar(categories, values)
plt.ylim(min(values) - 0.1, max(values) + 0.1)
``` | ```python
# Bar graph properly starting from 0
plt.bar(categories, values)
plt.ylim(0, max(values) * 1.1)
``` |
| ```python
# Misleading probability range
plt.plot(x, probabilities)
plt.ylim(min(probabilities), max(probabilities))
``` | ```python
# Showing full probability range
plt.plot(x, probabilities)
plt.ylim(0, 1)
``` |

### Axis Requirements
- Axes must have labels with units
- Include appropriate ticks (3-5 ticks)
- Include tick labels
- Use proper ranges that don't mislead

### Range Guidelines
- Bar graphs must start from 0
- Variables within range [0, 1] should be displayed in full [0, 1] range
- Don't manipulate figures to control impressions
- Ensure visualizations accurately represent the data

### Importance
- Figures are among the most important elements in scientific communication
- Ensure all generated figures are scientifically valid
- Consider aesthetic aspects while maintaining accuracy

## Statistical Reporting

| ❌ DO NOT | ✅ DO |
|-----------|------|
| ```python
# Incomplete statistical reporting
p = stats.ttest_ind(group1, group2).pvalue
print(f"p = {p:.3f}")
``` | ```python
# Complete statistical reporting
result = stats.ttest_ind(group1, group2)
pval = result.pvalue
dof = len(group1) + len(group2) - 2
effect_size = (np.mean(group1) - np.mean(group2)) / np.sqrt((np.std(group1)**2 + np.std(group2)**2) / 2)

results = {
    "p_value": pval,
    "stars": scitex.stats.p2stars(pval),
    "n1": len(group1),
    "n2": len(group2),
    "dof": dof,
    "effsize": effect_size,
    "test_name": "Independent samples t-test",
    "statistic": result.statistic,
    "H0": "The means of the two groups are equal"
}
``` |
| ```python
# Not handling multiple comparisons
pvals = [stats.ttest_ind(group, control).pvalue 
         for group in treatment_groups]
significant = [p < 0.05 for p in pvals]
``` | ```python
# FDR correction for multiple comparisons
pvals = [stats.ttest_ind(group, control).pvalue 
         for group in treatment_groups]
results_df = pd.DataFrame({"p_value": pvals})
corrected_results = scitex.stats.fdr_correction(results_df)
significant = corrected_results["p_value_fdr"] < 0.05
``` |

### Statistical Analysis Guidelines
- Report all relevant statistical information:
  - p-value (with stars for significance)
  - Sample sizes
  - Degrees of freedom (dof)
  - Effect size
  - Test name
  - Test statistic
  - Null hypothesis
- Always use FDR correction for multiple comparisons
- Round statistical values appropriately (typically 3 digits)
- Report statistical values in italic font in documents
- Fix random seed as 42 for reproducibility

## Document Format

| ❌ DO NOT | ✅ DO |
|-----------|------|
| ```
**IMPORTANT NOTE: This analysis shows...**
*Many asterisks to emphasize points*
``` | ```
Minimal formatting:
1. Analysis results
2. Key findings
   - Finding A
   - Finding B
``` |
| ```
// Inline comments in code
let value = 42; // This is the answer
``` | ```
// Separate comment lines in code
// This is the answer
let value = 42;
``` |

### Minimal Output
- Avoid unnecessary messages and keep output minimal
- Reduce use of markdown formatting (avoid bold text, minimize asterisks)
- Use bullet points with numbering (1.) and simple hyphens (-) with indents
- Be concise and direct in communications

### Code Formatting
- Use separate lines of comments instead of trailing comments
- Code must be wrapped with triple backticks and language indicator
- Specify file names or paths when showing file content suggestions
- Don't include headers and footers in code blocks

<!-- EOF -->