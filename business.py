# %% [markdown]
# # Step 7: Business impact (savings estimate)
# This dataset has no cost column, so the dollar figure here is a SCENARIO,
# not a fact from the data. Two numbers come from outside sources, cited
# below -- change them if you find better ones, and always report where
# they came from in your write-up.
#
# ASSUMPTION 1 -- Cost per readmission: $16,300
#   Source: AHRQ Healthcare Cost and Utilization Project (HCUP),
#   Statistical Brief #304 (2020 data): average cost of a 30-day all-cause
#   hospital readmission. https://hcup-us.ahrq.gov/reports/statbriefs/sb304-readmissions-2016-2020.pdf
#
# ASSUMPTION 2 -- Intervention effectiveness: 10% / 20% / 30% relative
#   reduction in readmissions among the group targeted (a sensitivity
#   range, not a single guess).
#   Grounded in published post-discharge phone-call / transitional-care
#   programs, which report relative reductions roughly in this range, e.g.
#   the VA's C-TraC nurse call-back program (~one-third relative
#   reduction: 23% vs. 34%, Health Affairs 2012) and Coleman's Care
#   Transitions Intervention (~36% relative reduction: 12.8% vs. 20%,
#   Archives of Internal Medicine). Real results vary a lot by hospital,
#   patient population and how well the program is run -- treat the
#   scenario numbers below as illustrative, not a forecast.

# %% Load the file saved by 05_risk_model.py (scored on the FULL population)
import pandas as pd

df = pd.read_csv("diabetic_scored.csv")
COST_PER_READMISSION = 16300  # AHRQ HCUP Statistical Brief #304

total_patients = len(df)
baseline_readmits = df["readmit_30"].sum()
print(f"Total patients: {total_patients:,} | Baseline readmissions: {baseline_readmits:,} "
      f"({100*baseline_readmits/total_patients:.2f}%)")

# %% Decile summary on the full population (highest risk = decile 9)
decile_summary = (
    df.groupby("risk_decile")
    .agg(patients=("readmit_30", "size"), readmits=("readmit_30", "sum"))
    .sort_index(ascending=False)
)
decile_summary["cum_patients"] = decile_summary["patients"].cumsum()
decile_summary["cum_readmits"] = decile_summary["readmits"].cumsum()
decile_summary["cum_patients_pct"] = (100 * decile_summary["cum_patients"] / total_patients).round(1)
decile_summary["cum_readmits_pct"] = (100 * decile_summary["cum_readmits"] / baseline_readmits).round(1)
print("\n=== Full-population decile summary ===")
print(decile_summary)

# %% Sensitivity table: targeting the top N% of patients, at 3 success rates
# Percentages are multiples of 10 because the model splits patients into
# deciles (10% chunks) -- that's the finest grouping available, so e.g. 15%
# and 20% would otherwise land on the exact same decile and look like
# duplicate rows.
target_pcts = [10, 20, 30, 40, 50]
success_rates = [0.10, 0.20, 0.30]

rows = []
for pct in target_pcts:
    cutoff = decile_summary[decile_summary["cum_patients_pct"] >= pct].iloc[0]
    patients_targeted = int(cutoff["cum_patients"])
    readmits_in_group = int(cutoff["cum_readmits"])
    row = {
        "target_top_pct": pct,
        "actual_pct_targeted": cutoff["cum_patients_pct"],
        "patients_targeted": patients_targeted,
        "readmits_in_group": readmits_in_group,
        "pct_of_all_readmits_captured": round(100 * readmits_in_group / baseline_readmits, 1),
    }
    for s in success_rates:
        avoided = readmits_in_group * s
        row[f"avoided_readmits_{int(s*100)}pct_success"] = round(avoided, 0)
        row[f"savings_{int(s*100)}pct_success"] = round(avoided * COST_PER_READMISSION, 0)
    rows.append(row)

impact_table = pd.DataFrame(rows)
print("\n=== Business impact sensitivity table ===")
print(impact_table.to_string(index=False))

impact_table.to_csv("business_impact_sensitivity.csv", index=False)
print("\nSaved business_impact_sensitivity.csv")

# %% [markdown]
# How to read this table, e.g. for the "target_top_pct = 20" row:
# - "pct_of_all_readmits_captured" -- if the hospital focused its
#   intervention on just this highest-risk 20% of patients, it would be
#   addressing that share of ALL 30-day readmissions in the dataset.
# - "avoided_readmits_20pct_success" -- if the intervention cuts
#   readmissions among that targeted group by 20% (a middle-of-the-road
#   published result), this many readmissions would be avoided.
# - "savings_20pct_success" -- that many avoided readmissions, valued at
#   the AHRQ average cost per readmission.
#