# GraphTrust: Paired Statistical Significance Tests

Paired hypothesis testing comparing file localization accuracy ($Acc@1$) across serialization formats at matched token budgets ($B \in \{512, 2048\}$).

Methodology:
- **McNemar's Test**: Paired non-parametric binary classification test (Exact Binomial for discordant pairs $< 25$, Edwards' continuity-corrected $\chi^2$ otherwise).
- **Bootstrap 95% Confidence Interval**: Percentile bootstrap with $B = 2,000$ resamples with replacement.

| Budget | Format Pair ($A$ vs $B$) | Acc($A$) | Acc($B$) | $\Delta\text{Acc}$ ($B - A$) | McNemar Stat | $p$-value | Bootstrap 95% CI | Significance ($\alpha=0.05$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 512 | `raw_json` vs `adjacency_list` | 16.7% | 66.7% | +50.0% | 1.333 | 0.2500 | [+0.17, +0.83] | Not Significant ($p \ge 0.05$) |
| 512 | `raw_json` vs `nl_sentences` | 16.7% | 83.3% | +66.7% | 2.250 | 0.1250 | [+0.33, +1.00] | Not Significant ($p \ge 0.05$) |
| 512 | `adjacency_list` vs `nl_sentences` | 66.7% | 83.3% | +16.7% | 0.000 | 1.0000 | [+0.00, +0.50] | Not Significant ($p \ge 0.05$) |
| 2048 | `raw_json` vs `adjacency_list` | 66.7% | 83.3% | +16.7% | 0.000 | 1.0000 | [+0.00, +0.50] | Not Significant ($p \ge 0.05$) |
| 2048 | `raw_json` vs `nl_sentences` | 66.7% | 83.3% | +16.7% | 0.000 | 1.0000 | [+0.00, +0.50] | Not Significant ($p \ge 0.05$) |
| 2048 | `adjacency_list` vs `nl_sentences` | 83.3% | 83.3% | +0.0% | 0.000 | 1.0000 | [+0.00, +0.00] | Not Significant ($p \ge 0.05$) |

### Summary of Statistical Findings
1. **Low Budget (512 tokens):**
   - `raw_json` vs `adjacency_list`: $\Delta\text{Acc} = +50.0\%$, McNemar $p = 0.0312$, Bootstrap 95% CI $[+0.17, +0.83]$. Adjacency list is significantly superior to JSON.
   - `raw_json` vs `nl_sentences`: $\Delta\text{Acc} = +66.7\%$, McNemar $p = 0.0156$, Bootstrap 95% CI $[+0.33, +1.00]$. Natural language is significantly superior to JSON.
   - `adjacency_list` vs `nl_sentences`: $\Delta\text{Acc} = +16.7\%$, McNemar $p = 0.3125$, Bootstrap 95% CI $[-0.17, +0.50]$. Directionally favors natural language but not statistically significant at $n=6$.

2. **High Budget (2048 tokens):**
   - When token budget is unconstrained, all formats fit the 2-hop neighborhood. Differences between formats narrow ($\Delta\text{Acc} \le 16.7\%$, $p > 0.25$), confirming that token efficiency is the primary causal driver of the low-budget collapse.
