import time
import os
import json
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import threading
import re

SLIDE_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slide_cache.json")

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

        self._paused = False
        self._font_cache = {}
        self._skip_event = threading.Event()
        self._lock = threading.Lock()

    # --- slide retrieval ---
    def get_slides(self):
        now = time.time()
        if not self.slides or (now - self.last_refresh) > self.refresh_interval:
            print("Refreshing slides...")
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
        non_error = [s for s in slides if "[ERROR]" not in s.get("content", "")]
        if non_error:
            self.slides = slides
            self._save_slide_cache()
        else:
            cached = self._load_slide_cache()
            self.slides = cached if cached else slides
        return self.slides

    # --- interruptible sleep ---
    def _wait_interruptible(self, duration):
        start = time.time()
        while (time.time() - start) < duration:
            if self._skip_event.is_set():
                break
            time.sleep(0.01)

    # --- slide navigation ---
    def next_slide(self, triggered_by_encoder=False):
        with self._lock:
            self.current_index += 1
            if self.current_index >= len(self.slides):
                self.current_index = 0
            if triggered_by_encoder:
                self._skip_event.set()

    def prev_slide(self, triggered_by_encoder=False):
        with self._lock:
            self.current_index -= 1
            if self.current_index < 0:
                self.current_index = len(self.slides) - 1
            if triggered_by_encoder:
                self._skip_event.set()

    def restart_slideshow(self):
        with self._lock:
            self.current_index = 0
            self._skip_event.set()

    def toggle_pause(self):
        with self._lock:
            self._paused = not self._paused
        self._skip_event.set()

    def _show_pause_overlay(self):
        img = Image.new("RGB", (self.screen_width, self.screen_height), "black")
        draw = ImageDraw.Draw(img)
        draw.text(
            (self.screen_width // 4, self.screen_height // 2 - 8),
            "II  PAUSED", font=self.font, fill=(255, 191, 0)
        )
        self.disp.display(img)

    def _get_font(self, size):
        if size not in self._font_cache:
            try:
                self._font_cache[size] = ImageFont.truetype(self.font.path, size)
            except Exception:
                self._font_cache[size] = self.font
        return self._font_cache[size]

    def _save_slide_cache(self):
        try:
            cacheable = [
                s for s in self.slides
                if isinstance(s, dict)
                and s.get("type") == "text"
                and "[ERROR]" not in s.get("content", "")
            ]
            if cacheable:
                with open(SLIDE_CACHE_FILE, "w") as f:
                    json.dump({"timestamp": time.time(), "slides": cacheable}, f)
        except Exception as e:
            print(f"[SlideshowHandler] Cache save failed: {e}")

    def _load_slide_cache(self):
        try:
            if os.path.exists(SLIDE_CACHE_FILE):
                with open(SLIDE_CACHE_FILE) as f:
                    data = json.load(f)
                slides = data.get("slides", [])
                ts = data.get("timestamp", 0)
                age_h = (time.time() - ts) / 3600
                if slides:
                    notice = {
                        "type": "text",
                        "content": f"[OFFLINE]\nShowing cached data\nLast updated {age_h:.0f}h ago"
                    }
                    return [notice] + slides
        except Exception as e:
            print(f"[SlideshowHandler] Cache load failed: {e}")
        return None

    # --- display ---
    def show_text(self, text, font_size=None):
        font = self._get_font(font_size) if font_size else self.font
        img = Image.new("RGB", (self.screen_width, self.screen_height), "black")
        draw = ImageDraw.Draw(img)
        draw.multiline_text((10, 10), text, font=font, fill=(255, 191, 0))
        self.disp.display(img)

        # Split into lines
        lines = text.splitlines()

        # Count only lines that have alphanumeric characters (words, numbers, etc.)
        content_lines = sum(1 for line in lines if re.search(r"[A-Za-z0-9]", line))

        # Fallback: if none matched, at least wait a minimal time
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
        slide = slides[self.current_index]
        if slide["type"] == "text":
            self.show_text(slide.get("content", ""), font_size=slide.get("font_size"))
        elif slide["type"] == "image":
            self.show_image(slide)

    # --- main loop ---
    def run(self):
        _was_paused = False
        while True:
            if self._paused:
                if not _was_paused:
                    self._show_pause_overlay()
                _was_paused = True
                self._skip_event.wait(timeout=0.1)
                self._skip_event.clear()
                continue
            _was_paused = False
            self.show_current_slide()
            # Auto-advance only if user hasn't triggered skip
            if not self._skip_event.is_set():
                with self._lock:
                    self.current_index += 1
                    if self.current_index >= len(self.slides):
                        self.current_index = 0
            # Clear skip event after handling
            self._skip_event.clear()
