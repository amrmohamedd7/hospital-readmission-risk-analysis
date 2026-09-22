# Hospital Readmission Risk Analysis

**Which patients are most likely to be readmitted within 30 days, why, and what would it be worth to intervene?**

A data-analyst case study using the UCI "Diabetes 130-US Hospitals" dataset — SQL for exploration, Python for statistical validation and risk modeling, Power BI for the decision-facing dashboard.

## Problem

Hospital readmissions within 30 days are costly and are treated as a quality-of-care signal by US payers (Medicare penalizes hospitals for excess readmissions). This project identifies which patients are at highest risk of readmission, tests whether the apparent drivers are statistically real, builds a model to flag high-risk patients before discharge, and estimates what a targeted intervention program could be worth.

## Data

- Source: [UCI Diabetes 130-US Hospitals (1999–2008)](https://archive.ics.uci.edu/dataset/296/diabetes-130-us-hospitals-for-years-1999-2008)
- Scope: inpatient diabetes encounters across 130 US hospitals
- Cleaning: removed patients who died or were discharged to hospice (cannot be readmitted), and deduplicated to one encounter per patient
- **Final cohort: 69,990 patients | Baseline 30-day readmission rate: 8.98%**

## Method

| Stage | Tool |
|---|---|
| Cleaning, feature engineering (diagnosis groups, age bands, prior-utilization bands) | Python (pandas) |
| Exploratory driver analysis (rate, gap vs. overall, share of readmissions per group) | SQL Server (T-SQL: CTEs, window functions, a reporting view) |
| Hypothesis testing (are the drivers real, or noise?) | Python (scipy: chi-square, Cramér's V, Cochran-Armitage trend test) |
| Risk scoring model | Python (scikit-learn: logistic regression) |
| Business impact / savings estimate | Python (pandas), external cost benchmark |
| Dashboard | Power BI (3 pages: Overview, Drivers, Risk & Savings) |

## Key findings

**1. Prior inpatient visits is the strongest driver of readmission — a clean dose-response relationship:**

| Prior inpatient visits | Readmission rate |
|---|---|
| 0 | 8.13% |
| 1 | 12.88% |
| 2 | 18.52% |
| 3+ | 26.45% |

Confirmed with a logistic regression: patients with 3+ prior inpatient visits have **~4.0x the odds** of readmission vs. patients with none (Cochran-Armitage trend test confirms this is a genuine ordered trend, not noise).

**2. Discharge destination is the second-strongest driver.** Patients discharged to "Other" (14.38%) or a skilled nursing facility (13.42%) are readmitted at roughly **double the rate** of patients discharged home (6.95%) — odds ratios of 2.19x and 1.75x respectively, holding other factors constant.

**3. Age, length of stay, and medication count show real but modest effects**, each confirmed significant by chi-square testing but with small effect sizes (Cramér's V 0.04–0.06).

**4. HbA1c testing shows no meaningful association with readmission in this data** (rates 8.16%–9.11% across all testing categories; chi-square p = 0.062, Cramér's V = 0.01). This is a deliberate, tested null finding, not an oversight — expanding HbA1c testing would not be a good readmission-reduction investment based on this evidence.

**Effect size ranking (Cramér's V, most to least important):**
`discharge_group (0.103) > prior_inpatient_band (0.098) > los_band (0.055) > age_group (0.051) > med_band (0.040) > diag_group (0.033) > med_change (0.015) > a1c_status (0.010, not significant)`

## Risk model

A logistic regression combining the confirmed drivers achieves a **test AUC of 0.637** — in line with published results on this dataset using far more features. The model isn't meant to predict individual outcomes with high precision; it's meant to **rank** patients so limited intervention resources go to the right people.

| Risk decile | Readmission rate |
|---|---|
| 9 (highest risk) | 18.45% |
| 5 (middle) | 8.60% |
| 0 (lowest risk) | 4.10% |

**The highest-risk 20% of patients account for 35% of all 30-day readmissions.**

## Business impact

The dataset has no cost field, so this section uses two external, cited assumptions rather than numbers invented for this analysis:

- **Cost per readmission: $16,300** — AHRQ Healthcare Cost and Utilization Project, [Statistical Brief #304](https://hcup-us.ahrq.gov/reports/statbriefs/sb304-readmissions-2016-2020.pdf) (2020 data)
- **Program effectiveness: 10–30% relative reduction in readmissions among the targeted group** — a sensitivity range grounded in two published transitional-care programs: the VA's C-TraC nurse call-back study (~1/3 relative reduction) and Coleman's Care Transitions Intervention (~36% relative reduction)

This cohort's readmissions represent an estimated **$102.4M** in total cost (6,285 readmissions × $16,300).

| Target group | Patients | % of all readmissions captured | Avoided readmissions (10–30% success) | Estimated savings (10–30% success) |
|---|---|---|---|---|
| Top 20% by risk score | 13,997 | 35.0% | 220 – 661 | $3.59M – $10.77M |

**Headline scenario:** targeting the highest-risk 20% of patients with a follow-up program achieving a conservative 20% relative reduction would avoid an estimated **440 readmissions, worth ~$7.2M**.

## Recommendations

1. **Launch a risk-based post-discharge follow-up program targeting the highest-risk 20% of patients**, using the model's risk score to prioritize outreach (e.g., a 72-hour follow-up call). This group is only a fifth of patients but accounts for over a third of all readmissions — the highest-leverage place to act.
2. **Build a structured discharge protocol for patients going to "Other" destinations or skilled nursing facilities.** Their readmission odds are roughly double those of patients discharged home, even after accounting for other risk factors — this points at the discharge/handoff process itself, not just patient severity.
3. **Flag patients with 2+ prior inpatient admissions automatically at admission.** This is the single strongest predictor in the data (up to 4x higher odds) and should trigger enrollment in a care-transitions program.
4. **Do not prioritize expanded HbA1c testing as a readmission-reduction lever.** The data shows no significant association — resources are better spent on the discharge-destination and prior-utilization interventions above, where the evidence is strong.
5. **Treat length of stay and medication count as secondary signals** to refine future model iterations, not as standalone intervention targets.

## Limitations

- Data covers 1999–2008, US hospitals, diabetic inpatients only. Findings describe patterns in this historical cohort and would need validation against a hospital's current population before any operational use.
- All relationships are observational associations, not proven causal effects — "associated with," not "causes."
- The $16,300 cost figure and the 10–30% effectiveness range are external published benchmarks, not values measured in this dataset. They're presented as a sensitivity range, not a forecast.
- An AUC of 0.637 means the model is useful for prioritization and ranking, not for confident individual-level prediction.

## Repository structure

```
sql/
  00_create_table_sqlserver.sql       -- explicit-schema table creation + bulk load
  03_driver_analysis_sqlserver.sql    -- driver analysis + reporting view (vw_driver_summary)
python/
  01_load_clean_explore.py            -- load, define target, clean
  02_features.py                      -- diagnosis/age/utilization groupings
  04_statistical_tests.py             -- chi-square, Cramer's V, trend test
  05_risk_model.py                    -- logistic regression risk scoring
  06_business_impact.py               -- savings sensitivity table
  07_driver_summary_csv.py            -- driver summary as CSV (no SQL Server needed)
  08_decile_summary_csv.py            -- decile summary as CSV, for the lift chart
dashboard/
  readmission_dashboard.pbix          -- 3-page Power BI report
README.md
```

## Tools

SQL Server (T-SQL) · Python (pandas, scipy, scikit-learn) · Power BI · Excel/CSV

---

### For a resume / CV

> Analyzed 69,990 hospital encounters to identify drivers of 30-day readmission, using SQL for exploration and statistical testing (chi-square, Cramér's V) to confirm findings. Built a logistic regression risk model (AUC 0.637) showing the highest-risk 20% of patients account for 35% of all readmissions, and quantified a targeted intervention program's value at $3.6M–$10.8M using AHRQ cost benchmarks and published program-effectiveness data. Delivered findings via a 3-page interactive Power BI dashboard.
