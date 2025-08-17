import os
from pathlib import Path

# Project root config
PROJECT_ROOT = Path(__file__).parent.parent

# Logging config
LOG_DIR = PROJECT_ROOT / 'logs'
LOG_FILE_NAME = 'nyc_hiring_audit_pipeline.log'
LOG_FILE = LOG_DIR / LOG_FILE_NAME

API_ENDPOINTS = {
    "nyc_jobs": "",
    "nyc_payroll": ""
}

# data/raw config
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
NYC_JOBS_DATA_FILE = DATA_DIR / 'nyc_jobs_data.csv'
NYC_PAYROLL_DATA_FILE = DATA_DIR / 'nyc_payroll_data.csv'
LIGHTCAST_DATA_FILE = DATA_DIR / 'lightcast_data.xlsx'

# DuckDB config
LAKEHOUSE_DATA_DIR = PROJECT_ROOT / 'lakehouse'
DUCKLAKE_PATH = PROJECT_ROOT / 'raw'

FUZZY_MATCHING_THRESHOLDS = {
    "salary_audit": 85,
    "posting_duration_audit": 75
}