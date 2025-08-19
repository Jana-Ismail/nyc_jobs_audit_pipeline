import os
from pathlib import Path

# Project root config
PROJECT_ROOT = Path(__file__).parent.parent

# Logging config
LOG_DIR = PROJECT_ROOT / 'logs'
LOG_FILE_NAME = 'nyc_hiring_audit_pipeline.log'
LOG_FILE_PATH = LOG_DIR / LOG_FILE_NAME

API_ENDPOINTS = {
    'nyc_job_postings': 'https://data.cityofnewyork.us/resource/kpav-sd4t.csv',
    'nyc_payroll': 'https://data.cityofnewyork.us/resource/k397-673e.csv'
}

# data/raw config
RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'

RAW_FILES = {
    'job_postings': RAW_DATA_DIR / 'nyc_job_postings.csv',
    'payroll': RAW_DATA_DIR / 'nyc_payroll.csv',
    'lightcast': RAW_DATA_DIR / 'lightcast_job_analytics.xlsx'
}

# Testing files and data
TEST_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
TEST_RAW_FILES = {
    'job_postings': TEST_DATA_DIR / 'sample_nyc_job_postings.csv',
    'payroll': TEST_DATA_DIR / 'sample_nyc_payroll.csv',
    'lightcast': TEST_DATA_DIR / 'sample_lightcast_job_analytics.xlsx'
}

API_SAMPLE_FILES = {
    'job_postings': RAW_DATA_DIR / 'nyc_job_postings_sample.csv',
    'payroll': RAW_DATA_DIR / 'nyc_payroll_sample.csv',
    'lightcast': RAW_DATA_DIR / 'lightcast_job_analytics_sample.xlsx'
}

# DuckDB config
LAKEHOUSE_DIR = PROJECT_ROOT / 'lakehouse'
DUCKDB_DB = LAKEHOUSE_DIR / 'nyc_audit.duckdb'
# DUCKDB_RAW_PATH = LAKEHOUSE_DATA_DIR / 'raw'
# DUCKDB_SILVER_PATH = LAKEHOUSE_DATA_DIR / 'silver'
# DUCKDB_GOLD_PATH = LAKEHOUSE_DATA_DIR / 'gold'

FUZZY_MATCHING_THRESHOLDS= {
    "job_postings_salary_match": 85,
    "posting_duration_match": 75
}

# Airflow config
# AIRFLOW_CONFIG = {
#     'dag_id': 'nyc_hiring_audit_pipeline',  # Specified in project
#     'schedule_interval': None,  # File-triggered
#     'default_retries': 2,
#     'retry_delay_minutes': 5,
#     'email_on_failure': True,
#     'email_on_retry': False
# }