import requests
from datetime import datetime
from collections import defaultdict
from .config import ICONIC_PRIORITY

# Taxon cache
taxon_cache = {}

def get_taxon_names(taxon_id):
    """Fetch scientific name and common names for a taxon from iNaturalist"""
    if taxon_id in taxon_cache:
        return taxon_cache[taxon_id]
    taxon_url = f"https://api.inaturalist.org/v1/taxa/{taxon_id}"
    try:
        r = requests.get(taxon_url, timeout=10)
        r.raise_for_status()
        tdata = r.json().get("results", [])
        if tdata:
            taxon = tdata[0]
            sci_name = taxon.get("name", "Unknown")
            common_names = [n.get("name") for n in taxon.get("common_names", []) if n.get("name")]
            preferred_common = taxon.get("preferred_common_name")
            if preferred_common and preferred_common not in common_names:
                common_names.insert(0, preferred_common)
            taxon_cache[taxon_id] = (sci_name, common_names)
            return sci_name, common_names
    except Exception:
        pass
    taxon_cache[taxon_id] = ("Unknown", [])
    return "Unknown", []

def wrap_text_into_slides(text, max_chars=30, max_lines_per_slide=8):
    """Wrap text to max_chars per line, split into slides if > max_lines_per_slide."""
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

def group_and_sort_observations(data):
    """Group observations by iconic taxon and sort them by priority."""
    grouped = defaultdict(list)
    for obs in data:
        taxon = obs.get("taxon")
        if not taxon:
            continue
        taxon_id = taxon.get("id")
        iconic = taxon.get("iconic_taxon_name", "Other")
        obs_date_raw = obs.get("observed_on", "Unknown Date")
        try:
            obs_date = datetime.strptime(obs_date_raw, "%Y-%m-%d").strftime("%b %d")
        except Exception:
            obs_date = "Unknown Date"

        sci_name, common_names = get_taxon_names(taxon_id)
        photo_url = None
        if obs.get("photos"):
            photo_url = obs["photos"][0]["url"].replace("square", "medium")

        grouped[iconic].append({
            "scientific_name": sci_name,
            "common_names": common_names,
            "date": obs_date,
            "photo_url": photo_url
        })

    sorted_groups = sorted(
        grouped.items(),
        key=lambda kv: ICONIC_PRIORITY.get(kv[0], 3)
    )
    return sorted_groups
