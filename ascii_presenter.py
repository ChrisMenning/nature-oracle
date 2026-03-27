import textwrap

class AsciiPresenter:
    def __init__(self, screen_width=32, screen_height=12):
        """
        screen_width/screen_height are in characters, not pixels.
        Tuned for 320x240 LCD using 8x16 font size.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

    # ----------------------------
    # Internal helpers
    # ----------------------------
    def _box(self, title, body_lines):
        """Wrap content in an ASCII box with a title bar."""
        width = self.screen_width
        top = "┌" + "─" * (width - 2) + "┐"

        # truncate title if too long
        title_str = (title[:width - 4] + "…") if len(title) > width - 4 else title
        title_line = f"│ {title_str}".ljust(width - 1) + "│"
        divider = "├" + "─" * (width - 2) + "┤"

        lines = []
        for line in body_lines[: self.screen_height - 4]:
            lines.append("│ " + line.ljust(width - 3) + "│")

        # pad empty space
        while len(lines) < self.screen_height - 4:
            lines.append("│" + " " * (width - 2) + "│")

        bottom = "└" + "─" * (width - 2) + "┘"

        return [top, title_line, divider] + lines + [bottom]

    def _wrap(self, text):
        # Split text by lines, preserve empty lines
        lines = text.split("\n")
        wrapped_lines = []
        for line in lines:
            if not line.strip():
                wrapped_lines.append("")  # preserve blank line
            else:
                wrapped_lines.extend(textwrap.wrap(line, self.screen_width - 4))
        return wrapped_lines

    def _progress_bar(self, percent, width=20):
        filled = int(width * percent / 100)
        return "[" + "█" * filled + "░" * (width - filled) + f"] {percent:.1f}%"

    # ----------------------------
    # Public slide builders
    # ----------------------------
    
    def make_text_slide(self, title, body):
        body_lines = self._wrap(body)
        framed = self._box(title, body_lines)
        return [{"type": "text", "content": "\n".join(framed)}]
        
    def make_progress_slide(self, title, label, percent):
        body_lines = self._wrap(label) + ["", self._progress_bar(percent)]
        framed = self._box(title, body_lines)
        return [{"type": "text", "content": "\n".join(framed)}]


def wrap_text_into_slides(text, max_chars=35, max_lines_per_slide=8):
    """Shared utility: wrap text and split into slide-sized string chunks."""
    paragraphs = text.split("\n")
    wrapped_lines = []
    for para in paragraphs:
        words = para.split()
        current_line, current_len = [], 0
        for word in words:
            if current_len + len(word) + (1 if current_line else 0) > max_chars:
                wrapped_lines.append(" ".join(current_line))
                current_line, current_len = [word], len(word)
            else:
                current_line.append(word)
                current_len += len(word) + (1 if current_line else 0)
        if current_line:
            wrapped_lines.append(" ".join(current_line))
        if not para.strip():
            wrapped_lines.append("")
    slides = []
    for i in range(0, len(wrapped_lines), max_lines_per_slide):
        slides.append("\n".join(wrapped_lines[i:i + max_lines_per_slide]))
    return slides
