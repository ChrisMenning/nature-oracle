import requests
from .config import ZEN_API_URL, STOIC_API_URL

def fetch_quote(api_url, quote_type=None):
    """Fetch a quote from the given API."""
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if quote_type == "stoic":
            return data['data']['quote'], data['data']['author']
        elif isinstance(data, list):
            return data[0]['q'], data[0]['a']
        else:
            return data[0]['q'], data[0]['a']
    except requests.RequestException as e:
        print(f"Error fetching {quote_type or 'quote'}: {e}")
        return None, None

def fetch_zen_quote():
    return fetch_quote(ZEN_API_URL)

def fetch_stoic_quote():
    return fetch_quote(STOIC_API_URL, quote_type="stoic")