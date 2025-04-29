from nicegui import ui
import sqlite3
from datetime import datetime
from cryptography.fernet import Fernet
import os
import json
from core import gdrive
import requests
from core.settings import load_setting

DB_FILE = "links.db"
KEY_FILE = "credentials.key"
MASTER_PASSWORD = os.getenv("CREDENTIALS_MASTER_PASSWORD")
if not MASTER_PASSWORD:
    raise ValueError("CREDENTIALS_MASTER_PASSWORD environment variable not set")

# --- Encryption Key Management ---
def load_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key

cipher = Fernet(load_key())

# --- DB Setup ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY,
            name TEXT,
            server_type TEXT,
            url TEXT,
            username TEXT,
            password TEXT,
            token TEXT,
            extra TEXT,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

init_db()

# --- Encryption Helpers ---
def encrypt_field(value):
    if value:
        return cipher.encrypt(value.encode()).decode()
    return ""

def decrypt_field(value):
    if value:
        try:
            return cipher.decrypt(value.encode()).decode()
        except Exception:
            return ""  # Decryption failed or empty
    return ""

# --- UI Render ---
def render():
    with ui.dialog() as master_dialog, ui.card().classes("p-6 bg-gray-700"):
        ui.label("Enter Master Password to Access Credentials").classes("text-2xl font-semibold text-gray-100 mb-4")
        password_input = ui.input("Master Password", password=True).classes("bg-gray-600 text-white rounded w-full mb-4")
        def check_password():
            if password_input.value == MASTER_PASSWORD:
                master_dialog.close()
                show_credentials_ui()
            else:
                ui.notify("Incorrect master password", type="negative")
        ui.button("Submit", on_click=check_password).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2")
    master_dialog.open()

def show_credentials_ui():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Credentials Manager").classes("text-2xl font-semibold text-gray-100 mb-4")
        ui.label("WARNING: Credentials are stored encrypted in the local database.").classes("text-yellow-400 mb-4")
        cred_list = ui.list().classes("w-full")

        def load_credentials():
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT id, name, server_type, url, username, password, token, extra, created_at FROM credentials ORDER BY created_at DESC")
            creds = c.fetchall()
            conn.close()
            decrypted_creds = []
            for cred in creds:
                id_, name, server_type, url, username, password, token, extra, created_at = cred
                decrypted_password = decrypt_field(password)
                decrypted_token = decrypt_field(token)
                decrypted_creds.append((id_, name, server_type, url, username, decrypted_password, decrypted_token, extra, created_at))
            return decrypted_creds

        def save_credential(name, server_type, url, username, password, token, extra):
            enc_password = encrypt_field(password)
            enc_token = encrypt_field(token)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                "INSERT INTO credentials (name, server_type, url, username, password, token, extra, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name, server_type, url, username, enc_password, enc_token, extra, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            refresh()

        def delete_credential(cred_id):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("DELETE FROM credentials WHERE id = ?", (cred_id,))
            conn.commit()
            conn.close()
            refresh()

        def edit_credential_dialog(cred):
            cred_id, name, server_type, url, username, password, token, extra, _ = cred
            with ui.dialog().props("persistent") as dialog, ui.card().classes("p-4 bg-gray-700"):
                ui.label("Edit Credential").classes("text-gray-100")
                name_in = ui.input("Name", value=name).classes("bg-gray-600 text-white rounded w-full mb-2")
                server_type_in = ui.select(["gitea", "github", "gitlab", "other"], value=server_type, label="Server Type").classes("bg-gray-600 text-white rounded w-full mb-2")
                url_in = ui.input("URL", value=url).classes("bg-gray-600 text-white rounded w-full mb-2")
                username_in = ui.input("Username", value=username).classes("bg-gray-600 text-white rounded w-full mb-2")
                password_in = ui.input("Password", value=password, password=True).classes("bg-gray-600 text-white rounded w-full mb-2")
                token_in = ui.input("Token", value=token).classes("bg-gray-600 text-white rounded w-full mb-2")
                extra_in = ui.input("Extra", value=extra).classes("bg-gray-600 text-white rounded w-full mb-2")
                with ui.row():
                    ui.button("Save", on_click=lambda: [
                        update_credential(cred_id, name_in.value, server_type_in.value, url_in.value, username_in.value, password_in.value, token_in.value, extra_in.value),
                        dialog.close()
                    ]).classes("bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2")
                    ui.button("Cancel", on_click=dialog.close).classes("bg-gray-600 hover:bg-gray-500 text-white rounded px-4 py-2")
            dialog.open()

        def update_credential(cred_id, name, server_type, url, username, password, token, extra):
            enc_password = encrypt_field(password)
            enc_token = encrypt_field(token)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute(
                "UPDATE credentials SET name=?, server_type=?, url=?, username=?, password=?, token=?, extra=? WHERE id=?",
                (name, server_type, url, username, enc_password, enc_token, extra, cred_id)
            )
            conn.commit()
            conn.close()
            refresh()

        def add_credential_dialog():
            with ui.dialog().props("persistent") as dialog, ui.card().classes("p-4 bg-gray-700"):
                ui.label("Add Credential").classes("text-gray-100")
                name_in = ui.input("Name").classes("bg-gray-600 text-white rounded w-full mb-2")
                server_type_in = ui.select(["gitea", "github", "gitlab", "other"], label="Server Type").classes("bg-gray-600 text-white rounded w-full mb-2")
                url_in = ui.input("URL").classes("bg-gray-600 text-white rounded w-full mb-2")
                username_in = ui.input("Username").classes("bg-gray-600 text-white rounded w-full mb-2")
                password_in = ui.input("Password", password=True).classes("bg-gray-600 text-white rounded w-full mb-2")
                token_in = ui.input("Token").classes("bg-gray-600 text-white rounded w-full mb-2")
                extra_in = ui.input("Extra").classes("bg-gray-600 text-white rounded w-full mb-2")
                with ui.row():
                    ui.button(
                        "Add",
                        on_click=lambda: [
                            save_credential(
                                name_in.value,
                                server_type_in.value,
                                url_in.value,
                                username_in.value,
                                password_in.value,
                                token_in.value,
                                extra_in.value
                            ),
                            dialog.close()
                        ]
                    ).classes("bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2")
                    ui.button(
                        "Cancel",
                        on_click=dialog.close
                    ).classes("bg-gray-600 hover:bg-gray-500 text-white rounded px-4 py-2")
                dialog.open()

        def test_credential(cred):
            cred_id, name, server_type, url, username, password, token, extra, _ = cred
            status = "Unknown"
            headers = {}
            if token:
                headers["Authorization"] = f"token {token}"
            try:
                if server_type == "gitea":
                    r = requests.get(f"{url}/api/v1/version", headers=headers, timeout=5)
                    if r.status_code == 200:
                        status = f"Valid (Gitea v{r.json().get('version','?')})"
                    else:
                        status = f"Invalid: {r.status_code} {r.text}"
                elif server_type == "github":
                    r = requests.get("https://api.github.com/user", headers=headers, timeout=5)
                    if r.status_code == 200:
                        status = f"Valid (GitHub user: {r.json().get('login','?')})"
                    else:
                        status = f"Invalid: {r.status_code} {r.text}"
                else:
                    status = "Test not supported for this server type."
            except Exception as e:
                status = f"Error: {e}"
            ui.notify(f"Test Credential '{name}': {status}", type="positive" if "Valid" in status else "negative")

        def export_credentials_to_json(filename="credentials_export.json"):
            creds = load_credentials()
            export_list = []
            for cred in creds:
                id_, name, server_type, url, username, password, token, extra, created_at = cred
                export_list.append({
                    "id": id_,
                    "name": name,
                    "server_type": server_type,
                    "url": url,
                    "username": username,
                    "password": password,
                    "token": token,
                    "extra": extra,
                    "created_at": created_at
                })
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(export_list, f, ensure_ascii=False, indent=4)
            gdrive.upload_file_stub(filename)

        def refresh():
            cred_list.clear()
            for cred in load_credentials():
                cred_id, name, server_type, url, username, password, token, extra, created_at = cred
                with cred_list:
                    with ui.card().classes("p-4 bg-gray-600 mb-2"):
                        ui.label(f"{name} [{server_type}]").classes("text-lg font-semibold text-gray-100")
                        ui.label(f"URL: {url}").classes("text-gray-300")
                        ui.label(f"Username: {username}").classes("text-gray-300")
                        ui.label(f"Token: {token}").classes("text-gray-400 text-sm")
                        ui.label(f"Created: {created_at}").classes("text-gray-400 text-xs")
                        with ui.row():
                            ui.button("Edit", on_click=lambda c=cred: edit_credential_dialog(c)).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-2 py-1")
                            ui.button("Delete", on_click=lambda i=cred_id: delete_credential(i)).classes("bg-red-600 hover:bg-red-500 text-white rounded px-2 py-1")
                            ui.button("Test Credential", on_click=lambda c=cred: test_credential(c)).classes("bg-green-600 hover:bg-green-500 text-white rounded px-2 py-1")
            ui.button("Add Credential", on_click=add_credential_dialog).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")
            ui.button("Export & Sync to Google Drive", on_click=export_credentials_to_json).classes("bg-purple-600 hover:bg-purple-500 text-white rounded px-4 py-2 mb-4")
            refresh()

# --- Helper for other modules ---
def get_credentials():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, server_type, url, username, password, token, extra, created_at FROM credentials ORDER BY created_at DESC")
    creds = c.fetchall()
    conn.close()
    decrypted_creds = []
    for cred in creds:
        id_, name, server_type, url, username, password, token, extra, created_at = cred
        decrypted_password = decrypt_field(password)
        decrypted_token = decrypt_field(token)
        decrypted_creds.append((id_, name, server_type, url, username, decrypted_password, decrypted_token, extra, created_at))
    return decrypted_creds

def get_credential_by_id(cred_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, server_type, url, username, password, token, extra, created_at FROM credentials WHERE id = ?", (cred_id,))
    cred = c.fetchone()
    conn.close()
    if cred:
        id_, name, server_type, url, username, password, token, extra, created_at = cred
        decrypted_password = decrypt_field(password)
        decrypted_token = decrypt_field(token)
        return (id_, name, server_type, url, username, decrypted_password, decrypted_token, extra, created_at)
    return None


def get_openweathermap_api_key():
    api_keys = load_setting("api_keys", {})
    return api_keys.get("openweathermap", os.getenv("OPENWEATHERMAP_API_KEY", ""))

def get_github_token():
    api_keys = load_setting("api_keys", {})
    return api_keys.get("github", os.getenv("GITHUB_TOKEN", ""))

def get_gitea_token():
    api_keys = load_setting("api_keys", {})
    return api_keys.get("gitea", os.getenv("GITEA_TOKEN", ""))

def get_gitlab_token():
    api_keys = load_setting("api_keys", {})
    return api_keys.get("gitlab", os.getenv("GITLAB_TOKEN", ""))