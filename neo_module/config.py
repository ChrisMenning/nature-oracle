import os

CACHE_FILE = "space_cache.json"
LAST_FETCH_FILE = "space_last_fetch.txt"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
METEOR_IMAGE_PATH = os.path.join(BASE_DIR, "meteor.png")
