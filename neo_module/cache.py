import os
import json
from datetime import datetime, timedelta
from .config import CACHE_FILE, LAST_FETCH_FILE

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None

def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    with open(LAST_FETCH_FILE, "w") as f:
        f.write(datetime.now().isoformat())

def should_fetch():
    if not os.path.exists(LAST_FETCH_FILE):
        return True
    with open(LAST_FETCH_FILE, "r") as f:
        last_fetch_time = datetime.fromisoformat(f.read().strip())
    return datetime.now() - last_fetch_time > timedelta(hours=1)
