"""File/path operations"""
from pathlib import Path
import pandas as pd

def ensure_directory_exists(path):
    """Create directory if it doesn't exist"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_xlsx_sheet_names(file_path):
    return pd.ExcelFile(file_path).sheet_names

def validate_file_exists(filepath):
    
    return Path(filepath).exists()

def get_file_size(path):
    pass

def clean_filename(filename):
    pass

def archive_file(source, destination):
    pass