from datetime import datetime, timezone, timedelta, date

def validate_date_format(date_str, date_format):
    pass

def get_current_utc_timestamp(date_format_str):
    # return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return datetime.now(timezone.utc).strftime(date_format_str)

def get_current_utc_iso_timestamp():
    return datetime.now(timezone.utc).isoformat()

def format_date_for_filename():
    pass

# def parse_date_formats(date_string):
#     return {
#         "full": "%Y-%m-%d %H:%M:%S",
#         "year_month_day": "%Y-%m-%d",
#         "day_month_year": "%d/%m/%Y",
#         "month_day_year": "%m-%d-%Y",
#         "long": "%B %d, %Y"
#     }