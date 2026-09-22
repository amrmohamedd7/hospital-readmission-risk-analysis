/* =====================================================================
   Create and load dbo.diabetic_features (SQL Server)
   Replaces the Import Flat File wizard: the column types are set here,
   so nothing gets mistyped, truncated or dropped.

   Before running:
   1) Copy diabetic_features.csv to C:\Temp\  (create the folder if needed)
   2) Change the database name below if yours is different
   ===================================================================== */

USE HospitalReadmission;
GO

-- Remove any half-loaded table left by a failed wizard import
DROP TABLE IF EXISTS dbo.diabetic_features;
GO

-- Column order = column order of diabetic_features.csv (61 columns)
CREATE TABLE dbo.diabetic_features (
    encounter_id              int         NOT NULL PRIMARY KEY,
    patient_nbr               int         NULL,
    race                      varchar(30) NULL,
    gender                    varchar(20) NULL,
    age                       varchar(10) NULL,
    admission_type_id         int         NULL,
    discharge_disposition_id  int         NULL,
    admission_source_id       int         NULL,
    time_in_hospital          int         NULL,
    payer_code                varchar(10) NULL,
    medical_specialty         varchar(100) NULL,
    num_lab_procedures        int         NULL,
    num_procedures            int         NULL,
    num_medications           int         NULL,
    number_outpatient         int         NULL,
    number_emergency          int         NULL,
    number_inpatient          int         NULL,
    diag_1                    varchar(10) NULL,
    diag_2                    varchar(10) NULL,
    diag_3                    varchar(10) NULL,
    number_diagnoses          int         NULL,
    max_glu_serum             varchar(10) NULL,
    A1Cresult                 varchar(10) NULL,
    metformin                 varchar(10) NULL,
    repaglinide               varchar(10) NULL,
    nateglinide               varchar(10) NULL,
    chlorpropamide            varchar(10) NULL,
    glimepiride               varchar(10) NULL,
    acetohexamide             varchar(10) NULL,
    glipizide                 varchar(10) NULL,
    glyburide                 varchar(10) NULL,
    tolbutamide               varchar(10) NULL,
    pioglitazone              varchar(10) NULL,
    rosiglitazone             varchar(10) NULL,
    acarbose                  varchar(10) NULL,
    miglitol                  varchar(10) NULL,
    troglitazone              varchar(10) NULL,
    tolazamide                varchar(10) NULL,
    examide                   varchar(10) NULL,
    citoglipton               varchar(10) NULL,
    insulin                   varchar(10) NULL,
    [glyburide-metformin]     varchar(10) NULL,
    [glipizide-metformin]     varchar(10) NULL,
    [glimepiride-pioglitazone] varchar(10) NULL,
    [metformin-rosiglitazone] varchar(10) NULL,
    [metformin-pioglitazone]  varchar(10) NULL,
    [change]                  varchar(10) NULL,
    diabetesMed               varchar(10) NULL,
    readmitted                varchar(10) NULL,
    readmit_30                int         NULL,   -- int, not bit, so SUM() works
    diag_group                varchar(30) NULL,
    age_lo                    int         NULL,
    age_group                 varchar(10) NULL,
    prior_visits              int         NULL,
    prior_inpatient_band      varchar(10) NULL,   -- text: holds 0, 1, 2, 3+
    los_band                  varchar(20) NULL,
    med_band                  varchar(20) NULL,
    a1c_status                varchar(20) NULL,
    a1c_tested                int         NULL,
    med_change                varchar(20) NULL,
    discharge_group           varchar(50) NULL
);
GO

-- Load the CSV. Needs SQL Server 2017 or newer (check with SELECT @@VERSION).
-- On older versions, replace FORMAT = 'CSV' with ROWTERMINATOR = '\n'
BULK INSERT dbo.diabetic_features
FROM 'C:\Temp\diabetic_features.csv'
WITH (
    FORMAT = 'CSV',
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    KEEPNULLS,
    TABLOCK
);
GO

-- Validation: compare with pandas
--   len(df), df["readmit_30"].sum(), df["number_emergency"].sum(), df["number_emergency"].max()
SELECT COUNT(*)                                   AS total_rows,
       SUM(readmit_30)                            AS readmits,
       SUM(CAST(number_emergency AS bigint))      AS sum_emergency,
       MAX(number_emergency)                      AS max_emergency
FROM dbo.diabetic_features;

-- Expect 4 groups: 0, 1, 2, 3+  (and no NULL group)
SELECT prior_inpatient_band, COUNT(*) AS n,
       MIN(number_inpatient) AS min_val, MAX(number_inpatient) AS max_val
FROM dbo.diabetic_features
GROUP BY prior_inpatient_band
ORDER BY prior_inpatient_band;
SELECT COUNT(*)                                           AS patients,
       SUM(readmit_30)                                    AS readmitted_30d,
       CAST(100.0 * SUM(readmit_30) / COUNT(*) AS decimal(5,2)) AS readmit_rate_pct,
       CAST(AVG(time_in_hospital * 1.0) AS decimal(5,2))  AS avg_los_days,
       CAST(AVG(num_medications * 1.0)  AS decimal(5,1))  AS avg_medications
FROM dbo.diabetic_features;
GO

CREATE OR ALTER VIEW dbo.vw_driver_summary AS
WITH long_form AS (
    SELECT 'Age group' AS dimension, CAST(age_group AS nvarchar(50)) AS [level],
           CAST(age_lo AS int) AS sort_key, readmit_30
    FROM dbo.diabetic_features
    UNION ALL
    SELECT 'Primary diagnosis', CAST(diag_group AS nvarchar(50)), NULL, readmit_30
    FROM dbo.diabetic_features
    UNION ALL
    SELECT 'Prior inpatient visits', CAST(prior_inpatient_band AS nvarchar(50)),
           CAST(number_inpatient AS int), readmit_30
    FROM dbo.diabetic_features
    UNION ALL
    SELECT 'Discharge destination', CAST(discharge_group AS nvarchar(50)), NULL, readmit_30
    FROM dbo.diabetic_features
    UNION ALL
    SELECT 'Length of stay', CAST(los_band AS nvarchar(50)), CAST(time_in_hospital AS int), readmit_30
    FROM dbo.diabetic_features
    UNION ALL
    SELECT 'Medication load', CAST(med_band AS nvarchar(50)), CAST(num_medications AS int), readmit_30
    FROM dbo.diabetic_features
    UNION ALL
    SELECT 'HbA1c testing', CAST(a1c_status AS nvarchar(50)), NULL, readmit_30
    FROM dbo.diabetic_features
    UNION ALL
    SELECT 'Medication change', CAST(med_change AS nvarchar(50)), NULL, readmit_30
    FROM dbo.diabetic_features
),
agg AS (
    SELECT dimension, [level],
           MIN(sort_key)  AS sort_key,
           COUNT(*)       AS patients,
           SUM(readmit_30) AS readmits
    FROM long_form
    GROUP BY dimension, [level]
)
SELECT dimension,
       [level],
       sort_key,
       patients,
       readmits,
       CAST(100.0 * readmits / patients AS decimal(5,2)) AS rate_pct,
       CAST(100.0 * readmits / patients
            - 100.0 * SUM(readmits) OVER (PARTITION BY dimension)
                    / SUM(patients) OVER (PARTITION BY dimension) AS decimal(6,2)) AS gap_vs_overall_pp,
       CAST(100.0 * readmits / SUM(readmits) OVER (PARTITION BY dimension) AS decimal(5,1)) AS share_of_readmits_pct
FROM agg;
GO

SELECT dimension, [level], patients, readmits, rate_pct, gap_vs_overall_pp, share_of_readmits_pct
FROM dbo.vw_driver_summary
ORDER BY dimension, sort_key, rate_pct DESC;

SELECT TOP 15 dimension, [level], patients, readmits, rate_pct, gap_vs_overall_pp, share_of_readmits_pct
FROM dbo.vw_driver_summary
WHERE patients >= 300
ORDER BY gap_vs_overall_pp DESC;

SELECT TOP 10 dimension, [level], patients, readmits, rate_pct, gap_vs_overall_pp, share_of_readmits_pct
FROM dbo.vw_driver_summary
WHERE patients >= 300
ORDER BY gap_vs_overall_pp ASC;

SELECT a1c_status,
       med_change,
       COUNT(*) AS patients,
       CAST(100.0 * SUM(readmit_30) / COUNT(*) AS decimal(5,2)) AS rate_pct
FROM dbo.diabetic_features
GROUP BY a1c_status, med_change
ORDER BY a1c_status, med_change;

WITH segments AS (
    SELECT diag_group,
           prior_inpatient_band,
           COUNT(*)        AS patients,
           SUM(readmit_30) AS readmits
    FROM dbo.diabetic_features
    GROUP BY diag_group, prior_inpatient_band
    HAVING COUNT(*) >= 100
)
SELECT TOP 10
       RANK() OVER (ORDER BY 1.0 * readmits / patients DESC) AS rnk,
       diag_group,
       prior_inpatient_band,
       patients,
       readmits,
       CAST(100.0 * readmits / patients AS decimal(5,2)) AS rate_pct
FROM segments
ORDER BY rnk;