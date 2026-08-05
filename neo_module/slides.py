# neo_module/slides.py
from .cache import load_cache, save_cache, should_fetch
from .fetch import fetch_neo_data, fetch_donki_data
from .formatters import get_sorted_asteroids, format_asteroid_slide, get_donki_slides
from ascii_presenter import AsciiPresenter, MODULE_BANNERS, MODULE_COLORS

presenter = AsciiPresenter()

_NEO_COLOR       = MODULE_COLORS["neo"]
_HAZARD_COLOR    = MODULE_COLORS["hazardous"]
_NEO_BANNER      = MODULE_BANNERS["neo"]
_HAZARD_BANNER   = MODULE_BANNERS["hazardous"]


def _convert_text_slide(slide, default_title="NEO", color=None, alert=False,
                        banner=None):
    """
    Convert a slide dict that has type=='text' into one or more ASCII-framed slides
    produced by AsciiPresenter.make_text_slide.
    """
    content = slide.get("content", "") if isinstance(slide, dict) else str(slide)
    title = slide.get("title") if isinstance(slide, dict) else None

    if not title:
        if "\n" in content:
            first, rest = content.split("\n", 1)
            first = first.strip()
            if first and len(first) <= (presenter.screen_width - 4):
                title = first
                body = rest.strip()
            else:
                title = default_title
                body = content
        else:
            title = default_title
            body = content
    else:
        body = content

    return presenter.make_text_slide(title, body, color=color, alert=alert,
                                     banner=banner)


def _emit_slide_list_into(slide_list, out_list, default_title="NEO",
                          color=None, alert=False, banner=None):
    """
    Take slide_list (list of slides from existing formatters)
    and append converted slides into out_list. Text slides are converted using
    _convert_text_slide; non-text slides (images) are appended unchanged.
    """
    for s in slide_list:
        if not isinstance(s, dict):
            out_list.extend(presenter.make_text_slide(default_title, str(s),
                                                      color=color, alert=alert,
                                                      banner=banner))
            continue

        stype = s.get("type")
        if stype == "text":
            out_list.extend(_convert_text_slide(s, default_title=default_title,
                                                color=color, alert=alert,
                                                banner=banner))
        else:
            out_list.append(s)


def _is_meteor_image_slide(s):
    """
    Heuristic to detect the meteor image slide that format_asteroid_slide used to append.
    Looks for typical keys and 'meteor' in the path/filename.
    """
    if not isinstance(s, dict):
        return False
    if s.get("type") != "image":
        return False
    # check common keys that may contain the meteor image path/identifier
    for key in ("path", "image", "url"):
        val = s.get(key)
        if isinstance(val, str) and "meteor" in val.lower():
            return True
    # fallback: allow explicit tag
    if s.get("tag") == "meteor" or s.get("alt", "").lower().find("meteor") != -1:
        return True
    return False


def get_neo_slides():
    """
    Fetch NEO + DONKI data (with caching) and return slides:
      - text slides converted to ASCII framed slides
      - image slides preserved
    Meteor image (if any) is shown only once, after hazardous asteroid slides.
    DONKI titles GST/FLR will be renamed.
    """
    if should_fetch():
        try:
            print("Fetching fresh space data...")
            data = {}
            data.update(fetch_neo_data())
            data.update(fetch_donki_data())
            save_cache(data)
        except Exception as e:
            print(f"API fetch failed: {e}")
            data = load_cache()
    else:
        data = load_cache()

    if not data:
        return presenter.make_text_slide("NEO Monitor", "No space data available.")

    hazardous, non_hazardous = get_sorted_asteroids(data)
    slides = []
    deferred_meteor_slide = None

    # Process hazardous asteroids first; capture meteor image and emit it once later
    if hazardous:
        first_hazardous = True
        for a in hazardous:
            fmt_slides = format_asteroid_slide(a)
            asteroid_title = f"Asteroid {a.get('name', '')}"
            for s in fmt_slides:
                if _is_meteor_image_slide(s):
                    if deferred_meteor_slide is None:
                        deferred_meteor_slide = s
                    continue
                # Hazardous slides: red-orange color, alert border, banner on first
                banner = _HAZARD_BANNER if first_hazardous else None
                if not isinstance(s, dict):
                    slides.extend(presenter.make_text_slide(
                        asteroid_title, str(s),
                        color=_HAZARD_COLOR, alert=True, banner=banner,
                    ))
                elif s.get("type") == "text":
                    slides.extend(_convert_text_slide(
                        s, default_title=asteroid_title,
                        color=_HAZARD_COLOR, alert=True, banner=banner,
                    ))
                else:
                    slides.append(s)
                first_hazardous = False
    else:
        slides.extend(presenter.make_text_slide(
            "NEO Monitor", "0 hazardous asteroids detected.",
            color=_NEO_COLOR, banner=_NEO_BANNER,
        ))
        first_neo = True
        for a in non_hazardous[:3]:
            fmt_slides = format_asteroid_slide(a)
            banner = _NEO_BANNER if first_neo else None
            _emit_slide_list_into(
                fmt_slides, slides,
                default_title=f"Asteroid {a.get('name', '')}",
                color=_NEO_COLOR, banner=banner,
            )
            first_neo = False

    # Emit the deferred meteor image once, after all hazardous slides
    if deferred_meteor_slide is not None:
        slides.append(deferred_meteor_slide)

    # DONKI slides: rename GST/FLR in content if present
    donki_slides = get_donki_slides(data)
    normalized_donki = []
    for s in donki_slides:
        if isinstance(s, dict) and s.get("type") == "text":
            content = s.get("content", "")
            if content.startswith("GST Event"):
                content = content.replace("GST Event", "Geomagnetic Storm", 1)
            elif content.startswith("FLR Event"):
                content = content.replace("FLR Event", "Solar Flare", 1)
            s = dict(s)
            s["content"] = content
        normalized_donki.append(s)

    _emit_slide_list_into(normalized_donki, slides, default_title="DONKI",
                          color=_NEO_COLOR)

    return slides


if __name__ == "__main__":
    for s in get_neo_slides():
        if isinstance(s, dict) and s.get("type") == "text":
            print(s["content"])
        else:
            print(s)
