# climate_module/slides.py
import requests
from datetime import datetime, timezone

from .config import API_URL, LIFELINE_TOGGLES
from .utils import load_cache, save_cache, should_fetch, compute_current_value
from ascii_presenter import AsciiPresenter, MODULE_BANNERS, MODULE_COLORS

# Use the presenter configured to your requested box size
presenter = AsciiPresenter()

_DEADLINE_COLOR  = MODULE_COLORS["deadline"]
_LIFELINE_COLOR  = MODULE_COLORS["lifeline"]
_DEADLINE_BANNER = MODULE_BANNERS["deadline"]
_LIFELINE_BANNER = MODULE_BANNERS["lifeline"]


def fetch_climate_data():
    """Fetch the climate clock modules from the remote API."""
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        return r.json()["data"]["modules"]
    except Exception as e:
        print(f"[climate_module] Fetch error: {e}")
        return None


def format_deadline(timer, show_banner=False):
    """Return framed slides for the main carbon deadline timer."""
    try:
        deadline_str = timer.get("timestamp")
        if not deadline_str:
            return presenter.make_text_slide(
                "CLIMATE - DEADLINE", "No deadline timestamp available.",
                color=_DEADLINE_COLOR,
            )

        deadline_dt = datetime.fromisoformat(deadline_str)
        # Ensure timezone-aware comparison
        if deadline_dt.tzinfo is None:
            deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = deadline_dt - now

        days = delta.days
        years = days // 365
        rem_days = days % 365

        content = f"Carbon Deadline:\n{years} years, {rem_days} days left"
        return presenter.make_text_slide(
            "CLIMATE - DEADLINE", content,
            color=_DEADLINE_COLOR,
            banner=_DEADLINE_BANNER if show_banner else None,
        )

    except Exception as e:
        print(f"[climate_module] Deadline error: {e}")
        return presenter.make_text_slide("CLIMATE - DEADLINE", f"[ERROR] {e}",
                                         color=_DEADLINE_COLOR)


def format_lifeline(key, lifeline, show_banner=False):
    """
    Format a lifeline 'value' module into framed slides.
    Displays an ASCII progress bar when unit is '%'.
    """
    try:
        labels = lifeline.get("labels", [])
        solution_labels = lifeline.get("solution_labels", [])
        unit_labels = lifeline.get("unit_labels", [])

        label = labels[0] if labels else key
        solution = solution_labels[0] if solution_labels else ""
        unit = unit_labels[0] if unit_labels else ""

        value = compute_current_value(lifeline)

        body_lines = []

        # If unit is %, show progress bar instead of raw value
        if unit == "%":
            body_lines.append(label + ":")
            body_lines.append(presenter._progress_bar(value))
        else:
            body_lines.append(f"{label}: {value} {unit}" if unit else f"{label}: {value}")

        # Insert blank line before solution if present
        if solution:
            body_lines.append("")
            body_lines.append(solution)

        body = "\n".join(body_lines)
        title = f"CLIMATE - {label}"
        return presenter.make_text_slide(
            title, body,
            color=_LIFELINE_COLOR,
            banner=_LIFELINE_BANNER if show_banner else None,
        )

    except Exception as e:
        print(f"[climate_module] Lifeline error: {e}")
        return presenter.make_text_slide("CLIMATE - LIFELINE", f"[ERROR] {e}",
                                         color=_LIFELINE_COLOR)


def get_climate_slides():
    """Fetch/cached climate data and build slides (timers + lifelines only)."""
    if should_fetch():
        data = fetch_climate_data()
        if data:
            try:
                save_cache(data)
            except Exception as e:
                print(f"[climate_module] Failed to save cache: {e}")
    else:
        data = load_cache()

    if not data:
        return presenter.make_text_slide("CLIMATE", "No climate data available.")

    slides = []

    # --- Debug: show available lifeline keys ---
    lifeline_keys = [k for k, m in data.items() if m.get("type") == "value" and m.get("flavor") == "lifeline"]
    if lifeline_keys:
        print("[climate_module] Available lifeline keys:", ", ".join(lifeline_keys))
    # -------------------------------------------

    # Iterate modules: timers and lifelines only (newsfeed removed)
    # Show the banner only on the very first slide of each flavour type.
    first_deadline = True
    first_lifeline = True
    for key, module in data.items():
        module_type = module.get("type")
        flavor = module.get("flavor")

        if module_type == "timer" and flavor == "deadline":
            slides.extend(format_deadline(module, show_banner=first_deadline))
            first_deadline = False

        elif module_type == "value" and flavor == "lifeline":
            if LIFELINE_TOGGLES.get(key, True):
                slides.extend(format_lifeline(key, module,
                                              show_banner=first_lifeline))
                first_lifeline = False

    return slides


if __name__ == "__main__":
    for s in get_climate_slides():
        print(s["content"] if s.get("type") == "text" else s)
