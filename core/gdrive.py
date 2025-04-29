from nicegui import ui
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os
from pathlib import Path
import io
import json
import csv
import sqlite3
from core.settings import load_setting

def export_notes_to_json(filename="notes_export.json"):
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute("SELECT id, title, content, tags FROM notes ORDER BY created_at DESC")
    notes = c.fetchall()
    conn.close()
    notes_list = []
    for note in notes:
        notes_list.append({
            "id": note[0],
            "title": note[1],
            "content": note[2],
            "tags": note[3]
        })
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(notes_list, f, ensure_ascii=False, indent=4)

def export_rss_to_csv(filename="rss_export.csv"):
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute("SELECT id, title, link, published FROM rss ORDER BY published DESC")
    rss_items = c.fetchall()
    conn.close()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "link", "published"])
        for item in rss_items:
            writer.writerow(item)

def export_events_to_json(filename="events_export.json"):
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute("SELECT id, title, date, description FROM events")
    events = c.fetchall()
    conn.close()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([{"id": e[0], "title": e[1], "date": e[2], "description": e[3]} for e in events], f, indent=4)

def sync_selected_modules():
    sync_modules = load_setting("sync_modules", ["notes", "todo", "calendar", "weblinks", "credentials"])
    for module in sync_modules:
        if module == "notes":
            export_notes_to_json()
            upload_file_stub("notes_export.json")
        elif module == "todo":
            from core.todo import export_todos
            export_todos()
        elif module == "calendar":
            export_events_to_json()
            upload_file_stub("events_export.json")
        elif module == "weblinks":
            from core.weblinks import export_weblinks
            export_weblinks()
        elif module == "credentials":
            from core.credentials import export_credentials_to_json
            export_credentials_to_json()
    ui.notify("Selected modules synced to Google Drive", type="positive")

def upload_file_stub(filename):
    creds = None
    SCOPES = ["https://www.googleapis.com/auth/drive.file"]
    DRIVE_FOLDER = "HomepageModules"

    def authenticate():
        nonlocal creds
        if not os.path.exists("token.json"):
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        else:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        return build("drive", "v3", credentials=creds)

    def get_folder_id(service):
        results = (
            service.files()
            .list(
                q=f"name='{DRIVE_FOLDER}' and mimeType='application/vnd.google-apps.folder'",
                fields="files(id)",
            )
            .execute()
        )
        folder = results.get("files", [])
        if not folder:
            file_metadata = {
                "name": DRIVE_FOLDER,
                "mimeType": "application/vnd.google-apps.folder",
            }
            folder = (
                service.files().create(body=file_metadata, fields="id").execute()
            )
            return folder.get("id")
        return folder[0].get("id")

    service = authenticate()
    file_metadata = {"name": filename, "parents": [get_folder_id(service)]}
    media = MediaFileUpload(filename)
    service.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()
    ui.notify(f"Uploaded {filename} to Google Drive", type="positive")

def render():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Google Drive Sync").classes(
            "text-2xl font-semibold text-gray-100 mb-4"
        )
        files_list = ui.list().classes("w-full")

        creds = None
        SCOPES = ["https://www.googleapis.com/auth/drive.file"]
        DRIVE_FOLDER = "HomepageModules"

        def has_credentials():
            return os.path.exists("token.json")

        def authenticate():
            nonlocal creds
            if not has_credentials():
                ui.notify(
                    "Google Drive not connected. Please upload credentials.json and connect.",
                    type="warning",
                )
                return None
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            return build("drive", "v3", credentials=creds)

        def get_folder_id(service):
            results = (
                service.files()
                .list(
                    q=f"name='{DRIVE_FOLDER}' and mimeType='application/vnd.google-apps.folder'",
                    fields="files(id)",
                )
                .execute()
            )
            folder = results.get("files", [])
            if not folder:
                file_metadata = {
                    "name": DRIVE_FOLDER,
                    "mimeType": "application/vnd.google-apps.folder",
                }
                folder = (
                    service.files().create(body=file_metadata, fields="id").execute()
                )
                return folder.get("id")
            return folder[0].get("id")

        def list_files():
            service = authenticate()
            if not service:
                return []
            folder_id = get_folder_id(service)
            results = (
                service.files()
                .list(
                    q=f"'{folder_id}' in parents",
                    fields="files(id, name, mimeType)",
                )
                .execute()
            )
            return results.get("files", [])

        def refresh_files():
            files_list.clear()
            if not has_credentials():
                with files_list:
                    ui.label(
                        "Google Drive not connected. Please upload credentials.json and connect."
                    ).classes("text-red-400")
                return
            for file in list_files():
                with files_list:
                    with ui.row().classes("items-center"):
                        icon = (
                            "📁"
                            if file["mimeType"] == "application/vnd.google-apps.folder"
                            else "📄"
                        )
                        ui.label(f"{icon} {file['name']}").classes("text-gray-100")
                        if file["mimeType"] != "application/vnd.google-apps.folder":
                            ui.button(
                                "Download", on_click=lambda f=file: download_file(f)
                            ).classes(
                                "bg-green-600 hover:bg-green-500 text-white rounded px-2 py-1"
                            )

        def upload_file(e):
            service = authenticate()
            if not service:
                return
            file_metadata = {" tyres": e.name, "parents": [get_folder_id(service)]}
            media = MediaFileUpload(Path("modules") / e.name)
            if not e.name.endswith(".py"):
                ui.notify("Invalid file type. Only .py files are allowed.", type="negative")
                return
            service.files().create(
                body=file_metadata, media_body=media, fields="id"
            ).execute()
            refresh_files()

        def download_file(file):
            service = authenticate()
            if not service:
                return
            request = service.files().get_media(fileId=file["id"])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            with open(Path("modules") / file["name"], "wb") as f:
                f.write(fh.getvalue())
            ui.notify(f"Downloaded {file['name']}", type="positive")
            refresh_files()

        ui.upload(on_upload=upload_file, auto_upload=True).props(
            "accept=.py label=Upload to Drive"
        ).classes("bg-gray-600 text-white rounded mb-2")
        ui.button(
            "Export Notes",
            on_click=lambda: [export_notes_to_json(), upload_file_stub("notes_export.json")],
        ).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")
        ui.button(
            "Export RSS",
            on_click=lambda: [export_rss_to_csv(), upload_file_stub("rss_export.csv")],
        ).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")
        ui.button(
            "Export Events",
            on_click=lambda: [export_events_to_json(), upload_file_stub("events_export.json")],
        ).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")
        ui.button("Refresh", on_click=refresh_files).classes(
            "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2"
        )
        refresh_files()