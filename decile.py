# %% [markdown]
# # Decile summary as its own CSV (for the Power BI lift chart)
# 10 rows, one per risk decile, with the cumulative % already calculated --
# so the "Risk & Savings" page needs no running-total DAX at all.

# %% Load the file saved by 05_risk_model.py
import pandas as pd

df = pd.read_csv("diabetic_scored.csv")
total_patients = len(df)
baseline_readmits = df["readmit_30"].sum()

decile_summary = (
    df.groupby("risk_decile")
    .agg(patients=("readmit_30", "size"), readmits=("readmit_30", "sum"))
    .sort_index(ascending=False)   # 9 = highest risk, first
    .reset_index()
)
decile_summary["rate_pct"] = (100 * decile_summary["readmits"] / decile_summary["patients"]).round(2)
decile_summary["cum_patients_pct"] = (100 * decile_summary["patients"].cumsum() / total_patients).round(1)
decile_summary["cum_readmits_pct"] = (100 * decile_summary["readmits"].cumsum() / baseline_readmits).round(1)

print(decile_summary.to_string(index=False))
decile_summary.to_csv("decile_summary.csv", index=False)
print("\nSaved decile_summary.csv -- import into Power BI with Get Data -> Text/CSV")