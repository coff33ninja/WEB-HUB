from nicegui import ui
import sqlite3
from datetime import datetime
import calendar
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from core.credentials import get_credentials
import os

def init_db():
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, title TEXT, date TEXT, description TEXT, recurrence TEXT DEFAULT '')"
    )
    c.execute("PRAGMA table_info(events)")
    columns = [info[1] for info in c.fetchall()]
    if "recurrence" not in columns:
        c.execute("ALTER TABLE events ADD COLUMN recurrence TEXT DEFAULT ''")
    conn.commit()
    conn.close()

init_db()

def render():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Calendar").classes("text-2xl font-semibold text-gray-100 mb-4")
        current_date = datetime.now()
        year = ui.number("Year", value=current_date.year, min=2000, max=2100).classes(
            "bg-gray-600 text-white rounded w-24 mr-2"
        )
        month = ui.select(
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            value=current_date.month,
            label="Month",
        ).classes("bg-gray-600 text-white rounded w-32")
        calendar_grid = ui.grid(columns=7).classes("w-full mb-4")
        events_list = ui.list().classes("w-full")

        def load_events(date_filter):
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute(
                "SELECT id, title, date, description, recurrence FROM events WHERE date LIKE ? OR (recurrence != '' AND (strftime('%Y-%m', date) <= ?))",
                (f"{date_filter}%", f"{date_filter}"),
            )
            events = c.fetchall()
            filtered_events = []
            for event in events:
                eid, title, date_str, desc, recurrence = event
                if recurrence == '':
                    if date_str.startswith(date_filter):
                        filtered_events.append(event)
                else:
                    event_date = datetime.strptime(date_str, "%Y-%m-%d")
                    year_month = datetime.strptime(date_filter, "%Y-%m")
                    if recurrence == 'weekly':
                        if event_date.weekday() == year_month.weekday():
                            filtered_events.append(event)
                        else:
                            filtered_events.append(event)
                    elif recurrence == 'monthly':
                        if event_date.day == year_month.day:
                            filtered_events.append(event)
                        else:
                            filtered_events.append(event)
                    else:
                        filtered_events.append(event)
            return filtered_events

        def save_event(title, date, description, recurrence=''):
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO events (title, date, description, recurrence) VALUES (?, ?, ?, ?)",
                (title, date, description, recurrence),
            )
            conn.commit()
            conn.close()

        def delete_event(event_id):
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute("DELETE FROM events WHERE id = ?", (event_id,))
            conn.commit()
            conn.close()
            refresh_events()

        def render_calendar():
            calendar_grid.clear()
            cal = calendar.monthcalendar(year.value, month.value)
            with calendar_grid:
                for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                    ui.label(day).classes("text-gray-400 font-semibold text-center")
                for week in cal:
                    for day in week:
                        if day == 0:
                            ui.label("").classes("p-2 bg-gray-600 rounded text-center")
                        else:
                            date_str = f"{int(year.value)}-{month.value:02d}-{day:02d}"
                            events = load_events(date_str)
                            with ui.element("div").classes(
                                "p-2 bg-gray-600 rounded text-center"
                            ):
                                ui.label(str(day)).classes("text-gray-100")
                                if events:
                                    ui.label(f"{len(events)} event(s)").classes(
                                        "text-blue-400 text-xs cursor-pointer"
                                    ).on("click", lambda d=date_str: show_day_events(d))

        def show_day_events(date):
            with ui.dialog().props(" persistent") as dialog, ui.card().classes(
                "p-4 bg-gray-700"
            ):
                ui.label(f"Events on {date}").classes("text-gray-100")
                for event_id, title, _, description in load_events(date):
                    with ui.row().classes("items-center"):
                        ui.label(title).classes("text-gray-100")
                        ui.button(
                            "Delete",
                            on_click=lambda e=event_id: [
                                delete_event(e),
                                dialog.close(),
                                refresh_events(),
                            ],
                        ).classes(
                            "bg-red-600 hover:bg-red-500 text-white rounded px-2 py-1"
                        )
                ui.button("Close", on_click=dialog.close).classes(
                    "bg-gray-600 hover:bg-gray-500 text-white rounded px-4 py-2"
                )
            dialog.open()

        def add_event():
            with ui.dialog().props("persistent") as dialog, ui.card().classes(
                "p-4 bg-gray-700"
            ):
                ui.label("New Event").classes("text-gray-100")
                title = (
                    ui.input("Title")
                    .props("clearable")
                    .classes("bg-gray-600 text-white rounded w-full mb-2")
                )
                date = (
                    ui.input(
                        "Date (YYYY-MM-DD)", value=datetime.now().strftime("%Y-%m-%d")
                    )
                    .props("clearable")
                    .classes("bg-gray-600 text-white rounded w-full mb-2")
                )
                description = ui.textarea("Description").classes(
                    "bg-gray-600 text-white rounded w-full mb-2"
                )
                recurrence = ui.select(
                    ["", "weekly", "monthly"], label="Recurrence"
                ).classes("bg-gray-600 text-white rounded w-full mb-2")
                with ui.row():
                    ui.button(
                        "Save",
                        on_click=lambda: [
                            save_event(title.value, date.value, description.value, recurrence.value),
                            refresh_events(),
                            dialog.close(),
                        ],
                    ).classes(
                        "bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2"
                    )
                    ui.button("Cancel", on_click=dialog.close).classes(
                        "bg-gray-600 hover:bg-gray-500 text-white rounded px-4 py-2"
                    )
            dialog.open()

        def refresh_events():
            render_calendar()
            events_list.clear()
            date_filter = f"{int(year.value)}-{month.value:02d}"
            for event_id, title, date, description in load_events(date_filter):
                with events_list:
                    with ui.row().classes("items-center"):
                        ui.label(f"{date} - {title}").classes("text-gray-100")
                        ui.button(
                            "Delete", on_click=lambda e=event_id: delete_event(e)
                        ).classes(
                            "bg-red-600 hover:bg-red-500 text-white rounded px-2 py-1"
                        )

        year.on("change", refresh_events)
        month.on("change", refresh_events)
        ui.button("Add Event", on_click=add_event).classes(
            "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4"
        )
        ui.button("Export to Drive", on_click=export_events).classes(
            "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4"
        )
        ui.button("Sync with Google Calendar", on_click=sync_with_google_calendar).classes(
            "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4"
        )
        refresh_events()

def export_events():
    from core import gdrive
    gdrive.export_events_to_json("events.json")
    gdrive.upload_file_stub("events.json")

def sync_with_google_calendar():
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    creds = None
    creds_list = get_credentials()
    for cred in creds_list:
        id_, name, server_type, url, username, password, token, extra, created_at = cred
        if "google" in name.lower() or "google" in server_type.lower():
            try:
                from google.oauth2.credentials import Credentials
                creds = Credentials(token=token, scopes=SCOPES)
                break
            except Exception:
                continue
    if not creds:
        if os.path.exists("token.json"):
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
    service = build("calendar", "v3", credentials=creds)

    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute("SELECT id, title, date, description, recurrence FROM events")
    local_events = c.fetchall()
    conn.close()

    calendar_id = "primary"
    gcal_events = service.events().list(calendarId=calendar_id, maxResults=100).execute().get("items", [])

    for event_id, title, date, description, recurrence in local_events:
        event = {
            "summary": title,
            "description": description,
            "start": {"date": date},
            "end": {"date": date},
        }
        if recurrence:
            event["recurrence"] = [f"RRULE:FREQ={recurrence.upper()}"]
        service.events().insert(calendarId=calendar_id, body=event).execute()

    for gcal_event in gcal_events:
        title = gcal_event.get("summary", "Untitled")
        date = gcal_event.get("start", {}).get("date")
        description = gcal_event.get("description", "")
        recurrence = gcal_event.get("recurrence", [""])[0].split("FREQ=")[-1] if gcal_event.get("recurrence") else ""
        conn = sqlite3.connect("links.db")
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO events (title, date, description, recurrence) VALUES (?, ?, ?, ?)",
            (title, date, description, recurrence.lower())
        )
        conn.commit()
        conn.close()

    ui.notify("Synced with Google Calendar", type="positive")

marketplace_info = {
    "name": "Calendar",
    "description": "Manage events with a web-based calendar",
    "module": "core.calendar",
    "ui_function": "render"
}