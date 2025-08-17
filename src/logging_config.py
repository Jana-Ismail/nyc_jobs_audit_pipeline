"""Module for logging config"""
import logging
from pathlib import Path
import os

os.makedirs('logs', exist_ok=True)
log_file = Path('/Users/janaismail/workspace/de_2025/group_projects/project-4/nyc_jobs_audit_pipeline') / 'logs' / 'app_nyc_hiring_audit.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger = logging.getLogger('logging_config')
    logger.info('Logging is set up and outputting to file correctly.')