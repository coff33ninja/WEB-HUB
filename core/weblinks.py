from nicegui import ui
import sqlite3
import requests
from pathlib import Path
import os
import json
import validators
from core.gdrive import upload_file_stub

def init_db():
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS weblinks (id INTEGER PRIMARY KEY, name TEXT, url TEXT, category TEXT)"
    )
    c.execute("PRAGMA table_info(weblinks)")
    columns = [info[1] for info in c.fetchall()]
    if "category" not in columns:
        c.execute("ALTER TABLE weblinks ADD COLUMN category TEXT")
    conn.commit()
    conn.close()

init_db()

def render():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Web Links").classes("text-2xl font-semibold text-gray-100 mb-4")
        weblinks_list = ui.list().classes("w-full")

        def load_weblinks():
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute("SELECT name, url, category FROM weblinks")
            return c.fetchall()

        def save_link(name, url, category):
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO weblinks (name, url, category) VALUES (?, ?, ?)",
                (name, url, category),
            )
            conn.commit()
            conn.close()

        def delete_link(url):
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute("DELETE FROM weblinks WHERE url = ?", (url,))
            conn.commit()
            conn.close()

        def fetch_favicon(url):
            try:
                response = requests.get(f"{url}/favicon.ico", timeout=5)
                if response.status_code == 200:
                    os.makedirs("static", exist_ok=True)
                    favicon_path = (
                        Path("static")
                        / f"{url.replace('http://', '').replace('https://', '').replace('/', '_')}.ico"
                    )
                    with open(favicon_path, "wb") as f:
                        f.write(response.content)
                    return str(favicon_path)
            except Exception:
                return None

        def refresh_weblinks():
            weblinks_list.clear()
            for name, url, category in load_weblinks():
                with weblinks_list:
                    with ui.row().classes("items-center"):
                        favicon = fetch_favicon(url) or "https://via.placeholder.com/16"
                        ui.image(favicon).classes("w-5 h-5 mr-2")
                        ui.link(name, url).props("target=_blank").classes(
                            "text-blue-400 hover:text-blue-300"
                        )
                        ui.label(category).classes("ml-2 text-gray-300 italic")
                        ui.button(
                            "Delete", on_click=lambda u=url: delete_link(u)
                        ).classes(
                            "bg-red-600 hover:bg-red-500 text-white rounded px-2 py-1"
                        )

        def add_link():
            url = url_input.value.strip()
            name = name_input.value.strip() or url
            category = category_input.value.strip()
            if url and validators.url(url):
                save_link(name, url, category)
                refresh_weblinks()
                url_input.value = ""
                name_input.value = ""
                category_input.value = ""
            else:
                ui.notify("Invalid URL", type="negative")

        def export_weblinks():
            weblinks = load_weblinks()
            with open("weblinks.json", "w") as f:
                json.dump(
                    [{"name": n, "url": u, "category": c} for n, u, c in weblinks], f
                )
            upload_file_stub("weblinks.json")

        name_input = (
            ui.input("Link Name")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )
        url_input = (
            ui.input("URL")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )
        category_input = (
            ui.input("Category")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )
        ui.button("Add Link", on_click=add_link).classes(
            "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2"
        )
        ui.button("Export to Drive", on_click=export_weblinks).classes(
            "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mt-4"
        )
        refresh_weblinks()