from datetime import date, datetime
from fastapi import FastAPI, Request, Form
from starlette.templating import Jinja2Templates, _TemplateResponse
from fastapi.staticfiles import StaticFiles
from dataclasses import dataclass
import requests, json, os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

client_id = os.getenv("AERISWEATHER_CLIENT_ID")
client_secret = os.getenv("AERISWEATHER_CLIENT_SECRET")
mapbox_token = os.getenv("MAPBOX_TOKEN")


@app.get("/")
def root(request: Request) -> _TemplateResponse:
    """Renders homepage. Gets user location data to load personalized Leaflet map. Loads current time"""
    user_dict = get_user_info()
    current_time = now = datetime.now().strftime("%H:%M")

    context = {
        "request": request,
        "current_time": current_time,
        "user_lat": user_dict["user_lat"],
        "user_long": user_dict["user_long"],
        "user_city": user_dict["user_city"],
        "user_state": user_dict["user_state"],
        "client_id": client_id,
        "client_secret": client_secret,
        "mapbox_token": mapbox_token,
    }

    return templates.TemplateResponse("index.html", context)


@app.post("/")
def get_data(
    request: Request,
    location_input: str = Form(...),
    time_start: str = Form(...),
    user_lat: str = Form(...),
    user_long: str = Form(...),
    user_city: str = Form(...),
    user_state: str = Form(...),
) -> _TemplateResponse:
    """Sumbits an API request to AerisWeather Conditions endpoint, calls another scoring function, and returns result to user via Modal."""

    api_request_string = f"http://api.aerisapi.com/conditions/{location_input}".replace(
        " ", "%20"
    )
    expected_time = str(date.today()) + " " + time_start + ":00"
    fields = "periods.tempF,periods.feelslikeF,periods.humidity,periods.windDir,periods.windSpeedMPH,periods.weather,periods.precipRateIN"
    query_params = {
        "for": expected_time,
        "fields": fields,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    # Make API request
    response = requests.get(api_request_string, params=query_params)
    if response.json()["success"] == True:
        weather_dict = response.json()["response"][0]["periods"][0]

        final_score = score_weather(
            weather_dict["feelslikeF"],
            weather_dict["tempF"],
            weather_dict["windSpeedMPH"],
        )

        # Return time as AM/PM format
        time_am_pm = datetime.strptime(time_start, "%H:%M").strftime("%I:%M %p")

        context = {
            "request": request,
            "final_score": final_score,
            "location_input": location_input,
            "time_am_pm": time_am_pm,
            "temp_f": round(weather_dict["tempF"]),
            "feels_like_f": round(weather_dict["feelslikeF"]),
            "humidity": weather_dict["humidity"],
            "wind_speed_mph": weather_dict["windSpeedMPH"],
            "wind_dir": weather_dict["windDir"],
            "weather": weather_dict["weather"],
            "rain_snow": weather_dict["precipRateIN"],
            "activate_modal": "is-active",
        }

        return templates.TemplateResponse("index.html", context)
    else:
        error_response_dict = response.json()["error"]["description"]

        context = {
            "request": request,
            "error_description": f"Error {response.status_code} - {error_response_dict}",
            "is_danger": "is-danger",
            "current_time": datetime.now().strftime("%H:%M"),
            "user_lat": user_lat,
            "user_long": user_long,
            "user_city": user_city,
            "user_state": user_state,
            "client_id": client_id,
            "client_secret": client_secret,
            "mapbox_token": mapbox_token,
        }

        return templates.TemplateResponse("index.html", context)


def get_user_info() -> dict:
    """Perform API call to ipinfo. Initialize dictionary with dummy values in case call is unsuccessful."""
    user_dict = {
        "user_lat": 1,
        "user_long": 1,
        "user_city": "Unknown",
        "user_state": "Location",
    }
    response = requests.get("http://ipinfo.io/json")
    if response.status_code == 200:
        location_dict = response.json()
        user_dict["user_lat"], user_dict["user_long"] = location_dict["loc"].split(",")
        user_dict["user_city"], user_dict["user_state"] = (
            location_dict["city"],
            location_dict["region"],
        )
        return user_dict
    else:
        return user_dict


def score_weather(feels_like_f: float, temp_f: float, wind_speed_mph: float) -> int:
    """Score weather model using Apparent Temp as a base. Outputs a 1-5 score"""

    # Incorporate wind to heat-index, regardless of humidity
    if temp_f >= 80:
        feels_like_f -= wind_speed_mph

    # Score the model
    if feels_like_f <= 0 or feels_like_f >= 90:
        final_score = 1
    if (0 < feels_like_f < 30) or (80 <= feels_like_f < 90):
        final_score = 2
    if (30 <= feels_like_f < 40) or (73 <= feels_like_f < 80):
        final_score = 3
    if (40 <= feels_like_f < 50) or (60 <= feels_like_f < 73):
        final_score = 4
    if 50 <= feels_like_f < 60:
        final_score = 5

    return final_score
