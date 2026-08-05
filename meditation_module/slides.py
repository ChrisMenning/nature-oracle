# meditation_module/slides.py
from .fetch import fetch_zen_quote, fetch_stoic_quote
from ascii_presenter import AsciiPresenter, MODULE_BANNERS, MODULE_COLORS

# Initialize presenter (32x12 characters by default)
presenter = AsciiPresenter()

_MEDITATION_COLOR  = MODULE_COLORS["meditation"]
_MEDITATION_BANNER = MODULE_BANNERS["meditation"]


def get_meditation_slides():
    """Return a list of meditation slides framed with ASCII boxes."""
    slides = []

    def fit_slide(title, text, show_banner=False):
        """Try progressively wider boxes until the content fits."""
        banner = _MEDITATION_BANNER if show_banner else None
        for w, h in [
            (32, 12), (36, 14), (40, 16), (44, 18),
            (48, 20), (52, 22), (56, 24), (60, 26),
        ]:
            p = AsciiPresenter(screen_width=w, screen_height=h)
            result = p.make_text_slide(title, text,
                                       color=_MEDITATION_COLOR,
                                       banner=banner)
            boxed = result[0]["content"]
            lines = boxed.splitlines()
            if all(len(line) <= w for line in lines) and len(lines) <= h:
                # Embed font_size hint for future use
                result[0]["font_size"] = max(16 - (w - 32) // 4, 8)
                return result
        # Fallback: largest box
        p = AsciiPresenter(screen_width=60, screen_height=26)
        result = p.make_text_slide(title, text,
                                   color=_MEDITATION_COLOR,
                                   banner=banner)
        result[0]["font_size"] = 8
        return result

    # Zen meditation — show banner on first quote
    zen_quote, zen_author = fetch_zen_quote()
    if zen_quote:
        zen_text = f'"{zen_quote}"\n— {zen_author}'
        slides.extend(fit_slide("ZEN MEDITATION", zen_text, show_banner=True))

    # Stoic meditation
    stoic_quote, stoic_author = fetch_stoic_quote()
    if stoic_quote:
        stoic_text = f'"{stoic_quote}"\n— {stoic_author}'
        slides.extend(fit_slide("STOIC MEDITATION", stoic_text))

    return slides


# For testing
if __name__ == "__main__":
    for s in get_meditation_slides():
        print(s["content"] if s.get("type") == "text" else s)
