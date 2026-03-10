# app/utils/date_utils.py
from datetime import datetime, date, timezone
from dateutil import parser
from dateutil.relativedelta import relativedelta

def safe_to_datetime(date_obj) -> datetime:
    """Convert date/datetime ke datetime dengan aman."""
    if date_obj is None:
        return datetime.now(timezone.utc)

    if isinstance(date_obj, datetime):
        return date_obj

    try:
        if hasattr(date_obj, "strftime"):
             return datetime.combine(date_obj, datetime.min.time())
        else:
             return datetime.combine(date_obj, datetime.min.time())
    except (AttributeError, TypeError):
        return datetime.now(timezone.utc)

def safe_format_date(date_obj, format_str: str = "%Y-%m-%d") -> str:
    """Format date dengan aman."""
    if date_obj is None:
        return ""
    try:
        if hasattr(date_obj, "strftime"):
            return date_obj.strftime(format_str)
        else:
            return str(date_obj)
    except (AttributeError, TypeError):
        return str(date_obj) if date_obj else ""

def safe_get_day(date_obj) -> int:
    """Get day dari date dengan aman."""
    if date_obj is None:
        return 1
    try:
        if hasattr(date_obj, "day"):
            return date_obj.day
        else:
            dt = safe_to_datetime(date_obj)
            return dt.day
    except (AttributeError, TypeError):
        return 1

def safe_relativedelta_operation(date_obj, delta_months: int):
    """Safe operation untuk relativedelta dengan date/datetime."""
    dt = safe_to_datetime(date_obj)
    return dt + relativedelta(months=delta_months)

def parse_xendit_datetime(iso_datetime_str: str) -> datetime:
    """Parse format ISO 8601 dari Xendit (e.g. 2020-01-01T00:00:00.000Z)."""
    try:
        return parser.isoparse(iso_datetime_str)
    except Exception:
        return datetime.now(timezone.utc)
