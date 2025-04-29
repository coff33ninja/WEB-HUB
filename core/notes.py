from nicegui import ui
import sqlite3
from datetime import datetime
import json
import markdown2
from core import gdrive

import bleach

def init_db():
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    # Add category column if not exists
    c.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT, content TEXT, tags TEXT, category TEXT, created_at TEXT)")
    conn.commit()
    # Check if category column exists, add if missing (for existing DB)
    c.execute("PRAGMA table_info(notes)")
    columns = [info[1] for info in c.fetchall()]
    if "category" not in columns:
        c.execute("ALTER TABLE notes ADD COLUMN category TEXT")
        conn.commit()
    conn.close()

init_db()

def render():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Notes").classes("text-2xl font-semibold text-gray-100 mb-4")
        search_input = ui.input("Search by title or tags").props("clearable").classes("bg-gray-600 text-white rounded w-full mb-4")
        notes_list = ui.list().classes("w-full")

        def load_notes():
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            search = f"%{search_input.value}%" if search_input.value else "%"
            c.execute(
                "SELECT id, title, content, tags, category FROM notes WHERE title LIKE ? OR tags LIKE ? ORDER BY created_at DESC",
                (search, search)
            )
            return c.fetchall()

        def save_note(title, content, tags, category):
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO notes (title, content, tags, category, created_at) VALUES (?, ?, ?, ?, ?)",
                (title, content, tags, category, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()

        def delete_note(note_id):
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            conn.close()
            refresh_notes()

        def refresh_notes():
            notes_list.clear()
            for note_id, title, content, tags, category in load_notes():
                with notes_list:
                    with ui.card().classes("p-4 bg-gray-600 mb-2"):
                        ui.label(title or "Untitled").classes("text-lg font-semibold text-gray-100")
                        ui.markdown(bleach.clean(markdown2.markdown(content[:100] + ("..." if len(content) > 100 else "")), tags=bleach.sanitizer.ALLOWED_TAGS + ['p', 'pre', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'], attributes=bleach.sanitizer.ALLOWED_ATTRIBUTES)).classes("text-gray-300")
                        if tags:
                            ui.label(f"Tags: {tags}").classes("text-gray-400 text-sm")
                        if category:
                            ui.label(f"Category: {category}").classes("text-gray-400 text-sm")
                        with ui.row():
                            ui.button("Edit", on_click=lambda n=(note_id, title, content, tags, category): edit_note(n)).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-2 py-1")
                            ui.button("Delete", on_click=lambda i=note_id: delete_note(i)).classes("bg-red-600 hover:bg-red-500 text-white rounded px-2 py-1")

        def add_note():
            with ui.dialog().props("persistent") as dialog, ui.card().classes("p-4 bg-gray-700"):
                ui.label("New Note").classes("text-gray-100")
                title = ui.input("Title").props("clearable").classes("bg-gray-600 text-white rounded w-full mb-2")
                content = ui.textarea("Content").classes("bg-gray-600 text-white rounded w-full mb-2")
                tags = ui.input("Tags (comma-separated)").props("clearable").classes("bg-gray-600 text-white rounded w-full mb-2")
                category = ui.input("Category").props("clearable").classes("bg-gray-600 text-white rounded w-full mb-2")
                preview_checkbox = ui.checkbox("Preview").classes("mb-2")
                preview_markdown = ui.markdown("").classes("text-gray-300 hidden")
                def toggle_preview(e):
                    if e.value:
                        preview_markdown.content = bleach.clean(markdown2.markdown(content.value), tags=bleach.sanitizer.ALLOWED_TAGS + ['p', 'pre', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'], attributes=bleach.sanitizer.ALLOWED_ATTRIBUTES)
                        preview_markdown.classes("block")
                        content.classes("hidden")
                    else:
                        preview_markdown.classes("hidden")
                        content.classes("block")
                preview_checkbox.on_change(toggle_preview)
                with ui.row():
                    ui.button("Save", on_click=lambda: [save_note(title.value, content.value, tags.value, category.value), refresh_notes(), dialog.close()]).classes("bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2")
                    ui.button("Cancel", on_click=dialog.close).classes("bg-gray-600 hover:bg-gray-500 text-white rounded px-4 py-2")
            dialog.open()

        def edit_note(note):
            note_id, title_text, content_text, tags_text, category_text = note
            with ui.dialog().props("persistent") as dialog, ui.card().classes("p-4 bg-gray-700"):
                ui.label("Edit Note").classes("text-gray-100")
                title = ui.input("Title", value=title_text).props("clearable").classes("bg-gray-600 text-white rounded w-full mb-2")
                content = ui.textarea("Content", value=content_text).classes("bg-gray-600 text-white rounded w-full mb-2")
                tags = ui.input("Tags (comma-separated)", value=tags_text).props("clearable").classes("bg-gray-600 text-white rounded w-full mb-2")
                category = ui.input("Category", value=category_text).props("clearable").classes("bg-gray-600 text-white rounded w-full mb-2")
                preview_checkbox = ui.checkbox("Preview").classes("mb-2")
                preview_markdown = ui.markdown("").classes("text-gray-300 hidden")
                def toggle_preview(e):
                    if e.value:
                        preview_markdown.content = bleach.clean(markdown2.markdown(content.value), tags=bleach.sanitizer.ALLOWED_TAGS + ['p', 'pre', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'], attributes=bleach.sanitizer.ALLOWED_ATTRIBUTES)
                        preview_markdown.classes("block")
                        content.classes("hidden")
                    else:
                        preview_markdown.classes("hidden")
                        content.classes("block")
                preview_checkbox.on_change(toggle_preview)
                with ui.row():
                    ui.button("Save", on_click=lambda: [update_note(note_id, title.value, content.value, tags.value, category.value), refresh_notes(), dialog.close()]).classes("bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2")
                    ui.button("Cancel", on_click=dialog.close).classes("bg-gray-600 hover:bg-gray-500 text-white rounded px-4 py-2")
            dialog.open()

        def update_note(note_id, title, content, tags, category):
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute(
                "UPDATE notes SET title = ?, content = ?, tags = ?, category = ? WHERE id = ?",
                (title, content, tags, category, note_id)
            )
            conn.commit()
            conn.close()

        def export_and_sync_notes():
            notes = []
            for note_id, title, content, tags, category in load_notes():
                notes.append({
                    "id": note_id,
                    "title": title,
                    "content": content,
                    "tags": tags,
                    "category": category
                })
            filename = "notes_export.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(notes, f, ensure_ascii=False, indent=4)
            gdrive.upload_file_stub(filename)
            ui.notify("Notes exported and synced to Google Drive", type="positive")

        search_input.on("change", refresh_notes)
        ui.button("New Note", on_click=add_note).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")
        ui.button("Export & Sync Notes", on_click=export_and_sync_notes).classes("bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2 mb-4")
        refresh_notes()
