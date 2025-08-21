{{
    config(
        materialized='view',
        schema='silver'
    )
}}

SELECT
    job_id,
    agency,
    business_title,
    career_level,

    CASE
        WHEN salary_range_from is not null and trim(salary_range_from) != ''
        THEN CAST(REGEXP_REPLACE(salary_range_from, '[$,]', '', 'g') AS DECIMAL(12,2))
        ELSE NULL
    END AS salary_range_from,

    CASE
        WHEN salary_range_to is not null and trim(salary_range_to) != ''
        THEN CAST(REGEXP_REPLACE(salary_range_to, '[$,]', '', 'g') AS DECIMAL(12,2))
        ELSE NULL
    END AS salary_range_to,

    salary_frequency,
    CAST(posting_date AS DATE) AS posting_date,
    CAST(post_until AS DATE) AS post_until,
    CAST(process_date)

    CASE
        WHEN post_until is not null and posting_date is not null
        THEN CAST(post_until AS DATE) - CAST(posting_date AS DATE)
        ELSE {{ var('default_posting_duration_days')}}
    END AS posting_duration,

    trim(lower(business_title)) AS business_title_clean,
    trim(upper(agency)) AS agency_clean,
    posting_date

FROM {{ source('bronze', 'raw_nyc_job_postings')}}
WHERE
    (
        EXTRACT(YEAR FROM CAST(POSTING_DATE AS DATE)) in ({{ var('target_years') | join(', ')}})
    or
    (posting_date is null and EXTRACT(YEAR FROM CAST(process_date AS DATE)) in ({{ var('target_years') | join(', ')}}))
    )
    
AND job_id IS NOT NULL
AND business_title IS NOT NULL
AND agency IS NOT NULL