import os
os.environ["ST7789_GPIO"] = "lgpio"

import st7789 as ST7789
from PIL import Image
import time

# Initialize display
disp = ST7789.ST7789(
    height=240,       # display height
    width=320,        # display width
    rotation=0,
    port=0,
    cs=0,             # or 1 if using CE1
    dc=25,
    rst=27,
    spi_speed_hz=20_000_000
)
disp.begin()

# Get the path of the script's folder
script_dir = os.path.dirname(os.path.realpath(__file__))
image_path = os.path.join(script_dir, "meteor.png")

# Load and resize the image to fit the display
img = Image.open(image_path)
img = img.resize((320, 240))  # resize to match display resolution

# Display the image
disp.display(img)

# Keep it displayed for a while
time.sleep(5)
