# weather_module/slides.py
import requests
from datetime import datetime, timezone
from . import logic
import timezone_config
from ascii_presenter import AsciiPresenter
from api_keys import OWM_API_KEY
# Initialize presenter (32x12 characters by default)
presenter = AsciiPresenter()


def get_weather(lat, lon):
    """Fetch current weather and short-term forecast from OpenWeatherMap."""
    try:
        # --- Current weather ---
        current_url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=imperial"
        )
        current_data = requests.get(current_url, timeout=10).json()

        temp = current_data["main"]["temp"]
        feels = current_data["main"]["feels_like"]
        humidity = current_data["main"]["humidity"]
        pressure = current_data["main"]["pressure"]
        wind_speed = current_data["wind"]["speed"]
        wind_dir = current_data["wind"].get("deg", 0)
        desc = current_data["weather"][0]["description"].capitalize()

        # Convert sunrise/sunset to timezone_config.LOCAL_TZ
        sunrise_local = datetime.fromtimestamp(
            current_data["sys"]["sunrise"], tz=timezone.utc
        ).astimezone(timezone_config.LOCAL_TZ)
        sunset_local = datetime.fromtimestamp(
            current_data["sys"]["sunset"], tz=timezone.utc
        ).astimezone(timezone_config.LOCAL_TZ)
        daylight_hours = (sunset_local - sunrise_local).seconds / 3600

        # --- Forecast (next few entries, ~3-hour intervals) ---
        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast?"
            f"lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=imperial"
        )
        forecast_data = requests.get(forecast_url, timeout=10).json()

        forecast_summaries = []
        for item in forecast_data.get("list", [])[:4]:  # next ~12 hours
            dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc).astimezone(timezone_config.LOCAL_TZ)
            w = item["weather"][0]["description"].capitalize()
            t = item["main"]["temp"]
            ws = item["wind"]["speed"]
            forecast_summaries.append(f"{dt:%a %I:%M %p}: {w}, {t:.0f}°F, wind {ws:.0f} mph")

        return {
            "current": (
                f"{desc}, {temp:.1f}°F (feels {feels:.1f}°F)\n"
                f"Humidity {humidity}%  Pressure {pressure} hPa\n"
                f"Wind {wind_speed:.1f} mph @ {wind_dir}°"
            ),
            "forecast": forecast_summaries,
            "sunrise_local": sunrise_local.strftime("%I:%M %p %Z"),
            "sunset_local": sunset_local.strftime("%I:%M %p %Z"),
            "daylight_hours": round(daylight_hours, 2),
        }

    except Exception as e:
        return {"error": str(e)}


def get_aqi(lat, lon):
    """Fetch Air Quality Index from the OpenWeatherMap Air Pollution API."""
    try:
        url = (
            f"http://api.openweathermap.org/data/2.5/air_pollution?"
            f"lat={lat}&lon={lon}&appid={OWM_API_KEY}"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        entry = r.json()["list"][0]
        aqi = entry["main"]["aqi"]
        components = entry["components"]
        aqi_labels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
        return {
            "aqi": aqi,
            "label": aqi_labels.get(aqi, "Unknown"),
            "pm2_5": components.get("pm2_5", 0.0),
            "pm10":  components.get("pm10",  0.0),
            "o3":    components.get("o3",    0.0),
        }
    except Exception as e:
        print(f"[weather_module] AQI fetch error: {e}")
        return None


def get_nws_alerts(lat, lon):
    """Fetch active NWS severe weather alerts. US coverage only; returns [] elsewhere."""
    try:
        url = f"https://api.weather.gov/alerts/active?point={lat:.4f},{lon:.4f}"
        r = requests.get(url, headers={"User-Agent": "nature-oracle/1.0"}, timeout=10)
        r.raise_for_status()
        features = r.json().get("features", [])
        alerts = []
        for feat in features[:3]:
            props = feat.get("properties", {})
            event = props.get("event", "Alert")
            headline = props.get("headline") or props.get("description", "")
            headline = headline[:120] if headline else ""
            alerts.append(f"{event}\n{headline}" if headline else event)
        return alerts
    except Exception:
        return []

(lat, lon):
    """Return a list of weather slides framed with ASCII boxes in the specified order."""
    slides = []

    # --- 0. NWS Severe Weather Alerts (prepended if any active) ---
    for alert in get_nws_alerts(lat, lon):
        slides.extend(presenter.make_text_slide("! WEATHER ALERT", alert))

    # Fetch weather
    weather_data = get_weather(lat, lon)
    if "error" in weather_data:
        slides.extend(presenter.make_text_slide("WEATHER ERROR", weather_data["error"]))
        return slides

    # --- 1. Current conditions ---
    slides.extend(presenter.make_text_slide("WEATHER", weather_data["current"]))

    # --- 2. Air Quality ---
    aqi_data = get_aqi(lat, lon)
    if aqi_data:
        aqi_text = (
            f"AQI: {aqi_data['aqi']} ({aqi_data['label']})"
            f"\nPM2.5: {aqi_data['pm2_5']:.1f}  PM10: {aqi_data['pm10']:.1f}"
            f"\nOzone: {aqi_data['o3']:.1f} ug/m3"
        )
        slides.extend(presenter.make_text_slide("AIR QUALITY", aqi_text))

    # --- 3. Forecast details ---
    if weather_data.get("forecast"):
        for entry in weather_data["forecast"]:
            slides.extend(presenter.make_text_slide("FORECAST", entry))
    else:
        slides.extend(presenter.make_text_slide("FORECAST", "No forecast data available."))

    # --- 4. Season + Astronomical Event ---
    today = datetime.now(timezone_config.LOCAL_TZ).date()
    season, start, end, next_event = logic.season_dates(today)
    percent = logic.season_progress(start, end, today)
    days_until = (end - today).days

    season_event_text = (
        f"{season}\n{presenter._progress_bar(percent)}\n"
        f"Next astronomical event: {next_event} in {days_until} days"
    )
    slides.extend(presenter.make_text_slide("SEASON & EVENT", season_event_text))

    # --- 5. Daylight info ---
    daylight_text = (
        f"Daylight hours: {weather_data['daylight_hours']} hrs\n"
        f"Sunrise: {weather_data['sunrise_local']}\n"
        f"Sunset:  {weather_data['sunset_local']}"
    )
    slides.extend(presenter.make_text_slide("DAYLIGHT", daylight_text))

    return slides


# For quick debugging
if __name__ == "__main__":
    LAT, LON = 44.5161, -88.0903
    for s in get_weather_slides(LAT, LON):
        print(s["content"] if s.get("type") == "text" else s)
