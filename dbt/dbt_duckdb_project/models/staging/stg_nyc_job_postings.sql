config {{
  materialized = "incremental",
  tags=['staging', 'silver', 'nyc_job_postings']
}

SELECT
  job_id,
  agency,
  business_title,
  career_level,
  salary_range_from,
  salary_range_to,
  salary_frequency,
  DATE(posting_date) AS posting_date

FROM {{ source('bronze', 'nyc_job_postings') }}
WHERE
  EXTRACT(YEAR FROM DATE(posting_date)) IN (2024, 2025)