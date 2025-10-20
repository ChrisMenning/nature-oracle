# climate_module/config.py

CACHE_FILE = "climate_cache.json"
LAST_FETCH_FILE = "climate_last_fetch.txt"
REFRESH_INTERVAL = 3600     # refresh API call every 1h
API_URL = "https://api.climateclock.world/v2/clock.json"

# Lifeline toggles: set to False to hide a lifeline from slides
LIFELINE_TOGGLES = {
    "actnow": False,
    "loss_damage_g7_debt": False,
    "loss_damage_g20_debt": False,
    "ff_divestment_stand_dot_earth": False,
    "_youth_anxiety": False,
    "end_subsidies": False,
    "regen_agriculture": False
    # add or remove keys as needed
}


#Available lifeline keys: renewables_1, , indigenous_land_1, women_in_parliaments, , , , , , , 