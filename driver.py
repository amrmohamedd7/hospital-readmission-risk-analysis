# %% [markdown]
# # Driver summary as CSV (no SQL Server needed)
# Reproduces the same numbers as the dbo.vw_driver_summary SQL view, straight
# from diabetic_features.csv. Use this if Power BI can't reach SQL Server --
# the values are identical either way, since it's the same logic.

# %% Load
import pandas as pd

df = pd.read_csv("diabetic_features.csv")
overall_rate = 100 * df["readmit_30"].mean()

# %% Stack every driver into one long table (dimension, level, readmit_30)
dimensions = {
    "Age group": "age_group",
    "Primary diagnosis": "diag_group",
    "Prior inpatient visits": "prior_inpatient_band",
    "Discharge destination": "discharge_group",
    "Length of stay": "los_band",
    "Medication load": "med_band",
    "HbA1c testing": "a1c_status",
    "Medication change": "med_change",
}

rows = []
for dim_name, col in dimensions.items():
    g = df.groupby(col)["readmit_30"].agg(patients="size", readmits="sum").reset_index()
    g = g.rename(columns={col: "level"})
    g["dimension"] = dim_name
    rows.append(g)

long_df = pd.concat(rows, ignore_index=True)

# %% Add the same derived columns as the SQL view
long_df["rate_pct"] = (100 * long_df["readmits"] / long_df["patients"]).round(2)
long_df["gap_vs_overall_pp"] = (long_df["rate_pct"] - overall_rate).round(2)
long_df["share_of_readmits_pct"] = (
    100 * long_df["readmits"] / long_df.groupby("dimension")["readmits"].transform("sum")
).round(1)

long_df = long_df[["dimension", "level", "patients", "readmits",
                    "rate_pct", "gap_vs_overall_pp", "share_of_readmits_pct"]]
long_df = long_df.sort_values(["dimension", "rate_pct"], ascending=[True, False])

print(long_df.to_string(index=False))
long_df.to_csv("driver_summary.csv", index=False)
print("\nSaved driver_summary.csv -- import this into Power BI with Get Data -> Text/CSV")