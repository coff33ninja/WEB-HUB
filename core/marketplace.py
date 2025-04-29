from nicegui import ui
import sqlite3
from pathlib import Path
import os


def init_db():
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS marketplace (id INTEGER PRIMARY KEY, name TEXT, description TEXT, author TEXT, filename TEXT)"
    )
    # Add version column if it doesn't exist
    c.execute("PRAGMA table_info(marketplace)")
    columns = [info[1] for info in c.fetchall()]
    if "version" not in columns:
        c.execute("ALTER TABLE marketplace ADD COLUMN version TEXT")
    # Add RSS Reader entry if not exists
    c.execute("SELECT id FROM marketplace WHERE name = ?", ("RSS Reader",))
    if not c.fetchone():
        c.execute(
            "INSERT INTO marketplace (name, description, author, filename) VALUES (?, ?, ?, ?)",
            ("RSS Reader", "Manage and read RSS feeds", "Unknown", ""),
        )
    conn.commit()
    conn.close()


init_db()


def load_modules():
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute("SELECT name, description, author, filename, version FROM marketplace")
    return c.fetchall()


def save_module(name, description, author, filename, version=None):
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO marketplace (name, description, author, filename, version) VALUES (?, ?, ?, ?, ?)",
        (name, description, author, filename, version),
    )
    conn.commit()
    conn.close()


def delete_module(filename):
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute("DELETE FROM marketplace WHERE filename = ?", (filename,))
    conn.commit()
    conn.close()
    os.remove(Path("marketplace") / filename)


def render():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Media Player Marketplace").classes(
            "text-2xl font-semibold text-gray-100 mb-4"
        )
        modules_list = ui.list().classes("w-full")

        def refresh_modules():
            modules_list.clear()
            for name, description, author, filename, version in load_modules():
                with modules_list:
                    with ui.card().classes("p-4 bg-gray-600 mb-2"):
                        ui.label(name).classes("text-lg font-semibold text-gray-100")
                        ui.label(description).classes("text-gray-300")
                        ui.label(f"Author: {author}").classes("text-gray-400 text-sm")
                        ui.label(f"Version: {version or 'N/A'}").classes("text-gray-400 text-sm")
                        ui.button(
                            "Download",
                            on_click=lambda f=filename: ui.download(
                                str(Path("marketplace") / f)
                            ),
                        ).classes(
                            "bg-green-600 hover:bg-green-500 text-white rounded px-2 py-1"
                        )
                        ui.button(
                            "Delete", on_click=lambda f=filename: delete_module(f)
                        ).classes(
                            "bg-red-600 hover:bg-red-500 text-white rounded px-2 py-1"
                        )

        def handle_upload(e):
            filename = e.name
            module_path = Path("marketplace") / filename
            with open(module_path, "wb") as f:
                f.write(e.content.read())
            save_module(
                name_input.value or filename,
                desc_input.value,
                author_input.value or "Anonymous",
                filename,
                version_input.value or None,
            )
            refresh_modules()

        name_input = (
            ui.input("Module Name")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )
        desc_input = (
            ui.input("Description")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )
        author_input = (
            ui.input("Author")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )
        version_input = (
            ui.input("Version")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )
        ui.upload(on_upload=handle_upload).props("accept='.py' label=Upload Module").classes(
            "bg-gray-600 text-white rounded mb-2"
        )
        ui.button("Refresh", on_click=refresh_modules).classes(
            "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2"
        )
        refresh_modules()
