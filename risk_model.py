# %% [markdown]
# # Step 6: Risk segmentation (logistic regression)
# Combines the drivers confirmed in step 5 into one model that ranks EVERY
# patient by readmission risk. The model doesn't need to be highly accurate
# at predicting the future -- it needs to be good at RANKING, so we can say
# "these patients are the highest-risk 20%" and act on that group.
#
# Realistic expectation: published work on this exact dataset gets an AUC
# around 0.65-0.68 using far more features than we're using here. Ours will
# likely land somewhere around 0.60-0.65. That's normal, not a bug -- write
# it in your README as an honest limitation, not something to hide.

# %% Load
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

df = pd.read_csv("diabetic_features.csv")

# %% Choose features
# Using the categorical bands confirmed in step 5 (04_statistical_tests.py).
# a1c_status is EXCLUDED: it wasn't significant (p=0.062, Cramer's V=0.01).
# That's a deliberate, documented choice -- not an oversight.
feature_cols = [
    "age_group", "discharge_group", "los_band",
    "med_band", "diag_group", "prior_inpatient_band", "med_change",
]
target_col = "readmit_30"

data = df[feature_cols + [target_col]].dropna()
print("Rows used:", len(data), "of", len(df))

# One-hot encode. drop_first=True sets a reference category per variable,
# so each coefficient means "vs. that reference," which is what makes the
# odds ratios below interpretable.
X = pd.get_dummies(data[feature_cols], drop_first=True)
y = data[target_col]

# %% Train/test split (stratify keeps the ~9% readmission rate the same in both)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)
print("Train:", len(X_train), "| Test:", len(X_test))

# %% Fit on train, evaluate on test (honest, out-of-sample check)
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

test_probs = model.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, test_probs)
print(f"\nTest AUC: {auc:.3f}  (0.5 = random guessing, 1.0 = perfect ranking)")

# %% Odds ratios: which categories raise or lower the odds of readmission?
odds_ratios = pd.DataFrame({
    "feature": X.columns,
    "odds_ratio": np.exp(model.coef_[0]),
}).sort_values("odds_ratio", ascending=False)
print("\n=== Odds ratios (vs. each variable's reference category) ===")
print(odds_ratios.to_string(index=False))
# odds_ratio > 1 means higher odds of readmission than the reference group;
# < 1 means lower odds. E.g. 1.8 reads as "1.8x the odds of the reference."

# %% Risk deciles on the TEST set (out-of-sample, so the lift numbers are honest)
test_results = pd.DataFrame({"y_true": y_test.values, "risk_score": test_probs})
test_results["risk_decile"] = pd.qcut(
    test_results["risk_score"], 10, labels=False, duplicates="drop"
)
# decile 9 = highest risk, 0 = lowest

decile_summary = (
    test_results.groupby("risk_decile")
    .agg(patients=("y_true", "size"), readmits=("y_true", "sum"))
    .sort_index(ascending=False)
)
decile_summary["rate_pct"] = (100 * decile_summary["readmits"] / decile_summary["patients"]).round(2)
decile_summary["cumulative_readmits_pct"] = (
    100 * decile_summary["readmits"].cumsum() / decile_summary["readmits"].sum()
).round(1)
decile_summary["cumulative_patients_pct"] = (
    100 * decile_summary["patients"].cumsum() / decile_summary["patients"].sum()
).round(1)
print("\n=== Risk deciles (9 = highest risk), test set only ===")
print(decile_summary)

# %% [markdown]
# Read `cumulative_readmits_pct` next to `cumulative_patients_pct`:
# e.g. if the top 2 deciles (20% of patients) show cumulative_readmits_pct
# of 35%, that means: "targeting the highest-risk 20% of patients would
# reach 35% of all 30-day readmissions." That's the lift number your
# business-impact section will use to estimate savings.

# %% Final step: refit on ALL data, score every patient (for Power BI)
final_model = LogisticRegression(max_iter=1000)
final_model.fit(X, y)
data["risk_score"] = final_model.predict_proba(X)[:, 1]
data["risk_decile"] = pd.qcut(data["risk_score"], 10, labels=False, duplicates="drop")
data["risk_tier"] = pd.cut(
    data["risk_decile"], bins=[-1, 6, 8, 9], labels=["Low", "Medium", "High"]
)

print("\n=== Risk tier sizes (full dataset) ===")
print(data["risk_tier"].value_counts())

data.to_csv("diabetic_scored.csv", index=False)
print("\nSaved diabetic_scored.csv (feed this into Power BI)")