"""Module to get .csv files from NYC Open Data API URLs"""
import requests

from utils.logging_utils import setup_logger
from config.settings import API_ENDPOINTS, LOG_FILE_PATH, RAW_FILES

logger = setup_logger(__name__, log_file=LOG_FILE_PATH)

# API URLs
JOB_POSTINGS_API_URL = API_ENDPOINTS["nyc_job_postings"]
PAYROLL_API_URL = API_ENDPOINTS["nyc_payroll"]

# File paths
JOB_POSTINGS_FILE_PATH = RAW_FILES["job_postings"]
PAYROLL_FILE_PATH = RAW_FILES["payroll"]

def download_nyc_open_data_csv(url, limit=1000, offset=0, timeout=10):
    logger.info(f"Downloading data from {url} with limit={limit} and offset={offset}")
    params = {
        "$limit": limit,
        "$offset": offset
    }

    try:
        response = requests.get(url, stream=True, params=params, timeout=timeout)
        response.raise_for_status()
        logger.info(f"Successfully downloaded csv data from url: {url}")
    except requests.RequestException as e:
        logger.error(f"Error downloading data from {url}: {e}")

    return response.content if response else None

def save_csv_data(data, file_path):
    try:
        with open(file_path, 'wb') as file:
            file.write(data)
            logger.info(f"Data saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving data to {file_path}: {e}")

def main():
    # limit 10 rows for testing
    job_postings_csv = download_nyc_open_data_csv(JOB_POSTINGS_API_URL, limit=10)
    payroll_csv = download_nyc_open_data_csv(PAYROLL_API_URL, limit=10)
    
    save_csv_data(job_postings_csv, JOB_POSTINGS_FILE_PATH)
    save_csv_data(payroll_csv, PAYROLL_FILE_PATH)

if __name__ == "__main__":
    main()