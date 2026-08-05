# weather_module/slides.py
import requests
from datetime import datetime, timezone
from . import logic
from timezone_config import LOCAL_TZ  # Global timezone
from ascii_presenter import AsciiPresenter, MODULE_BANNERS, MODULE_COLORS
from secrets import OWM_API_KEY
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

        # Convert sunrise/sunset to LOCAL_TZ
        sunrise_local = datetime.fromtimestamp(
            current_data["sys"]["sunrise"], tz=timezone.utc
        ).astimezone(LOCAL_TZ)
        sunset_local = datetime.fromtimestamp(
            current_data["sys"]["sunset"], tz=timezone.utc
        ).astimezone(LOCAL_TZ)
        daylight_hours = (sunset_local - sunrise_local).seconds / 3600

        # --- Forecast (next few entries, ~3-hour intervals) ---
        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast?"
            f"lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=imperial"
        )
        forecast_data = requests.get(forecast_url, timeout=10).json()

        forecast_summaries = []
        for item in forecast_data.get("list", [])[:4]:  # next ~12 hours
            dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc).astimezone(LOCAL_TZ)
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


def get_weather_slides(lat, lon):
    """Return a list of weather slides framed with ASCII boxes in the specified order."""
    slides = []

    # Fetch weather
    weather_data = get_weather(lat, lon)
    if "error" in weather_data:
        slides.extend(presenter.make_text_slide("WEATHER ERROR", weather_data["error"]))
        return slides

    weather_color  = MODULE_COLORS["weather"]
    forecast_color = MODULE_COLORS["forecast"]
    season_color   = MODULE_COLORS["season"]
    daylight_color = MODULE_COLORS["daylight"]

    # --- 1. Current conditions (with weather banner on first slide) ---
    slides.extend(presenter.make_text_slide(
        "WEATHER", weather_data["current"],
        color=weather_color,
        banner=MODULE_BANNERS["weather"],
    ))

    # --- 2. Forecast details ---
    if weather_data.get("forecast"):
        for entry in weather_data["forecast"]:
            slides.extend(presenter.make_text_slide(
                "FORECAST", entry, color=forecast_color,
            ))
    else:
        slides.extend(presenter.make_text_slide(
            "FORECAST", "No forecast data available.", color=forecast_color,
        ))

    # --- 3. Season + Astronomical Event ---
    today = datetime.now(LOCAL_TZ).date()
    season, start, end, next_event = logic.season_dates(today)
    percent = logic.season_progress(start, end, today)
    days_until = (end - today).days

    season_event_text = (
        f"{season}\n{presenter._progress_bar(percent)}\n"
        f"Next event: {next_event} in {days_until} days"
    )
    slides.extend(presenter.make_text_slide(
        "SEASON & EVENT", season_event_text,
        color=season_color,
        banner=MODULE_BANNERS["season"],
    ))

    # --- 4. Daylight info ---
    daylight_text = (
        f"Daylight hours: {weather_data['daylight_hours']} hrs\n"
        f"Sunrise: {weather_data['sunrise_local']}\n"
        f"Sunset:  {weather_data['sunset_local']}"
    )
    slides.extend(presenter.make_text_slide(
        "DAYLIGHT", daylight_text,
        color=daylight_color,
        banner=MODULE_BANNERS["daylight"],
    ))

    return slides


# For quick debugging
if __name__ == "__main__":
    LAT, LON = 44.5161, -88.0903
    for s in get_weather_slides(LAT, LON):
        print(s["content"] if s.get("type") == "text" else s)
