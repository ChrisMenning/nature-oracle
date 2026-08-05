import time
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import threading
import re

# Default text colour (amber) used when a slide carries no "color" key
DEFAULT_COLOR = (255, 191, 0)

# Spinner frames for the animated refresh screen
_SPINNER_FRAMES = ["|", "/", "─", "\\"]


def fetch_and_fit_image(url, target_width=320, target_height=240):
    """Fetch an image from URL and resize/crop to fit target resolution without distortion."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")

        src_width, src_height = img.size
        src_ratio = src_width / src_height
        target_ratio = target_width / target_height

        if src_ratio > target_ratio:
            # Wider → scale height, crop width
            scale_factor = target_height / src_height
            new_width = int(src_width * scale_factor)
            img = img.resize((new_width, target_height), Image.LANCZOS)
            left = (new_width - target_width) // 2
            img = img.crop((left, 0, left + target_width, target_height))
        else:
            # Taller → scale width, crop height
            scale_factor = target_width / src_width
            new_height = int(src_height * scale_factor)
            img = img.resize((target_width, new_height), Image.LANCZOS)
            top = (new_height - target_height) // 2
            img = img.crop((0, top, target_width, top + target_height))

        return img

    except Exception as e:
        print(f"[SlideshowHandler] Failed to fetch/fit image: {e}")
        return Image.new("RGB", (target_width, target_height), "black")


class SlideshowHandler:
    def __init__(self, slide_functions, disp, font,
                 screen_width=320, screen_height=240,
                 text_display_time=2.5, image_display_time=3,
                 refresh_interval=900):
        self.slide_functions = slide_functions
        self.disp = disp
        self.font = font
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.text_display_time = text_display_time
        self.image_display_time = image_display_time
        self.refresh_interval = refresh_interval

        self.slides = []
        self.last_refresh = 0
        self.current_index = 0

        self._skip_event = threading.Event()
        self._lock = threading.Lock()

        # Flag set while a background refresh is in progress
        self._refreshing = False

    # ── helpers ──────────────────────────────────────────────────────────────

    def _render_text(self, text, color=None, overlay=None):
        """Render *text* onto a black PIL image and return it.

        Parameters
        ----------
        text : str
            Multi-line string to draw.
        color : tuple | None
            RGB fill colour.  Defaults to DEFAULT_COLOR.
        overlay : callable | None
            Optional ``fn(draw, img)`` called after the text is drawn,
            used to paint progress-dot overlays etc.
        """
        color = color or DEFAULT_COLOR
        img = Image.new("RGB", (self.screen_width, self.screen_height), "black")
        draw = ImageDraw.Draw(img)
        draw.multiline_text((10, 10), text, font=self.font, fill=color)
        if overlay:
            overlay(draw, img)
        return img

    def _dot_overlay(self, total, current):
        """Return an overlay function that paints a progress-dot row.

        Dots are drawn at the bottom of the screen.  Filled dot = current
        slide; hollow dot = other slides.  Only shown when there are
        between 2 and 12 slides (beyond that it gets too crowded).
        """
        if total < 2 or total > 12:
            return None

        DOT_RADIUS = 4
        DOT_SPACING = 12
        DOT_Y = self.screen_height - 12
        color_filled  = DEFAULT_COLOR
        color_hollow  = (80, 60, 0)

        total_width = (total - 1) * DOT_SPACING
        start_x = (self.screen_width - total_width) // 2

        def _draw(draw, img):
            for i in range(total):
                cx = start_x + i * DOT_SPACING
                cy = DOT_Y
                bbox = [cx - DOT_RADIUS, cy - DOT_RADIUS,
                        cx + DOT_RADIUS, cy + DOT_RADIUS]
                fill = color_filled if i == current else color_hollow
                draw.ellipse(bbox, fill=fill)

        return _draw

    # ── slide retrieval ───────────────────────────────────────────────────────

    def get_slides(self):
        now = time.time()
        if not self.slides or (now - self.last_refresh) > self.refresh_interval:
            self._do_refresh()
        return self.slides

    def _do_refresh(self):
        """Fetch all slide functions, showing an animated spinner while loading."""
        print("Refreshing slides...")
        self._refreshing = True

        # Run the actual fetch in a background thread so we can animate
        result_holder = []

        def _fetch():
            slides = []
            for func in self.slide_functions:
                try:
                    slide = func()
                    if slide:
                        if isinstance(slide, list):
                            slides.extend(slide)
                        else:
                            slides.append(slide)
                except Exception as e:
                    print(f"Slide error: {e}")
            if not slides:
                slides = [{"type": "text", "content": "No slides available."}]
            result_holder.append(slides)

        fetch_thread = threading.Thread(target=_fetch, daemon=True)
        fetch_thread.start()

        # Animate spinner on the display while fetching
        frame_idx = 0
        while fetch_thread.is_alive():
            spinner = _SPINNER_FRAMES[frame_idx % len(_SPINNER_FRAMES)]
            refresh_text = (
                f"  Consulting the oracle...\n\n"
                f"         {spinner}"
            )
            img = self._render_text(refresh_text, color=DEFAULT_COLOR)
            self.disp.display(img)
            frame_idx += 1
            time.sleep(0.15)

        fetch_thread.join()

        new_slides = result_holder[0] if result_holder else [
            {"type": "text", "content": "No slides available."}
        ]

        with self._lock:
            self.slides = new_slides
            self.last_refresh = time.time()
            self.current_index = 0

        self._refreshing = False

    # ── interruptible sleep ───────────────────────────────────────────────────

    def _wait_interruptible(self, duration):
        start = time.time()
        while (time.time() - start) < duration:
            if self._skip_event.is_set():
                break
            time.sleep(0.01)

    # ── slide navigation ──────────────────────────────────────────────────────

    def next_slide(self, triggered_by_encoder=False):
        with self._lock:
            if not self.slides:
                return
            self.current_index = (self.current_index + 1) % len(self.slides)
            if triggered_by_encoder:
                self._skip_event.set()

    def prev_slide(self, triggered_by_encoder=False):
        with self._lock:
            if not self.slides:
                return
            self.current_index = (self.current_index - 1) % len(self.slides)
            if triggered_by_encoder:
                self._skip_event.set()

    def restart_slideshow(self):
        with self._lock:
            self.current_index = 0
            self._skip_event.set()

    # ── boot splash ───────────────────────────────────────────────────────────

    def show_splash(self, duration=2.5):
        """Display a boot splash screen for *duration* seconds."""
        splash_lines = [
            "┌──────────────────────────────┐",
            "│                              │",
            "│       NATURE  ORACLE         │",
            "│                              │",
            "│  Consulting the spirits...   │",
            "│                              │",
            "└──────────────────────────────┘",
        ]
        splash_text = "\n".join(splash_lines)
        img = self._render_text(splash_text, color=DEFAULT_COLOR)
        self.disp.display(img)
        time.sleep(duration)

    # ── display ───────────────────────────────────────────────────────────────

    def show_text(self, text, color=None, slide_index=None, total_slides=None):
        """Render a text slide, optionally with progress dots."""
        overlay = None
        if slide_index is not None and total_slides is not None:
            overlay = self._dot_overlay(total_slides, slide_index)

        img = self._render_text(text, color=color, overlay=overlay)
        self.disp.display(img)

        # Duration proportional to content lines
        lines = text.splitlines()
        content_lines = sum(1 for line in lines if re.search(r"[A-Za-z0-9]", line))
        if content_lines == 0:
            content_lines = 1

        self._wait_interruptible(self.text_display_time * content_lines * 0.66)

    def show_image(self, slide):
        img = None
        try:
            if "url" in slide:
                # Remote image URL (string)
                img = fetch_and_fit_image(slide["url"], self.screen_width, self.screen_height)

            elif "image" in slide:
                if isinstance(slide["image"], Image.Image):
                    # Already a PIL image (from slides.py)
                    img = slide["image"].convert("RGB")
                    img = img.resize((self.screen_width, self.screen_height), Image.LANCZOS)
                elif isinstance(slide["image"], str):
                    # Local file path
                    img_path = slide["image"]
                    img = Image.open(img_path).convert("RGB")
                    img = img.resize((self.screen_width, self.screen_height), Image.LANCZOS)

            elif "path" in slide:
                # Legacy: explicit local path
                img_path = slide["path"]
                img = Image.open(img_path).convert("RGB")
                img = img.resize((self.screen_width, self.screen_height), Image.LANCZOS)

            elif "content" in slide and isinstance(slide["content"], Image.Image):
                # Directly an Image object
                img = slide["content"].convert("RGB")
                img = img.resize((self.screen_width, self.screen_height), Image.LANCZOS)

        except Exception as e:
            print(f"[show_image] Image error: {e}")
            img = Image.new("RGB", (self.screen_width, self.screen_height), "black")

        if img is None:
            img = Image.new("RGB", (self.screen_width, self.screen_height), "black")

        self.disp.display(img)
        self._wait_interruptible(self.image_display_time)

    def show_current_slide(self):
        slides = self.get_slides()
        with self._lock:
            idx = self.current_index
            total = len(slides)

        # Guard against empty list or stale index
        if not slides or idx >= total:
            return

        slide = slides[idx]
        if slide["type"] == "text":
            color = slide.get("color", DEFAULT_COLOR)
            self.show_text(
                slide.get("content", ""),
                color=color,
                slide_index=idx,
                total_slides=total,
            )
        elif slide["type"] == "image":
            self.show_image(slide)

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while True:
            self.show_current_slide()
            # Auto-advance only if user hasn't triggered skip
            if not self._skip_event.is_set():
                with self._lock:
                    if self.slides:
                        self.current_index = (self.current_index + 1) % len(self.slides)
            # Clear skip event after handling
            self._skip_event.clear()
