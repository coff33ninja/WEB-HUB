from nicegui import ui
import sqlite3
import validators
import os
import time
import requests
from scripts.radioscraper import scrape_radio_stations
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Ensure db and exports folders exist
os.makedirs("db", exist_ok=True)
os.makedirs("exports", exist_ok=True)

def init_db():
    try:
        conn = sqlite3.connect("db/radio.db")
        c = conn.cursor()
        # Add favorite column if it doesn't exist
        c.execute("PRAGMA table_info(radio_stations)")
        columns = [info[1] for info in c.fetchall()]
        if "favorite" not in columns:
            c.execute("ALTER TABLE radio_stations ADD COLUMN favorite BOOLEAN DEFAULT 0")
        c.execute(
            "CREATE TABLE IF NOT EXISTS radio_stations (id INTEGER PRIMARY KEY, name TEXT, url TEXT, country TEXT, favorite BOOLEAN DEFAULT 0)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS exports (id INTEGER PRIMARY KEY, timestamp TEXT, file_path TEXT)"
        )
        conn.commit()
    except sqlite3.Error as e:
        ui.notify(f"Database error: {e}", type="negative")
    finally:
        conn.close()

init_db()

def import_to_media():
    from modules.media import add_playlist, load_playlists
    import sqlite3
    add_playlist("Radio Stations", "m3u")
    playlist_id = max(load_playlists().values())
    conn = sqlite3.connect("db/radio.db")
    c = conn.cursor()
    c.execute("SELECT name, url FROM radio_stations")
    for name, url in c.fetchall():
        conn2 = sqlite3.connect("links.db")
        c2 = conn2.cursor()
        c2.execute(
            "INSERT INTO playlist_items (playlist_id, url, title) VALUES (?, ?, ?)",
            (playlist_id, url, name)
        )
        conn2.commit()
        conn2.close()
    conn.close()

def render():
    with ui.card().classes("p-6 bg-gray-800 w-full max-w-3xl mx-auto"):
        ui.label("Streaming Radio").classes("text-3xl font-bold text-gray-100 mb-6")

        # Fetch countries from Radio Garden API
        def get_countries():
            try:
                response = requests.get("http://radio.garden/api/ara/content/places", timeout=10)
                response.raise_for_status()
                data = response.json()
                countries = sorted(set(place.get("country", "Unknown").title() for place in data.get("data", {}).get("list", [])))
                return ["All"] + countries
            except requests.RequestException:
                return ["All", "United States", "United Kingdom", "Canada", "Australia", "Germany", "France", "India", "Brazil", "South Africa", "Japan", "Other"]

        # Search and Filter
        with ui.row().classes("w-full mb-4"):
            search = ui.input("Search Stations").props("clearable").classes("bg-gray-700 text-white rounded w-1/2")
            country = ui.select(
                get_countries(),
                value="All",
                label="Country"
            ).classes("bg-gray-700 text-white rounded w-1/4")
            ui.button(
                "Scrape Stations",
                on_click=lambda: scrape_and_add(country.value)
            ).classes("bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2")

        # Audio Player
        radio = ui.audio(src="").classes("w-full mb-6")

        # Dynamic Stations Dropdown
        with ui.row().classes("w-full mb-4"):
            stations_dropdown = ui.select(
                [],  # Populated dynamically
                label="Select Station",
                value=None
            ).props("clearable").classes("bg-gray-700 text-white rounded w-3/4")
            ui.button(
                "Add Station",
                on_click=lambda: save_station(stations_dropdown.value)
            ).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2")

        # Station List
        stations_list = ui.column().classes("w-full max-h-96 overflow-y-auto")

        async def update_stations_dropdown(selected_country):
            """Populate stations dropdown based on selected country."""
            stations_dropdown.options.clear()
            stations_dropdown.value = None
            if selected_country == "All":
                stations_dropdown.options = []
                stations_dropdown.update()
                return
            try:
                stations = await scrape_radio_stations(selected_country)
                if not stations:
                    ui.notify(f"No stations found for {selected_country}.", type="warning")
                    return
                # Create options as dict with label and value
                stations_dropdown.options = [
                    {
                        "label": f"{name} ({country})",
                        "value": {"name": name, "url": url, "country": country}
                    }
                    for name, url, country in stations
                ]
                stations_dropdown.update()
            except Exception as e:
                ui.notify(f"Error fetching stations: {e}", type="negative")

        async def scrape_and_add(country):
            if country == "All":
                ui.notify("Please select a specific country to scrape.", type="warning")
                return
            with ui.dialog() as dialog, ui.card():
                ui.label("Scraping stations...").classes("text-gray-100")
                ui.spinner().classes("w-8 h-8")
            dialog.open()
            try:
                stations = await scrape_radio_stations(country)
                if not stations:
                    ui.notify(f"No stations found for {country}.", type="warning")
                    return
                conn = sqlite3.connect("db/radio.db")
                c = conn.cursor()
                for station_name, station_url, station_country in stations:
                    if validators.url(station_url):
                        c.execute(
                            "INSERT OR IGNORE INTO radio_stations (name, url, country) VALUES (?, ?, ?)",
                            (station_name, station_url, station_country)
                        )
                conn.commit()
                conn.close()
                refresh_stations()
                await update_stations_dropdown(country)  # Refresh dropdown
                ui.notify(f"Added {len(stations)} stations for {country}.", type="positive")
            except Exception as e:
                ui.notify(f"Error scraping stations: {e}", type="negative")
            finally:
                dialog.close()

        def load_stations(search_query="", country_filter="All"):
            try:
                conn = sqlite3.connect("db/radio.db")
                c = conn.cursor()
                query = "SELECT id, name, url, country, favorite FROM radio_stations"
                params = []
                if search_query or country_filter != "All":
                    query += " WHERE "
                    conditions = []
                    if search_query:
                        conditions.append("name LIKE ?")
                        params.append(f"%{search_query}%")
                    if country_filter != "All":
                        conditions.append("country = ?")
                        params.append(country_filter)
                    query += " AND ".join(conditions)
                c.execute(query, params)
                return c.fetchall()
            except sqlite3.Error as e:
                ui.notify(f"Database error: {e}", type="negative")
                return []
            finally:
                conn.close()

        def save_station(station_data):
            if not station_data:
                ui.notify("Please select a station.", type="warning")
                return
            try:
                conn = sqlite3.connect("db/radio.db")
                c = conn.cursor()
                c.execute(
                    "INSERT OR IGNORE INTO radio_stations (name, url, country) VALUES (?, ?, ?)",
                    (station_data["name"], station_data["url"], station_data["country"])
                )
                conn.commit()
                stations_dropdown.value = None  # Clear selection
                refresh_stations()
                ui.notify(f"Added {station_data['name']}.", type="positive")
            except sqlite3.Error as e:
                ui.notify(f"Database error: {e}", type="negative")
            finally:
                conn.close()

        def delete_station(station_id):
            try:
                conn = sqlite3.connect("db/radio.db")
                c = conn.cursor()
                c.execute("DELETE FROM radio_stations WHERE id = ?", (station_id,))
                conn.commit()
                refresh_stations()
                ui.notify("Station deleted.", type="positive")
            except sqlite3.Error as e:
                ui.notify(f"Database error: {e}", type="negative")
            finally:
                conn.close()

        def play_station(url):
            try:
                radio.set_source(url)
                ui.notify(f"Playing {url}", type="positive")
            except Exception as e:
                ui.notify(f"Error playing station: {e}", type="negative")

        def export_m3u():
            try:
                conn = sqlite3.connect("db/radio.db")
                c = conn.cursor()
                c.execute("SELECT name, url FROM radio_stations")
                stations = c.fetchall()

                timestamp = time.strftime("%Y%m%d_%H%M%S")
                file_path = f"exports/radio_stations_{timestamp}.m3u"
                m3u_content = "#EXTM3U\n"
                for name, url in stations:
                    m3u_content += f"#EXTINF:-1,{name}\n{url}\n"
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(m3u_content)
                
                # Log export in database
                c.execute(
                    "INSERT INTO exports (timestamp, file_path) VALUES (?, ?)",
                    (timestamp, file_path)
                )
                conn.commit()
                conn.close()
                
                ui.notify(f"Exported to {file_path}", type="positive")
                ui.download(file_path, f"radio_stations_{timestamp}.m3u")
            except Exception as e:
                ui.notify(f"Error exporting M3U: {e}", type="negative")

        async def update_all_stations():
            try:
                countries = get_countries()[1:]  # Skip "All"
                for country in countries:
                    stations = await scrape_radio_stations(country)
                    if stations:
                        conn = sqlite3.connect("db/radio.db")
                        c = conn.cursor()
                        # Clear old stations for this country
                        c.execute("DELETE FROM radio_stations WHERE country = ?", (country,))
                        for station_name, station_url, station_country in stations:
                            if validators.url(station_url):
                                c.execute(
                                    "INSERT INTO radio_stations (name, url, country) VALUES (?, ?, ?)",
                                    (station_name, station_url, station_country)
                                )
                        conn.commit()
                        conn.close()
                        print(f"Updated {len(stations)} stations for {country}")
                refresh_stations()
                export_m3u()  # Generate new M3U after update
                ui.notify("Scheduled update completed and M3U exported.", type="positive")
            except Exception as e:
                print(f"Scheduled update error: {e}")
                ui.notify(f"Scheduled update failed: {e}", type="negative")

        def refresh_stations():
            stations_list.clear()
            for station_id, station_name, station_url, station_country, favorite in load_stations(search.value, country.value):
                with stations_list:
                    with ui.row().classes("items-center py-2 border-b border-gray-600"):
                        checkbox = ui.checkbox("Favorite").bind_value_to(favorite).classes("mr-2")
                        ui.label(f"{station_name} ({station_country})").classes("text-gray-100 flex-grow")
                        ui.button(
                            "Play",
                            on_click=lambda u=station_url: play_station(u)
                        ).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-3 py-1 mr-2")
                        ui.button(
                            "Delete",
                            on_click=lambda i=station_id: delete_station(i)
                        ).classes("bg-red-600 hover:bg-red-500 text-white rounded px-3 py-1")
                        
                        def on_favorite_change(value, station_id=station_id):
                            try:
                                conn = sqlite3.connect("db/radio.db")
                                c = conn.cursor()
                                c.execute("UPDATE radio_stations SET favorite = ? WHERE id = ?", (value, station_id))
                                conn.commit()
                            except sqlite3.Error as e:
                                ui.notify(f"Database error: {e}", type="negative")
                            finally:
                                conn.close()
                        
                        checkbox.on("update:model-value", on_favorite_change)

        # Bind search, country, and stations updates
        search.on("update:model-value", refresh_stations)
        country.on("update:model-value", lambda: update_stations_dropdown(country.value))
        ui.button("Export M3U", on_click=export_m3u).classes("bg-purple-600 hover:bg-purple-500 text-white rounded px-4 py-2 mb-4")
        ui.button("Update Now", on_click=update_all_stations).classes("bg-orange-600 hover:bg-orange-500 text-white rounded px-4 py-2 mb-4")
        ui.button("Import to Media Player", on_click=import_to_media).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")
        ui.button("Sync M3U to Drive", on_click=lambda: upload_m3u_to_drive()).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2")
        ui.button("Sync Exports to Drive", on_click=lambda: sync_exports()).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")
        
        # Schedule weekly updates
        scheduler = AsyncIOScheduler()
        scheduler.add_job(update_all_stations, "interval", weeks=1)
        scheduler.start()
        
        refresh_stations()

    def sync_exports():
        from core.gdrive import upload_file_stub
        from pathlib import Path
        for file in Path("exports").iterdir():
            if file.is_file():
                upload_file_stub(str(file))
        ui.notify("Synced all exports to Google Drive.", type="positive")

    def upload_m3u_to_drive():
        from core.gdrive import upload_file_stub
        import glob
        import os
        # Find latest M3U export file
        files = glob.glob("exports/radio_stations_*.m3u")
        if not files:
            ui.notify("No M3U export files found to upload.", type="warning")
            return
        latest_file = max(files, key=os.path.getctime)
        upload_file_stub(latest_file)
        ui.notify(f"Uploaded {os.path.basename(latest_file)} to Google Drive.", type="positive")

# Marketplace metadata
def marketplace_info():
    return {
        "name": "Radio",
        "description": "An online radio streaming module",
        "icon": "radio",
        "author": "nice-web",
        "author_url": "https://github.com/nice-web",
        "license": "MIT",
        "homepage": "https://example.com"
    }
