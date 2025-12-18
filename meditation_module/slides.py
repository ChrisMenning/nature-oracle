# meditation_module/slides.py
from .fetch import fetch_zen_quote, fetch_stoic_quote
from ascii_presenter import AsciiPresenter

# Initialize presenter (32x12 characters by default)
presenter = AsciiPresenter()

def get_meditation_slides():
    """Return a list of meditation slides framed with ASCII boxes."""
    slides = []

    def fit_slide(title, text, min_width=20, min_height=8):
        # Try decreasing font size (increasing chars per line/box) until it fits
        width, height = presenter.screen_width, presenter.screen_height
        for w, h in [
            (32, 12), (36, 14), (40, 16), (44, 18), (48, 20), (52, 22), (56, 24), (60, 26)
        ]:
            p = AsciiPresenter(screen_width=w, screen_height=h)
            boxed = p.make_text_slide(title, text)[0]["content"]
            lines = boxed.splitlines()
            # If all lines fit within box width and height, accept
            if all(len(line) <= w for line in lines) and len(lines) <= h:
                return [
                    {"type": "text", "content": boxed, "font_size": max(16 - (w-32)//4, 8)}
                ]
        # Fallback: use largest box
        p = AsciiPresenter(screen_width=60, screen_height=26)
        boxed = p.make_text_slide(title, text)[0]["content"]
        return [{"type": "text", "content": boxed, "font_size": 8}]

    # Zen meditation
    zen_quote, zen_author = fetch_zen_quote()
    if zen_quote:
        zen_text = f'"{zen_quote}"\n— {zen_author}'
        slides.extend(fit_slide("ZEN MEDITATION", zen_text))

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
