"""Module to get .csv files from NYC Open Data API URLs"""
import requests
import os
import io
import polars as pl


from utils.logging_utils import setup_logger
from utils.file_utils import validate_file_exists
from utils.date_utils import get_current_utc_timestamp
from config.settings import API_ENDPOINTS, LOG_FILE_PATH, RAW_FILES, TEST_RAW_FILES

logger = setup_logger(__name__, log_file=LOG_FILE_PATH)

# API URLs
JOB_POSTINGS_API_URL = API_ENDPOINTS["nyc_job_postings"]
PAYROLL_API_URL = API_ENDPOINTS["nyc_payroll"]

# File paths
JOB_POSTINGS_BASE_FILE_PATH = RAW_FILES["job_postings"]
PAYROLL_BASE_FILE_PATH = RAW_FILES["payroll"]

# Test/sample file paths:
TEST_JOB_POSTINGS_FILE_PATH = TEST_RAW_FILES["job_postings"]
TEST_PAYROLL_FILE_PATH = TEST_RAW_FILES["payroll"]

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
        logger.error(
            f"""
                Error downloading rows {offset}-{offset + limit} from {url}.
                Error: {e}
                Moving on to next page: offset={offset + limit}
            """
        )
        return None

    content = response.content if response else None
    if content is not None:
        # Decode a small part to check for header-only
        lines = content.decode('utf-8', errors='ignore').splitlines()
        if len(lines) <= 1:
            # Only header or empty
            return None
    return content

    return response.content if len(response.content) > 1 else None

def save_csv_data(bytes_data, file_path):
    """
    Save CSV data to a file using polars. If appending, do not write header if file exists.
    Assumes 'data' is bytes of a CSV file.
    """
    logger.info(f"Saving data to {file_path}")
    try:
        dataframe = pl.read_csv(io.BytesIO(bytes_data))
        append = validate_file_exists(file_path)

        if append:
            csv_str = dataframe.write_csv(include_header=False)
            with open(file_path, 'a') as csv_file:
                csv_file.write(csv_str)
        else:
            dataframe.write_csv(file_path)
        logger.info(f"Data saved to {file_path} (append={append})")
    
    except Exception as e:
        logger.error(f"Error saving data to {file_path}: {e}")

def main():
    # Manually set offset for testing appending 1000 rows at a time
    offset = 0
    limit = 1000
    max_row = 10000

    timestamp = get_current_utc_timestamp()

    while offset < max_row:
        
        job_postings_bytes = download_nyc_open_data_csv(JOB_POSTINGS_API_URL, limit=limit, offset=offset)

        if job_postings_bytes is not None:
            chunk_rows = f'{offset}-{offset + limit}'
            JOB_POSTINGS_CHUNK_FILE_PATH = f"{JOB_POSTINGS_BASE_FILE_PATH}_{timestamp}_{chunk_rows}.csv"
            save_csv_data(job_postings_bytes, JOB_POSTINGS_CHUNK_FILE_PATH)

        payroll_data = download_nyc_open_data_csv(PAYROLL_API_URL, limit=limit, offset=offset)

        if payroll_data is not None:
            chunk_rows = f'{offset}-{offset + limit}'
            PAYROLL_CHUNK_FILE_PATH = f"{PAYROLL_BASE_FILE_PATH}_{timestamp}_{chunk_rows}.csv"
            save_csv_data(payroll_data, PAYROLL_CHUNK_FILE_PATH)

        offset += limit

if __name__ == "__main__":
    main()