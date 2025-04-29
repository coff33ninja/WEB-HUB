from nicegui import ui
import requests
import sqlite3
from core.settings import load_setting

def init_db():
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS weather_cities (id INTEGER PRIMARY KEY, city TEXT UNIQUE)"
    )
    conn.commit()
    conn.close()

def save_city(city_name):
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    try:
        c.execute("INSERT OR IGNORE INTO weather_cities (city) VALUES (?)", (city_name,))
        conn.commit()
        ui.notify(f"City '{city_name}' saved to favorites.", type="positive")
    except Exception as e:
        ui.notify(f"Error saving city: {e}", type="negative")
    finally:
        conn.close()

def render():
    init_db()
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Weather").classes("text-2xl font-semibold text-gray-100 mb-4")
        city = (
            ui.input("City")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )
        weather_label = ui.label().classes("text-gray-100")
        forecast_label = ui.label().classes("text-gray-100 mt-4")

        def get_openweathermap_api_key():
            api_keys = load_setting("api_keys", {})
            return api_keys.get("openweathermap", "")

        def fetch_weather():
            try:
                api_key = get_openweathermap_api_key()
                if not api_key:
                    weather_label.set_text("API key not set. Please configure in Settings.")
                    return
                response = requests.get(
                    f"https://api.openweathermap.org/data/2.5/weather?q={city.value}&appid={api_key}"
                )
                data = response.json()
                if response.status_code == 200:
                    weather_label.set_text(
                        f"{data['name']}: {(data['main']['temp'] - 273.15):.1f}°C, {data['weather'][0]['description']}"
                    )
                else:
                    weather_label.set_text(f"Error: {data.get('message', 'Unknown error')}")
            except Exception:
                weather_label.set_text("Error fetching weather").classes("text-red-500")

        def fetch_forecast():
            try:
                api_key = get_openweathermap_api_key()
                if not api_key:
                    forecast_label.set_text("API key not set. Please configure in Settings.")
                    return
                response = requests.get(
                    f"https://api.openweathermap.org/data/2.5/forecast?q={city.value}&appid={api_key}"
                )
                data = response.json()
                if response.status_code == 200:
                    forecast_text = "Forecast:\n"
                    for item in data['list'][:5]:  # Show next 5 forecast entries
                        dt_txt = item['dt_txt']
                        temp_c = item['main']['temp'] - 273.15
                        desc = item['weather'][0]['description']
                        forecast_text += f"{dt_txt}: {temp_c:.1f}°C, {desc}\n"
                    forecast_label.set_text(forecast_text)
                else:
                    forecast_label.set_text(f"Error: {data.get('message', 'Unknown error')}")
            except Exception:
                forecast_label.set_text("Error fetching forecast").classes("text-red-500")

        ui.button("Get Weather", on_click=fetch_weather).classes(
            "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mr-2"
        )
        ui.button("Get Forecast", on_click=fetch_forecast).classes(
            "bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2 mr-2"
        )
        ui.button("Save City", on_click=lambda: save_city(city.value)).classes(
            "bg-indigo-600 hover:bg-indigo-500 text-white rounded px-4 py-2"
        )