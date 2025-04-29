import os
import sqlite3
from pathlib import Path
from nicegui import ui

# Database setup
db_path = Path("db/db.db")


def init_db():
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """
        )
        conn.commit()


# Load and save settings
def load_setting(key, default):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        if result:
            try:
                return eval(
                    result[0], {}, {}
                )  # Safely evaluate string to Python object
            except Exception:
                return default
        return default


def save_setting(key, value):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value)),
        )
        conn.commit()


# Initialize database
init_db()


def render():
    with ui.card().classes("p-6"):
        ui.label("Settings").classes("text-2xl font-bold")

        # Module Visibility
        ui.label("Module Visibility").classes("text-lg font-semibold mt-4")
        modules = load_setting("modules", {})
        checkboxes = {}
        for module_name in sorted(modules.keys()):
            with ui.row().classes("items-center"):
                checkbox = ui.checkbox(
                    module_name.capitalize(), value=modules.get(module_name, True)
                )
                checkboxes[module_name] = checkbox
                if module_name == "settings":  # Prevent disabling Settings module
                    checkbox.disable()

        # Homepage Widgets
        ui.label("Homepage Widgets").classes("text-lg font-semibold mt-4")
        homepage_widgets = load_setting("homepage_widgets", {
            "notes": True, "todo": True, "calendar": True, "weather": True, "weblinks": True
        })
        widget_checkboxes = {}
        for module_name in ["notes", "todo", "calendar", "weather", "weblinks"]:
            with ui.row().classes("items-center"):
                checkbox = ui.checkbox(
                    module_name.capitalize(), value=homepage_widgets.get(module_name, True)
                )
                widget_checkboxes[module_name] = checkbox

        # Theme Settings
        ui.label("Theme Settings").classes("text-lg font-semibold mt-4")
        theme = load_setting(
            "custom_colors",
            {
                "bg": "#1f2937",
                "card": "#374151",
                "text": "#f3f4f6",
                "accent": "#3b82f6",
            },
        )
        bg_color = ui.color_input("Background Color", value=theme["bg"]).classes("w-full")
        card_color = ui.color_input("Card Color", value=theme["card"]).classes("w-full")
        text_color = ui.color_input("Text Color", value=theme["text"]).classes("w-full")
        accent_color = ui.color_input("Accent Color", value=theme["accent"]).classes("w-full")

        # API Keys
        ui.label("API Keys").classes("text-lg font-semibold mt-4")
        api_keys = load_setting("api_keys", {})
        openweathermap_key = ui.input("OpenWeatherMap API Key", value=api_keys.get("openweathermap", "")).classes("w-full")
        github_key = ui.input("GitHub Token", value=api_keys.get("github", "")).classes("w-full")
        gitea_key = ui.input("Gitea Token", value=api_keys.get("gitea", "")).classes("w-full")
        gitlab_key = ui.input("GitLab Token", value=api_keys.get("gitlab", "")).classes("w-full")

        # Google Drive Credentials
        ui.label("Google Drive Credentials").classes("text-lg font-semibold mt-4")
        def handle_credentials_upload(e):
            with open("credentials.json", "wb") as f:
                f.write(e.content.read())
            ui.notify("Google Drive credentials uploaded", type="positive")
        ui.upload(on_upload=handle_credentials_upload).props("accept=.json label=Upload credentials.json").classes("w-full mb-2")
        if os.path.exists("token.json"):
            ui.label("Google Drive: Connected").classes("text-green-400")
        else:
            ui.label("Google Drive: Not connected").classes("text-red-400")


        def sync_selected_modules_handler():
            from core.gdrive import sync_selected_modules
            sync_selected_modules()
            ui.notify("Selected modules synced!", type="positive")

        ui.button(
            "Sync Selected Modules",
            on_click=sync_selected_modules_handler
        ).classes("mt-4 bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2")

        # Sync Settings
        ui.label("Sync Settings").classes("text-lg font-semibold mt-4")
        sync_modules = ui.select(
            ["notes", "todo", "calendar", "weblinks", "credentials"], multiple=True,
            value=load_setting("sync_modules", ["notes", "todo", "calendar", "weblinks", "credentials"]),
            label="Modules to Sync"
        ).classes("w-full")

        # Apply Settings
        def apply_settings():
            # Save module visibility
            modules = {name: cb.value for name, cb in checkboxes.items()}
            save_setting("modules", modules)
            # Save homepage widgets
            homepage_widgets = {name: cb.value for name, cb in widget_checkboxes.items()}
            save_setting("homepage_widgets", homepage_widgets)
            # Save theme
            theme = {
                "bg": bg_color.value,
                "card": card_color.value,
                "text": text_color.value,
                "accent": accent_color.value,
            }
            save_setting("custom_colors", theme)
            # Save API keys
            api_keys = {
                "openweathermap": openweathermap_key.value,
                "github": github_key.value,
                "gitea": gitea_key.value,
                "gitlab": gitlab_key.value,
            }
            save_setting("api_keys", api_keys)
            # Save sync modules
            save_setting("sync_modules", sync_modules.value)
            ui.notify("Settings applied!", type="positive")

        ui.button("Apply Settings", on_click=apply_settings).classes("mt-4")
        def sync_selected_modules_handler():
            from core.gdrive import sync_selected_modules
            sync_selected_modules()

