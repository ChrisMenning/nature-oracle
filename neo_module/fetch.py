import requests
from datetime import datetime, timedelta
from secrets import NASA_API_KEY

def fetch_neo_data():
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={NASA_API_KEY}"
    r = requests.get(url)
    r.raise_for_status()
    return {"neo": r.json()}

def fetch_donki_data():
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    base_url = "https://api.nasa.gov/DONKI"
    events = {}
    for event_type in ["GST", "FLR"]:
        url = f"{base_url}/{event_type}?startDate={start_date}&endDate={end_date}&api_key={NASA_API_KEY}"
        try:
            r = requests.get(url)
            r.raise_for_status()
            events[event_type] = r.json()
        except Exception as e:
            print(f"Failed to fetch {event_type}: {e}")
            events[event_type] = []
    return {"donki": events}
