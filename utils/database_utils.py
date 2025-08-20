import duckdb
from pathlib import Path
from utils.file_utils import ensure_directory_exists
from utils.logging_utils import setup_logger
from config.settings import DATABASE_PATH, BRONZE_SCHEMA, SILVER_SCHEMA, GOLD_SCHEMA, LOG_FILE_PATH

logger = setup_logger(__name__, LOG_FILE_PATH)

def setup_lakehouse(db_path=DATABASE_PATH):
    """Initialize the DuckDB lakehouse database with proper schemas."""
    db_path = db_path
    
    ensure_directory_exists(db_path.parent)

    conn = duckdb.connect(str(db_path))

    try:
        # Create schemas if they do not exist
        conn.execute(f'CREATE SCHEMA IF NOT EXISTS {BRONZE_SCHEMA}')
        conn.execute(f'CREATE SCHEMA IF NOT EXISTS {SILVER_SCHEMA}')
        conn.execute(f'CREATE SCHEMA IF NOT EXISTS {GOLD_SCHEMA}')

        logger.info(f"Lakehouse database initialized at {db_path}")
    except Exception as e:
        logger.error(f"Error initializing lakehouse database: {e}")
    finally:
        conn.close()

def get_duckdb_connection(db_path=DATABASE_PATH):
    """Get a DuckDB connection to the lakehouse database."""
    db_path = db_path
    ensure_directory_exists(db_path.parent)
    
    conn = duckdb.connect(str(db_path))
    logger.info(f"Connected to DuckDB database at {db_path}")

    return conn

def install_duckdb_excel_extension(conn):
    """Install and load the DuckDB Excel extension."""
    try:
        conn.execute("INSTALL 'spatial';")
        conn.execute("INSTALL 'excel';")
        
        conn.execute("LOAD 'spatial';")
        conn.execute("LOAD 'excel';")
        logger.info("DuckDB Excel extension installed and loaded.")
    except Exception as e:
        logger.error(f"Error installing/loading DuckDB Excel extension: {e}")
        # raise

def execute_query(query, db_path=DATABASE_PATH):
    """Execute a query and return the results"""
    conn = get_duckdb_connection(db_path)
    try:
        return conn.execute(query).fetchall()
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise
    finally:
        conn.close()

def check_table_exists(schema, table_name, db_path=DATABASE_PATH):
    """Check if a table exists in the given schema"""
    query = f"""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = '{schema}' 
        AND table_name = '{table_name}'
    """
    result = execute_query(query, db_path)
    return result[0][0] > 0

def get_table_row_count(dataset_name):
    """Get current row count for a dataset table"""
    table_name = f"raw_{dataset_name}"
    conn = get_duckdb_connection(DATABASE_PATH)
    
    try:
        if check_table_exists(BRONZE_SCHEMA, table_name, DATABASE_PATH):
            result = conn.execute(f"SELECT COUNT(*) FROM {BRONZE_SCHEMA}.{table_name}").fetchone()
            return result[0] if result else 0
        return 0
    finally:
        conn.close()


def get_latest_batch_info(dataset_name):
    """Get info about the latest batch for a dataset"""
    table_name = f"raw_{dataset_name}"
    conn = get_duckdb_connection(DATABASE_PATH)
    
    try:
        if check_table_exists(BRONZE_SCHEMA, table_name, DATABASE_PATH):
            result = conn.execute(f"""
                SELECT 
                    batch_id,
                    COUNT(*) as row_count,
                    MAX(ingested_at) as last_ingested
                FROM {BRONZE_SCHEMA}.{table_name}
                WHERE batch_id = (
                    SELECT MAX(batch_id) FROM {BRONZE_SCHEMA}.{table_name}
                )
                GROUP BY batch_id
            """).fetchone()
            
            if result:
                return {
                    "batch_id": result[0],
                    "row_count": result[1], 
                    "last_ingested": result[2]
                }
        return None
    finally:
        conn.close()