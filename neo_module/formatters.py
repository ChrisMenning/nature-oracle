from datetime import datetime
from .config import METEOR_IMAGE_PATH

def get_time_until(approach_time_str):
    try:
        approach_time = datetime.strptime(approach_time_str, "%Y-%b-%d %H:%M")
        delta = approach_time - datetime.now()
        if delta.total_seconds() < 0:
            return "Already passed"
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        parts = []
        if days > 0: parts.append(f"{days}d")
        if hours > 0: parts.append(f"{hours}h")
        if minutes > 0: parts.append(f"{minutes}m")
        return " ".join(parts) if parts else "Less than a minute"
    except Exception as e:
        print(f"Failed to parse approach time: {approach_time_str}, error: {e}")
        return "Unknown"

def get_sorted_asteroids(data):
    asteroids = []
    for _, objs in data["neo"]["near_earth_objects"].items():
        for obj in objs:
            approach = obj["close_approach_data"][0]
            asteroids.append({
                "name": obj["name"],
                "hazardous": obj["is_potentially_hazardous_asteroid"],
                "distance_km": float(approach["miss_distance"]["kilometers"]),
                "speed_kmh": float(approach["relative_velocity"]["kilometers_per_hour"]),
                "approach_time": approach["close_approach_date_full"],
                "diameter": f"{obj['estimated_diameter']['meters']['estimated_diameter_min']:.0f}-{obj['estimated_diameter']['meters']['estimated_diameter_max']:.0f} m"
            })
    hazardous = sorted([a for a in asteroids if a["hazardous"]], key=lambda x: x["distance_km"])
    non_hazardous = sorted([a for a in asteroids if not a["hazardous"]], key=lambda x: x["distance_km"])
    return hazardous, non_hazardous

def wrap_text_into_slides(text, max_chars=35, max_lines_per_slide=8):
    paragraphs = text.split("\n")
    wrapped_lines = []
    for para in paragraphs:
        words, current_line, current_len = para.split(), [], 0
        for word in words:
            if current_len + len(word) + (1 if current_line else 0) > max_chars:
                wrapped_lines.append(" ".join(current_line))
                current_line, current_len = [word], len(word)
            else:
                current_line.append(word)
                current_len += len(word) + (1 if current_line else 0)
        if current_line: wrapped_lines.append(" ".join(current_line))
        if not para.strip(): wrapped_lines.append("")
    slides = []
    for i in range(0, len(wrapped_lines), max_lines_per_slide):
        slides.append("\n".join(wrapped_lines[i:i + max_lines_per_slide]))
    return slides

def get_donki_slides(data):
    events = data.get("donki", {})
    slides = []
    for etype, items in events.items():
        if not items:
            slides.append({"type": "text", "content": f"No {etype} events detected."})
        else:
            for e in items[:3]:
                date = e.get("startTime") or e.get("time21_5") or e.get("beginTime") or "Unknown date"
                note = e.get("note", "No details")
                title = f"{etype} Event\nDate: {date}"
                for slide_text in wrap_text_into_slides(f"{title}\n\n{note}"):
                    slides.append({"type": "text", "content": slide_text})
    return slides

def format_asteroid_slide(asteroid):
    time_until = get_time_until(asteroid["approach_time"])
    content = (
        f"{'POTENTIALLY HAZARDOUS ASTEROID' if asteroid['hazardous'] else 'Asteroid:'} {asteroid['name']}\n"
        f"Diameter: {asteroid['diameter']}\n"
        f"Miss Distance: {asteroid['distance_km']:.0f} km\n"
        f"Speed: {asteroid['speed_kmh']:.0f} km/h\n"
        f"Time until approach: {time_until}"
    )
    slides = [{"type": "text", "content": s} for s in wrap_text_into_slides(content)]
    if asteroid["hazardous"]:
        slides.append({"type": "image", "path": METEOR_IMAGE_PATH})
    return slides
