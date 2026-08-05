import textwrap

# ── Module colour palette (RGB tuples) ──────────────────────────────────────
MODULE_COLORS = {
    "weather":    (255, 191,   0),   # amber  (default)
    "forecast":   (255, 191,   0),
    "season":     (255, 191,   0),
    "daylight":   (255, 191,   0),
    "neo":        (255, 191,   0),   # overridden to red-orange for hazardous
    "hazardous":  (255,  80,   0),   # red-orange
    "climate":    (255, 191,   0),   # overridden per flavour below
    "deadline":   (220,  50,  50),   # red
    "lifeline":   ( 80, 200,  80),   # green
    "meditation": (255, 220, 100),   # soft gold
    "inaturalist":(150, 220,  80),   # warm green
    "default":    (255, 191,   0),   # fallback amber
}

# ── Module header banners (shown on the first slide of each module) ──────────
MODULE_BANNERS = {
    "weather":    "- - ~ ~ - -",
    "forecast":   "- - ~ ~ - -",
    "season":     "* . * . * . *",
    "daylight":   "( sun ) - ( moon )",
    "neo":        ". * . * . * .",
    "hazardous":  "! ! ALERT ! !",
    "climate":    "/\\ /\\ /\\",
    "deadline":   "/\\ /\\ /\\",
    "lifeline":   "~ ~ ~ ~ ~",
    "meditation": "~ ~ ~ ~ ~",
    "inaturalist":"- ~ WILD ~ -",
}


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
    def _box(self, title, body_lines, footer=None, alert=False):
        """Wrap content in an ASCII box with a title bar.

        Parameters
        ----------
        title : str
            Text shown in the title bar.
        body_lines : list[str]
            Lines of body content.
        footer : str | None
            Optional short string embedded in the bottom border
            (e.g. "2/5").  Truncated if too long.
        alert : bool
            When True the top/bottom borders use '!' instead of '─'
            for a hazardous-alert look.
        """
        width = self.screen_width
        fill_char = "!" if alert else "─"

        top = "┌" + fill_char * (width - 2) + "┐"

        # truncate title if too long
        title_str = (title[:width - 4] + "…") if len(title) > width - 4 else title
        title_line = f"│ {title_str}".ljust(width - 1) + "│"
        divider = "├" + fill_char * (width - 2) + "┤"

        lines = []
        for line in body_lines[: self.screen_height - 4]:
            lines.append("│ " + line.ljust(width - 3) + "│")

        # pad empty space
        while len(lines) < self.screen_height - 4:
            lines.append("│" + " " * (width - 2) + "│")

        # Bottom border — optionally embed a footer counter
        if footer:
            # e.g. "└── 2/5 ──────────────────────────┘"
            tag = f" {footer} "
            tag = tag[:width - 4]  # safety truncate
            remaining = width - 2 - len(tag)
            left_dashes  = fill_char * (remaining // 2)
            right_dashes = fill_char * (remaining - len(left_dashes))
            bottom = "└" + left_dashes + tag + right_dashes + "┘"
        else:
            bottom = "└" + fill_char * (width - 2) + "┘"

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
        """Return a progress bar string with label on a separate line."""
        percent = max(0.0, min(100.0, percent))
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percent:.1f}%"

    # ----------------------------
    # Public slide builders
    # ----------------------------

    def make_text_slide(self, title, body, footer=None, alert=False,
                        color=None, banner=None):
        """Build a framed text slide dict.

        Parameters
        ----------
        title : str
        body : str
        footer : str | None
            Short string embedded in the bottom border (e.g. "2/5").
        alert : bool
            Use '!' border characters for hazardous-alert styling.
        color : tuple | None
            RGB fill colour for the text.  Falls back to MODULE_COLORS
            lookup by title keyword, then to the default amber.
        banner : str | None
            One-line decorative string prepended to the body (module
            header banner).  Pass an empty string "" to suppress.
        """
        body_lines = self._wrap(body)

        # Prepend banner if provided
        if banner is not None and banner != "":
            body_lines = [banner, ""] + body_lines

        framed = self._box(title, body_lines, footer=footer, alert=alert)

        slide = {"type": "text", "content": "\n".join(framed)}

        # Resolve colour
        if color is not None:
            slide["color"] = color
        else:
            # Try to infer from title keywords
            title_lower = title.lower()
            for key, col in MODULE_COLORS.items():
                if key in title_lower:
                    slide["color"] = col
                    break

        return [slide]

    def make_progress_slide(self, title, label, percent, footer=None,
                            color=None):
        """Build a framed progress-bar slide."""
        body_lines = self._wrap(label) + ["", self._progress_bar(percent)]
        framed = self._box(title, body_lines, footer=footer)
        slide = {"type": "text", "content": "\n".join(framed)}
        if color is not None:
            slide["color"] = color
        return [slide]
