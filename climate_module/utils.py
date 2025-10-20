import os
import json
import time
from datetime import datetime, timezone

from .config import CACHE_FILE, LAST_FETCH_FILE, REFRESH_INTERVAL

def wrap_text_into_slides(text, max_chars=35, max_lines_per_slide=8):
    """Wrap text into lines and split across multiple slides."""
    paragraphs = text.split("\n")
    wrapped_lines = []
    for para in paragraphs:
        words = para.split()
        current_line = []
        current_len = 0
        for word in words:
            if current_len + len(word) + (1 if current_line else 0) > max_chars:
                wrapped_lines.append(" ".join(current_line))
                current_line = [word]
                current_len = len(word)
            else:
                current_line.append(word)
                current_len += len(word) + (1 if current_line else 0)
        if current_line:
            wrapped_lines.append(" ".join(current_line))
        if not para.strip():
            wrapped_lines.append("")

    slides = []
    for i in range(0, len(wrapped_lines), max_lines_per_slide):
        slides.append("\n".join(wrapped_lines[i:i + max_lines_per_slide]))
    return slides

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return None

def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    with open(LAST_FETCH_FILE, "w") as f:
        f.write(str(int(time.time())))

def should_fetch():
    if not os.path.exists(LAST_FETCH_FILE):
        return True
    with open(LAST_FETCH_FILE, "r") as f:
        last_fetch_time = int(f.read().strip())
    return time.time() - last_fetch_time > REFRESH_INTERVAL

def compute_current_value(lifeline):
    """Compute the up-to-date value of a growing metric."""
    try:
        initial = lifeline.get("initial", 0)
        rate = lifeline.get("rate", 0)
        timestamp = lifeline.get("timestamp")
        if not timestamp:
            return initial
        start_time = datetime.fromisoformat(timestamp)
        now = datetime.now(timezone.utc)
        elapsed_seconds = (now - start_time).total_seconds()
        return round(initial + rate * elapsed_seconds, 2)
    except Exception as e:
        print(f"[climate_module] Growth calc error: {e}")
        return lifeline.get("initial", 0)
