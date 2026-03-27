# moon_module/slides.py
import math
from datetime import date, datetime, timezone
from ascii_presenter import AsciiPresenter

presenter = AsciiPresenter()

# Reference new moon: 6 January 2000 18:14 UTC  (JD 2451550.1)
_KNOWN_NEW_MOON_JD = 2451550.1
_LUNAR_CYCLE = 29.53058867


def _julian_day(d: date) -> float:
    """Convert a date to an approximate Julian Day Number (integer noon value)."""
    a = (14 - d.month) // 12
    y = d.year + 4800 - a
    m = d.month + 12 * a - 3
    return d.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def get_moon_phase(today: date = None):
    """Return a dict describing the current lunar phase."""
    if today is None:
        today = datetime.now(timezone.utc).date()

    jd = _julian_day(today)
    age = (jd - _KNOWN_NEW_MOON_JD) % _LUNAR_CYCLE  # days into current cycle

    if age < 1.85:
        phase_name = "New Moon"
    elif age < 7.38:
        phase_name = "Waxing Crescent"
    elif age < 9.22:
        phase_name = "First Quarter"
    elif age < 14.77:
        phase_name = "Waxing Gibbous"
    elif age < 16.61:
        phase_name = "Full Moon"
    elif age < 22.15:
        phase_name = "Waning Gibbous"
    elif age < 23.99:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"

    illumination = (1 - math.cos(2 * math.pi * age / _LUNAR_CYCLE)) / 2 * 100

    # Days until next full and new moon
    days_to_full = (_LUNAR_CYCLE / 2 - age) % _LUNAR_CYCLE
    days_to_new = (_LUNAR_CYCLE - age) % _LUNAR_CYCLE

    return {
        "phase": phase_name,
        "age_days": age,
        "illumination": illumination,
        "days_to_full": days_to_full,
        "days_to_new": days_to_new,
    }


def get_moon_slides():
    """Return slides describing the current moon phase."""
    info = get_moon_phase()

    phase_text = (
        f"{info['phase']}\n"
        f"Age: {info['age_days']:.1f} days\n"
        f"Illumination: {info['illumination']:.0f}%"
    )
    slides = presenter.make_text_slide("MOON PHASE", phase_text)

    next_text = (
        f"Full Moon in {info['days_to_full']:.0f} days\n"
        f"New Moon in  {info['days_to_new']:.0f} days"
    )
    slides += presenter.make_text_slide("MOON — NEXT EVENTS", next_text)

    return slides


if __name__ == "__main__":
    for s in get_moon_slides():
        print(s["content"])
