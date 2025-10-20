import time
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import threading
import re

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
            self.slides = slides
            self.last_refresh = now
            self.current_index = 0
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

    # --- display ---
    def show_text(self, text):
        img = Image.new("RGB", (self.screen_width, self.screen_height), "black")
        draw = ImageDraw.Draw(img)
        draw.multiline_text((10, 10), text, font=self.font, fill=(255, 191, 0))
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
            self.show_text(slide.get("content", ""))
        elif slide["type"] == "image":
            self.show_image(slide)

    # --- main loop ---
    def run(self):
        while True:
            self.show_current_slide()
            # Auto-advance only if user hasn't triggered skip
            if not self._skip_event.is_set():
                with self._lock:
                    self.current_index += 1
                    if self.current_index >= len(self.slides):
                        self.current_index = 0
            # Clear skip event after handling
            self._skip_event.clear()
