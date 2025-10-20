import os
os.environ["ST7789_GPIO"] = "lgpio"

import time
import requests
import st7789
from PIL import ImageFont
from threading import Thread
from rotary_encoder import RotaryEncoder
from slideshow_handler import SlideshowHandler

from inaturalist_module import get_inaturalist_slides
from weather_module import get_weather_slides
from meditation_module import get_meditation_slides
from neo_module import get_neo_slides
from climate_module import get_climate_slides

# === CONFIGURATION ===
SCREEN_WIDTH, SCREEN_HEIGHT = 320, 240
TEXT_DISPLAY_TIME = 3
IMAGE_DISPLAY_TIME = 5
REFRESH_INTERVAL = 900

# === INIT DISPLAY ===
disp = st7789.ST7789(
    height=SCREEN_HEIGHT,
    width=SCREEN_WIDTH,
    rotation=0,
    port=0,
    cs=0,
    dc=25,
    rst=27,
    spi_speed_hz=80_000_000
)
disp.begin()

# === FONT ===
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)

# === LOCATION HANDLER ===
def get_current_location():
    try:
        r = requests.get("https://ipinfo.io/json", timeout=5)
        loc = r.json().get("loc")
        if loc:
            lat, lon = map(float, loc.split(","))
            return lat, lon
    except Exception as e:
        print(f"Could not determine location: {e}")
    return 44.5161, -88.0903

latitude, longitude = get_current_location()
print(f"Using location: {latitude}, {longitude}")

# === SAFE WRAPPER ===
def safe_slide(func):
    """Wrap slide function so exceptions return an error slide."""
    def wrapper():
        try:
            return func()
        except Exception as e:
            return [{"type": "text", "content": f"[ERROR] {e}"}]
    return wrapper

# === SLIDE FUNCTIONS ===
def welcome_slide():
    return [{"type": "text", "content": "Welcome"}]

# Weather slide wrapped in a lambda to pass lat/lon
weather_slide_func = lambda: get_weather_slides(latitude, longitude)

slide_functions = [
     safe_slide(welcome_slide),
     safe_slide(weather_slide_func),        # Unified weather + season + event slides
     safe_slide(get_neo_slides),
     safe_slide(get_climate_slides),
     safe_slide(get_meditation_slides),
     safe_slide(lambda: get_inaturalist_slides(latitude, longitude))

]

# === SLIDESHOW HANDLER ===
slideshow = SlideshowHandler(
    slide_functions=slide_functions,
    disp=disp,
    font=font,
    screen_width=SCREEN_WIDTH,
    screen_height=SCREEN_HEIGHT,
    text_display_time=TEXT_DISPLAY_TIME,
    image_display_time=IMAGE_DISPLAY_TIME,
    refresh_interval=REFRESH_INTERVAL
)

# === ROTARY ENCODER SETUP ===
encoder = RotaryEncoder()
encoder.on_rotate = lambda direction: slideshow.next_slide(triggered_by_encoder=True) \
    if direction == 'CLOCKWISE' else slideshow.prev_slide(triggered_by_encoder=True)
encoder.on_button = lambda: slideshow.restart_slideshow()
encoder.start()

# === RUN SLIDESHOW IN THREAD ===
slideshow_thread = Thread(target=slideshow.run, daemon=True)
slideshow_thread.start()

# Keep main thread alive for encoder
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    encoder.stop()
