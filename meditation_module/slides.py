# meditation_module/slides.py
from .fetch import fetch_zen_quote, fetch_stoic_quote
from ascii_presenter import AsciiPresenter

# Initialize presenter (32x12 characters by default)
presenter = AsciiPresenter()

def get_meditation_slides():
    """Return a list of meditation slides framed with ASCII boxes."""
    slides = []

    # Zen meditation
    zen_quote, zen_author = fetch_zen_quote()
    if zen_quote:
        zen_text = f"\"{zen_quote}\"\n— {zen_author}"
        slides.extend(presenter.make_text_slide("ZEN MEDITATION", zen_text))

    # Stoic meditation
    stoic_quote, stoic_author = fetch_stoic_quote()
    if stoic_quote:
        stoic_text = f"\"{stoic_quote}\"\n— {stoic_author}"
        slides.extend(presenter.make_text_slide("STOIC MEDITATION", stoic_text))

    return slides


# For testing
if __name__ == "__main__":
    for s in get_meditation_slides():
        print(s["content"] if s.get("type") == "text" else s)
