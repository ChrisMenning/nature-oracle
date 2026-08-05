# inaturalist_module/slides.py
import requests
from datetime import datetime, timedelta
from ascii_presenter import AsciiPresenter, MODULE_BANNERS, MODULE_COLORS
from .config import DAYS_BACK, RADIUS_KM, MAX_RESULTS
from .utils import group_and_sort_observations
from slideshow_handler import fetch_and_fit_image

presenter = AsciiPresenter()

_INAT_COLOR  = MODULE_COLORS["inaturalist"]
_INAT_BANNER = MODULE_BANNERS["inaturalist"]

def get_inaturalist_slides(latitude, longitude):
    """
    Fetch recent biological sightings and return a list of slides:
    Each slide is a dict with {"type": "text", "content": "..."} or {"type": "image", "url": "..."}.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS_BACK)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    obs_url = "https://api.inaturalist.org/v1/observations"
    obs_params = {
        "lat": latitude,
        "lng": longitude,
        "radius": RADIUS_KM,
        "d1": start_date_str,
        "d2": end_date_str,
        "per_page": MAX_RESULTS,
        "order_by": "observed_on",
        "order": "desc"
    }

    try:
        resp = requests.get(obs_url, params=obs_params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("results", [])
    except Exception:
        data = []

    if not data:
        return [{"type": "text", "content": "No recent observations found.",
                 "color": _INAT_COLOR}]

    sorted_groups = group_and_sort_observations(data)

    slides = []

    # Intro slide — show the module banner here
    intro_text = f"Recent biological sightings within {RADIUS_KM} km"
    slides.extend(presenter.make_text_slide(
        "iNaturalist", intro_text,
        color=_INAT_COLOR,
        banner=_INAT_BANNER,
    ))

    # Observations grouped by iconic taxa
    for iconic_group, species_list in sorted_groups:
        # Taxon summary slide
        taxon_summary = f"{iconic_group} ({len(species_list)} observations)"
        slides.extend(presenter.make_text_slide(
            "iNaturalist", taxon_summary, color=_INAT_COLOR,
        ))

        # Individual species slides (limit 3 per group)
        for s in species_list[:3]:
            names = f" ({', '.join(s['common_names'])})" if s['common_names'] else ""
            text_block = f"{s['scientific_name']}{names} observed on {s['date']}"
            slides.extend(presenter.make_text_slide(
                "iNaturalist", text_block, color=_INAT_COLOR,
            ))

            # Image slide if photo exists
            if s.get("photo_url"):
                img = fetch_and_fit_image(s["photo_url"])
                if img:
                    slides.append({"type": "image", "image": img})

    return slides
