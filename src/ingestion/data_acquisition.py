"""Module to get .csv files from NYC Open Data API URLs"""
import requests
import io
import polars as pl
from datetime import datetime


from utils.logging_utils import setup_logger
from utils.date_utils import get_current_utc_timestamp
from utils.database_utils import get_duckdb_connection, setup_lakehouse, get_latest_batch_info, get_table_row_count
from config.settings import (
    API_ENDPOINTS, 
    LOG_FILE_PATH, 
    DATASET_NAMES, 
    DATA_DIR, 
    DATABASE_PATH, 
    BRONZE_SCHEMA
)

logger = setup_logger(__name__, log_file=LOG_FILE_PATH)

# API URLs
JOB_POSTINGS_API_URL = API_ENDPOINTS["nyc_job_postings"]
PAYROLL_API_URL = API_ENDPOINTS["nyc_payroll"]

# Dataset names
JOB_POSTINGS_DATASET_NAME = DATASET_NAMES['job_postings']
PAYROLL_DATASET_NAME = DATASET_NAMES['payroll']

def fetch_api_data(api_url, dataset_name, limit=1000, offset=0, timeout=10):
    """Fetch data from API URL and return as bytes."""

    logger.info(f"Downloading {dataset_name} data from {api_url} with limit={limit} and offset={offset}")
    
    params = {
        "$limit": limit,
        "$offset": offset
    }

    try:
        response = requests.get(api_url, stream=True, params=params, timeout=timeout)
        response.raise_for_status()
        logger.info(f"Successfully downloaded data from {api_url}")
    except requests.RequestException as e:
        logger.error(
            f"Error downloading rows {offset}-{offset + limit} from {api_url}. Error: {e}"
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

def ensure_bronze_table_exists(dataset_name, sample_dataframe, api_url):
    """
    Ensure that the bronze table for the given dataset exists.
    If it doesn't, create it using the provided sample dataframe.
    """
    table_name = f'raw_{dataset_name}'

    conn = get_duckdb_connection(DATABASE_PATH)
    try:
        add_metadata_columns = sample_dataframe.with_columns([
            pl.lit(None, dtype=pl.String).alias('batch_id'),
            pl.lit(None, dtype=pl.Int64).alias('chunk_number'),
            pl.lit(None, dtype=pl.String).alias('ingested_at'),
            pl.lit(None, dtype=pl.String).alias('api_url'),
            pl.lit(None, dtype=pl.String).alias('source_dataset')
        ])

        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {BRONZE_SCHEMA}.{table_name} AS 
            SELECT * FROM add_metadata_columns WHERE 1=0
        """)

        logger.info(f"Ensured bronze table {BRONZE_SCHEMA}.{table_name} exists for dataset {dataset_name}")
    except Exception as e:
        logger.error(f"Error ensuring bronze table {BRONZE_SCHEMA}.{table_name} exists: {e}")
        raise
    finally:
        conn.close()

def save_data_to_bronze_schema(bytes_data, dataset_name, api_url, batch_id, chunk_number):
    """
    Save CSV data to bronze schema in the DuckDB lakehouse database
    """
    if bytes_data is None:
        logger.warning(f"No data to save for {dataset_name} chunk {chunk_number}")
        return False

    table_name = f'raw_{dataset_name}'
    # db_path = f'{LAKEHOUSE_BRONZE_DIR}/{dataset_name}/{dataset_name}_{timestamp}_{chunk_info}.duckdb'

    logger.info(f'Saving {dataset_name} chunk {chunk_number} to bronze.{table_name}')

    try:
        dataframe = pl.read_csv(io.BytesIO(bytes_data))

        if dataframe.height == 0:
            logger.warning(f"No data in {dataset_name} chunk {chunk_number}. Skipping save.")
            return False
        
        # Write to duckdb

        ensure_bronze_table_exists(dataset_name, dataframe, api_url)

        table_with_metadata = dataframe.with_columns([
            pl.lit(batch_id).cast(pl.String).alias('batch_id'),
            pl.lit(chunk_number).cast(pl.Int64).alias('chunk_number'),
            pl.lit(datetime.utcnow().isoformat()).cast(pl.String).alias('ingested_at'),
            pl.lit(api_url).cast(pl.String).alias('api_url'),
            pl.lit(dataset_name).cast(pl.String).alias('source_dataset')
        ])

        conn = get_duckdb_connection(DATABASE_PATH)
        try:
            conn.execute(f'INSERT INTO {BRONZE_SCHEMA}.{table_name} SELECT * FROM table_with_metadata')

            row_count = table_with_metadata.height
            logger.info(f"Saved {row_count} rows to {BRONZE_SCHEMA}.{table_name}")
            return True
    
        finally:
            if 'conn' in locals():
                conn.close()

    except Exception as e:
        logger.error(f"Error saving data to {BRONZE_SCHEMA}.{table_name}: {e}")
        raise

def ingest_dataset(api_url, dataset_name, limit=1000, max_rows=None, timeout=200):
    """
    Ingest a complete dataset from API in chunks
    
    Args:
        api_url: API endpoint URL
        dataset_name: Name of the dataset
        limit: Number of rows per chunk
        max_rows: Maximum total rows to fetch (None for all)
        timeout: Request timeout in seconds
    
    Returns:
        dict: Summary of ingestion results
    """
    logger.info(f"Starting ingestion for {dataset_name}")
    
    batch_id = get_current_utc_timestamp("%Y%m%d_%H%M%S")
    offset = 0
    chunk_number = 1
    successful_chunks = 0
    total_rows_ingested = 0
    
    while True:
        # Check if we've reached max_rows limit
        if max_rows and offset >= max_rows:
            logger.info(f"Reached max_rows limit ({max_rows}) for {dataset_name}")
            break
        
        # Fetch chunk data
        chunk_data = fetch_api_data(
            api_url=api_url,
            dataset_name=dataset_name,
            limit=limit,
            offset=offset,
            timeout=timeout
        )
        
        # If no data returned, we've reached the end
        if chunk_data is None:
            logger.info(f"No more data available for {dataset_name} at offset {offset}")
            break
        
        # Save chunk to bronze schema
        success = save_data_to_bronze_schema(
            bytes_data=chunk_data,
            dataset_name=dataset_name,
            api_url=api_url,
            batch_id=batch_id,
            chunk_number=chunk_number
        )
        
        if success:
            successful_chunks += 1
            total_rows_ingested += limit  # Approximate count
        
        # Move to next chunk
        offset += limit
        chunk_number += 1
        
        logger.info(f"Processed chunk {chunk_number - 1} for {dataset_name}")
    
    summary = {
        "dataset_name": dataset_name,
        "batch_id": batch_id,
        "total_chunks": successful_chunks,
        "estimated_rows": total_rows_ingested,
        "api_url": api_url
    }
    
    logger.info(f"Completed ingestion for {dataset_name}: {summary}")
    return summary

def ingest_job_postings(limit=1000, max_rows=None):
    """Ingest NYC job postings data"""
    return ingest_dataset(
        api_url=JOB_POSTINGS_API_URL,
        dataset_name=JOB_POSTINGS_DATASET_NAME,
        limit=limit,
        max_rows=max_rows
    )


def ingest_payroll(limit=1000, max_rows=None):
    """Ingest NYC payroll data"""
    return ingest_dataset(
        api_url=PAYROLL_API_URL,
        dataset_name=PAYROLL_DATASET_NAME,
        limit=limit,
        max_rows=max_rows
    )

def main():
    logger.info("Starting data ingestion process")

    setup_lakehouse(DATABASE_PATH)

    try:
        logger.info(f"Current row count for {JOB_POSTINGS_DATASET_NAME}: {get_table_row_count(JOB_POSTINGS_DATASET_NAME)}")
        
        result = ingest_job_postings(limit=1000, max_rows=6000)
        
        logger.info(f"Ingestion completed: {result}")
        logger.info(f"New row count for {JOB_POSTINGS_DATASET_NAME}: {get_table_row_count(JOB_POSTINGS_DATASET_NAME)}")
        
        # Show batch info
        batch_info = get_latest_batch_info(JOB_POSTINGS_DATASET_NAME)
        if batch_info:
            logger.info(f"Latest batch info: {batch_info}")
            
    except Exception as e:
        logger.error(f"Error in main ingestion process: {e}")
        raise

    

if __name__ == "__main__":
    main()