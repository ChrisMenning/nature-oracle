import textwrap
from .config import WRAP_WIDTH

def wrap_text(text, width=WRAP_WIDTH):
    """Wrap text to a given width while respecting explicit newlines."""
    wrapped_lines = []
    for line in text.split("\n"):
        wrapped_lines.extend(textwrap.wrap(line, width=width) or [""])
    return "\n".join(wrapped_lines)
