# timezone_config.py
from zoneinfo import ZoneInfo
import requests

def get_local_timezone():
    """
    Determine local timezone based on IP.
    Falls back to UTC if detection fails.
    """
    try:
        res = requests.get("http://ip-api.com/json/", timeout=5)
        data = res.json()
        tz_name = data.get("timezone", "UTC")
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("UTC")

# Initialize a global tz object
LOCAL_TZ = get_local_timezone()
