import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "space_cache.json")
LAST_FETCH_FILE = os.path.join(BASE_DIR, "space_last_fetch.txt")
METEOR_IMAGE_PATH = os.path.join(BASE_DIR, "meteor.png")
