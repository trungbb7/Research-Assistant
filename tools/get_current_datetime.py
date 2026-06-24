from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_core.tools import tool


@tool
def get_current_datetime() -> str:
    """Get current datetime"""
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d %H:%M:%S")
