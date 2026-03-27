# timezone_config.py
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("UTC")

def init_timezone(tz_name: str):
    """Set LOCAL_TZ from a timezone name string (e.g. 'America/Chicago').
    Call once at startup after location is resolved."""
    global LOCAL_TZ
    try:
        LOCAL_TZ = ZoneInfo(tz_name)
    except Exception:
        LOCAL_TZ = ZoneInfo("UTC")
