"""Module to get .csv files from NYC Open Data API URLs"""
import requests
import io
import pandas as pd
import polars as pl
from datetime import datetime, timezone


from utils.logging_utils import setup_logger
from utils.date_utils import get_current_utc_timestamp, get_current_utc_iso_timestamp
from utils.database_utils import (
    get_duckdb_connection, 
    setup_lakehouse, 
    get_latest_batch_info, 
    get_table_row_count, 
    install_duckdb_excel_extension
)
from config.settings import (
    API_ENDPOINTS, 
    LOG_FILE_PATH, 
    DATASET_NAMES, 
    DATA_DIR, 
    DATABASE_PATH, 
    BRONZE_SCHEMA,
    LIGHTCAST_SHEET_NAMES_ALL,
    LIGHTCAST_SHEET_NAMES_TO_KEEP,
    LIGHTCAST_SHEET_NAMES_METADATA,
    XLS_LIGHTCAST_PATH,
    XLSX_LIGHTCAST_PATH
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
        dataframe = pl.read_csv(io.BytesIO(bytes_data), infer_schema_length=1000)

        if dataframe.height == 0:
            logger.warning(f"No data in {dataset_name} chunk {chunk_number}. Skipping save.")
            return False
        
        # Write to duckdb

        ensure_bronze_table_exists(dataset_name, dataframe, api_url)

        table_with_metadata = dataframe.with_columns([
            pl.lit(batch_id).cast(pl.String).alias('batch_id'),
            pl.lit(chunk_number).cast(pl.Int64).alias('chunk_number'),
            pl.lit(datetime.now(timezone.utc).isoformat()).cast(pl.String).alias('ingested_at'),
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

def process_bronze_layer_excel_sheet(xls_file_path, sheet_name):
    """Process sheet with table name in row 1 and headers in row 3"""
    try:
        # Get the table name from row 1, column A
        if sheet_name == 'Advertised Salary':
            table_name_df = pd.read_excel(xls_file_path, sheet_name=sheet_name, header=None, nrows=1)
            table_name = str(table_name_df.iloc[0, 0]) if not table_name_df.empty else sheet_name

        # Read the data with headers in row 3
            df = pd.read_excel(xls_file_path, sheet_name=sheet_name, header=5)
        elif sheet_name in LIGHTCAST_SHEET_NAMES_METADATA:
            table_name = None
            df = pd.read_excel(xls_file_path, sheet_name=sheet_name, header=None)
        else:
            table_name_df = pd.read_excel(xls_file_path, sheet_name=sheet_name, header=None, nrows=1)
            table_name = str(table_name_df.iloc[0, 0]) if not table_name_df.empty else sheet_name
            df = pd.read_excel(xls_file_path, sheet_name=sheet_name, header=2)
        
        if df is None or df.empty:
            logger.warning(f"No data found in sheet {sheet_name} of {xls_file_path}. Creating Empty DataFrame.")
            df = pd.DataFrame()

        return df, table_name
    except Exception as e:
        logger.error(f"Error processing sheet {sheet_name} in {xls_file_path}: {e}")
        # raise
        return sheet_name, pd.DataFrame()  # Return empty DataFrame on error

def convert_xls_to_xlsx(xls_file_path, xlsx_file_path, sheet_names):
    table_names = {}

    with pd.ExcelWriter(xlsx_file_path, engine='openpyxl') as writer:
        for sheet_name in sheet_names:
            df, table_name = process_bronze_layer_excel_sheet(xls_file_path, sheet_name)
            if table_name is not None:
                table_names[sheet_name] = table_name
            
            df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Converted {xls_file_path} to {xlsx_file_path} with sheet: {sheet_name} and table: {table_name}")
    
    logger.info(f'Table names extracted from sheet names: {table_names}')
    return table_names

def create_bronze_table_from_excel_schema(conn, xlsx_file_path, sheet_name, table_name):
    try:
        # Use correct DuckDB range syntax from the docs
        # if sheet_name == 'Advertised Salary':
        #     range_param = "A4:Z"  # From row 5 to end, columns A-Z
        # else:
        #     range_param = "A1:Z"  # From row 3 to end, columns A-Z
        
        sample_query = f'SELECT * FROM read_xlsx("{xlsx_file_path}", sheet="{sheet_name}", header=true, stop_at_empty=true) LIMIT 1'

        result = conn.execute(sample_query).fetchall()
        if not result:
            logger.warning(f"No data found in {sheet_name} of {xlsx_file_path}. Skipping table creation.")
            return False
    
        columns_info = conn.execute(f'DESCRIBE ({sample_query})').fetchall()

        columns = []
        for col_name, col_type, _, _, _, _ in columns_info:
            columns.append(f'"{col_name}" {col_type}')
        
        metadata_columns = [
            'batch_id VARCHAR',
            'ingested_at VARCHAR',
            'api_url VARCHAR',
            'source_dataset VARCHAR',
            'excel_sheet_name VARCHAR',
            'excel_table_name VARCHAR'
        ]

        all_columns = columns + metadata_columns

        # I will carve out a separate util function for this later
        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {BRONZE_SCHEMA}.{table_name} (
                {', '.join(all_columns)}
            )
        """

        conn.execute(create_table_sql)
        logger.info(f"Created bronze table {BRONZE_SCHEMA}.{table_name} from sheet {sheet_name}")
        return True
    except Exception as e:
        logger.error(f"Error creating bronze table {BRONZE_SCHEMA}.{table_name} from sheet {sheet_name}: {e}")
        return False


def load_excel_sheet_to_bronze(conn, xlsx_file_path, sheet_name, table_name, dataset_name, batch_id):
    """Load a single Excel sheet directly into a bronze table using DuckDB."""
    try:
        # Determine header row based on sheet type
        # if sheet_name == 'Advertised Salary':
            # header_row = 6  # Headers in row 6 (0-indexed would be 5, but DuckDB uses 1-indexed)
            # range_param = "A4:Z"  # Start from row 6, go to a large range
        if sheet_name in LIGHTCAST_SHEET_NAMES_METADATA:
            # Skip metadata sheets
            logger.info(f"Skipping metadata sheet '{sheet_name}'")
            return True
        # else:
            # header_row = 3  # Headers in row 3
            # range_param = "A1:Z"  # Start from row 3, go to a large range

        # Create the table if it doesn't exist
        if not create_bronze_table_from_excel_schema(conn, xlsx_file_path, sheet_name, table_name):
            return False
        
        ingested_at = get_current_utc_iso_timestamp()

        insert_sql = f"""
        INSERT INTO {BRONZE_SCHEMA}.{table_name}
        SELECT
            *,
            '{batch_id}' AS batch_id,
            '{ingested_at}' AS ingested_at,
            '{xlsx_file_path}' AS excel_file,
            '{dataset_name}' AS source_dataset,
            '{sheet_name}' AS excel_sheet_name,
            '{table_name}' AS excel_table_name
        FROM read_xlsx('{xlsx_file_path}', sheet='{sheet_name}', header=true, stop_at_empty=true)
        """

        result = conn.execute(insert_sql)

        logger.info(f"Loaded sheet '{sheet_name}' into {BRONZE_SCHEMA}.{table_name}, rows inserted: {result.rowcount}")
        return True
    
    except Exception as e:
        logger.error(f"Error loading sheet '{sheet_name}' into bronze: {e}")
        return False


def load_all_excel_sheets_to_bronze(xlsx_file_path, dataset_name, table_names_map):
    batch_id = get_current_utc_timestamp("%Y%m%d_%H%M%S")

    logger.info(f'Starting Excel sheets ingestion to duckdb bronze schema with batch_id {batch_id}')

    conn = get_duckdb_connection(DATABASE_PATH)
    try:
        install_duckdb_excel_extension(conn)

        for sheet_name, table_name in table_names_map.items():
            if sheet_name in LIGHTCAST_SHEET_NAMES_METADATA:
                logger.info(f"Skipping metadata sheet '{sheet_name}'")
                continue
        
            logger.info(f'Processing sheet {sheet_name} into table {table_name}')

            clean_table_name = table_name.replace(" ", "_").lower()
            raw_table_name = f'raw_{dataset_name}_{clean_table_name}'

            success = load_excel_sheet_to_bronze(
                conn=conn,
                xlsx_file_path=xlsx_file_path,
                sheet_name=sheet_name,
                table_name=raw_table_name,
                dataset_name=dataset_name,
                batch_id=batch_id
            )
    finally:
        conn.close()
    
    summary = {
        "dataset_name": dataset_name,
        "batch_id": batch_id,
        "total_sheets": len(table_names_map),
        "xlsx_file_path": xlsx_file_path
    }

    logger.info(f'Excel ingestion completed: {summary}')

def ingest_api_dataset(api_url, dataset_name, limit=1000, max_rows=None, timeout=200):
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
    return ingest_api_dataset(
        api_url=JOB_POSTINGS_API_URL,
        dataset_name=JOB_POSTINGS_DATASET_NAME,
        limit=limit,
        max_rows=max_rows
    )


def ingest_payroll(limit=1000, max_rows=None):
    """Ingest NYC payroll data"""
    return ingest_api_dataset(
        api_url=PAYROLL_API_URL,
        dataset_name=PAYROLL_DATASET_NAME,
        limit=limit,
        max_rows=max_rows
    )

def main():
    logger.info("Starting data ingestion process")

    setup_lakehouse(DATABASE_PATH)

    logger.info("Ingesting NYC Job Postings data")
    try:
        logger.info(f"Current row count for {JOB_POSTINGS_DATASET_NAME}: {get_table_row_count(JOB_POSTINGS_DATASET_NAME)}")
        
        result = ingest_job_postings(limit=1000, max_rows=10000)
        
        logger.info(f"Ingestion completed: {result}")
        logger.info(f"New row count for {JOB_POSTINGS_DATASET_NAME}: {get_table_row_count(JOB_POSTINGS_DATASET_NAME)}")
        
        # Show batch info
        batch_info = get_latest_batch_info(JOB_POSTINGS_DATASET_NAME)
        if batch_info:
            logger.info(f"Latest batch info: {batch_info}")
            
    except Exception as e:
        logger.error(f"Error in main ingestion process: {e}")
        raise

    logger.info("Ingesting NYC Payroll data ")
    try:
        logger.info(f"Current row count for {PAYROLL_DATASET_NAME}: {get_table_row_count(PAYROLL_DATASET_NAME)}")

        result = ingest_payroll(limit=1000, max_rows=10000)

        logger.info(f"Ingestion completed: {result}")
        logger.info(f"New row count for {PAYROLL_DATASET_NAME}: {get_table_row_count(PAYROLL_DATASET_NAME)}")
        
        # Show batch info
        batch_info = get_latest_batch_info(PAYROLL_DATASET_NAME)
        if batch_info:
            logger.info(f"Latest batch info: {batch_info}")
    except Exception as e:
        logger.error(f"Error in main ingestion process: {e}")
        raise

    logger.info("Ingesting Lightcast Excel data")
    try:
        logger.info("Converting Lightcast .xls to .xlsx")
        table_names = convert_xls_to_xlsx(
            xls_file_path=XLS_LIGHTCAST_PATH,
            xlsx_file_path=XLSX_LIGHTCAST_PATH,
            sheet_names=LIGHTCAST_SHEET_NAMES_ALL
    )
    except Exception as e:
        logger.error(f"Error converting Lightcast .xls to .xlsx: {e}")

    logger.info('Loading Lightcast .xlsx sheets to DuckDB bronze schema')
    try:
        load_all_excel_sheets_to_bronze(
        xlsx_file_path=XLSX_LIGHTCAST_PATH,
        dataset_name='lightcast_analytics',
        table_names_map=table_names
        )
    except Exception as e:
        logger.error(f"Error loading Lightcast Excel sheets to bronze: {e}")

if __name__ == "__main__":
    main()