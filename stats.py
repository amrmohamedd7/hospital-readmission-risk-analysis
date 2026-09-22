# %% [markdown]
# # Step 5: Statistical testing
# Confirms which SQL findings are real effects vs. noise, and ranks them by
# how STRONG each effect is (not just whether it's "significant").
#
# Why this matters: with ~70,000 patients, almost every difference will show
# up as "statistically significant" (very small p-value) even if it's tiny
# and useless in practice. So we report BOTH the p-value (is it real?) and
# Cramer's V (how big is it?). Cramer's V for a 2-row table roughly means:
#   ~0.10 = small effect | ~0.20-0.30 = moderate | 0.30+ = strong

# %% Load
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency

df = pd.read_csv("diabetic_features.csv")
print("Rows:", len(df), "| Overall readmit_30 rate:", round(df["readmit_30"].mean() * 100, 2), "%")

# %% Chi-square + Cramer's V for every driver found in SQL
def chi_square_test(data, col, target="readmit_30"):
    table = pd.crosstab(data[col], data[target])
    chi2, p, dof, expected = chi2_contingency(table)
    n = table.values.sum()
    min_dim = min(table.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * min_dim))
    return {
        "variable": col,
        "chi2": round(chi2, 1),
        "dof": dof,
        "p_value": p,
        "cramers_v": round(cramers_v, 4),
        "n": n,
    }

drivers = [
    "prior_inpatient_band", "discharge_group", "los_band", "age_group",
    "diag_group", "med_change", "a1c_status", "med_band",
]

results = pd.DataFrame([chi_square_test(df, col) for col in drivers])
results["p_value_fmt"] = results["p_value"].apply(lambda p: "<0.001" if p < 0.001 else round(p, 4))
results = results.sort_values("cramers_v", ascending=False)
print("\n=== Ranked by effect size (Cramer's V) ===")
print(results[["variable", "cramers_v", "chi2", "dof", "p_value_fmt", "n"]].to_string(index=False))

# %% [markdown]
# Read the table above like this:
# - Sort by cramers_v, not by p-value. p-value only says "not random";
#   cramers_v says "how much it actually matters."
# - Anything below ~0.05 is negligible even if p < 0.001 -- flag it as
#   "statistically detectable but practically weak" in your write-up.

# %% Deep dive on the strongest driver: prior_inpatient_band
# Standardized residuals show WHICH specific cells drive the association
# (>2 or <-2 is generally considered notable)
table = pd.crosstab(df["prior_inpatient_band"], df["readmit_30"])
chi2, p, dof, expected = chi2_contingency(table)
residuals = (table - expected) / np.sqrt(expected)
print("\n=== prior_inpatient_band: observed counts ===")
print(table)
print("\n=== prior_inpatient_band: standardized residuals (col 1 = readmitted) ===")
print(residuals.round(2))

# %% Same deep dive for discharge_group
table2 = pd.crosstab(df["discharge_group"], df["readmit_30"])
chi2b, pb, dofb, expected2 = chi2_contingency(table2)
residuals2 = (table2 - expected2) / np.sqrt(expected2)
print("\n=== discharge_group: standardized residuals (col 1 = readmitted) ===")
print(residuals2.round(2))

# %% Trend test for prior_inpatient_band: is the rise actually a straight-line trend?
# (Cochran-Armitage trend test -- more powerful than plain chi-square for
#  ordered categories, because it uses the order, not just the grouping)
def cochran_armitage_trend(data, ordered_col, scores, target="readmit_30"):
    table = pd.crosstab(data[ordered_col], data[target]).reindex(list(scores.keys()))
    n_i = table.sum(axis=1).values
    r_i = table[1].values
    s = np.array(list(scores.values()))
    N = n_i.sum()
    R = r_i.sum()
    s_bar = (n_i * s).sum() / N
    numerator = (r_i * (s - s_bar)).sum()
    p_bar = R / N
    var = p_bar * (1 - p_bar) * (n_i * (s - s_bar) ** 2).sum()
    z = numerator / np.sqrt(var)
    from scipy.stats import norm
    p_value = 2 * (1 - norm.cdf(abs(z)))
    return z, p_value

z, p_trend = cochran_armitage_trend(
    df, "prior_inpatient_band", {"0": 0, "1": 1, "2": 2, "3+": 3}
)
print(f"\nCochran-Armitage trend test (prior_inpatient_band): z={z:.2f}, p={'<0.001' if p_trend < 0.001 else round(p_trend, 4)}")

results.drop(columns="p_value_fmt").to_csv("statistical_test_results.csv", index=False)
print("\nSaved statistical_test_results.csv")