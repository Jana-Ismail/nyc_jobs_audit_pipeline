import os
from pathlib import Path

# Project root config
PROJECT_ROOT = Path(__file__).parent.parent

# Logging config
LOG_DIR = PROJECT_ROOT / 'logs'
LOG_FILE_NAME = 'nyc_hiring_audit_pipeline.log'
LOG_FILE_PATH = LOG_DIR / LOG_FILE_NAME

# API CSV endpoints
API_ENDPOINTS = {
    'nyc_job_postings': 'https://data.cityofnewyork.us/resource/kpav-sd4t.csv',
    'nyc_payroll': 'https://data.cityofnewyork.us/resource/k397-673e.csv'
}

# EXCEL FILES
XLS_LIGHTCAST_PATH = PROJECT_ROOT / 'data' / 'raw' / 'lightcast_nyc_job_analytics.xls'

# Converted .xlsx file path
XLSX_LIGHTCAST_PATH = PROJECT_ROOT / 'data' / 'raw' / 'lightcast_nyc_job_analytics.xlsx'

LIGHTCAST_SHEET_NAMES_ALL = [
    'Cover Page', 
    'Parameters', ''
    'Executive Summary', 
    'Advertised Salary', 
    'Advertised Salary Trend', 
    'Full Text Job Posting Samples', 
    'Job Postings Timeseries', 
    'Edu and Experience Breakdown', 
    'Edu and Experience Break... (2)', 
    'Edu and Experience Break... (3)', 
    'Job Postings Top Companies', 
    'Job Postings Top Cities', 
    'Job Postings Top Occs', 
    'Job Postings Top Occs (2)', 
    'Job Postings Top Occs (3)', 
    'Job Postings Job Titles', 
    'Job Postings Top Inds', 
    'Top Specialized Skills', 
    'Top Common Skills', 
    'Top Software Skills', 
    'Top Qualifications (2)', 
    'Appendix A', 
    'Appendix B - Data Sources an...'
]

LIGHTCAST_SHEET_NAMES_METADATA = [
    'Cover Page',
    'Parameters',
    'Executive Summary',
    'Appendix B - Data Sources an...'
]

LIGHTCAST_SHEET_NAMES_TO_KEEP = [
    'Advertised Salary', 
    'Advertised Salary Trend', 
    'Full Text Job Posting Samples', 
    'Job Postings Timeseries', 
    'Edu and Experience Breakdown', 
    'Edu and Experience Break... (2)', 
    'Edu and Experience Break... (3)', 
    'Job Postings Top Companies', 
    'Job Postings Top Cities', 
    'Job Postings Top Occs', 
    'Job Postings Top Occs (2)', 
    'Job Postings Top Occs (3)', 
    'Job Postings Job Titles', 
    'Job Postings Top Inds', 
    'Top Specialized Skills', 
    'Top Common Skills', 
    'Top Software Skills', 
    'Top Qualifications (2)',
    'Appendix A',
]

XLSX_LIGHTCAST_SHEET_NAMES_TO_KEEP = [
    'Job Postings Job Titles',
    'Advertised Salary Trend',
    'Full Text Job Posting Samples',
    'Job Postings Timeseries',
    'Edu and Experience Breakdown',
    'Edu and Experience Break... (2)'
]

# Dataset reference names
DATASET_NAMES = {
    'job_postings': 'nyc_job_postings',
    'payroll': 'nyc_payroll',
    'lightcast': 'lightcast_nyc_job_analytics'
}

# data/raw config
# RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'

# RAW_FILES = {
#     'job_postings': RAW_DATA_DIR / 'nyc_job_postings.csv',
#     'payroll': RAW_DATA_DIR / 'nyc_payroll.csv',
#     'lightcast': RAW_DATA_DIR / 'lightcast_job_analytics.xlsx'
# }

# Testing files and data
# TEST_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
# TEST_RAW_FILES = {
#     'job_postings': TEST_DATA_DIR / 'sample_nyc_job_postings.csv',
#     'payroll': TEST_DATA_DIR / 'sample_nyc_payroll.csv',
#     'lightcast': TEST_DATA_DIR / 'sample_lightcast_job_analytics.xlsx'
# }

# API_SAMPLE_FILES = {
#     'job_postings': RAW_DATA_DIR / 'nyc_job_postings_sample.csv',
#     'payroll': RAW_DATA_DIR / 'nyc_payroll_sample.csv',
#     'lightcast': RAW_DATA_DIR / 'lightcast_job_analytics_sample.xlsx'
# }

# DuckDB config
DATA_DIR = PROJECT_ROOT / 'lakehouse'
DATABASE_NAME = 'nyc_hiring_audit.duckdb'
DATABASE_PATH = DATA_DIR / DATABASE_NAME

BRONZE_SCHEMA = 'bronze'
SILVER_SCHEMA = 'silver'
GOLD_SCHEMA = 'gold'

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