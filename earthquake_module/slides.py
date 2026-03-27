# earthquake_module/slides.py
import requests
from datetime import datetime, timezone as tz
from ascii_presenter import AsciiPresenter

presenter = AsciiPresenter()

_USGS_URL = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    "?format=geojson&orderby=time&limit=5&minmagnitude=2.5"
    "&maxradiuskm=500"
)


def get_earthquake_slides(latitude, longitude):
    """Return slides of recent M2.5+ earthquakes within 500 km via the USGS FDSNWS API."""
    try:
        url = f"{_USGS_URL}&latitude={latitude}&longitude={longitude}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        features = r.json().get("features", [])
    except Exception as e:
        return presenter.make_text_slide("EARTHQUAKES", f"Could not fetch seismic data:\n{e}")

    if not features:
        return presenter.make_text_slide("EARTHQUAKES", "No significant seismic\nactivity nearby.")

    slides = []
    slides.extend(presenter.make_text_slide(
        "EARTHQUAKES",
        f"{len(features)} recent quake(s)\nwithin 500 km  (M2.5+)"
    ))

    for feat in features:
        props = feat.get("properties", {})
        mag = props.get("mag", "?")
        place = props.get("place", "Unknown location")
        ts = props.get("time", 0) / 1000
        dt = datetime.fromtimestamp(ts, tz=tz.utc).strftime("%b %d %H:%M UTC")
        slides.extend(presenter.make_text_slide(
            "EARTHQUAKES",
            f"M{mag} — {place}\n{dt}"
        ))

    return slides


if __name__ == "__main__":
    for s in get_earthquake_slides(44.5161, -88.0903):
        print(s["content"])
