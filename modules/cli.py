from nicegui import ui
import subprocess
import sqlite3
import datetime

DB_FILE =  "db/cli.db"
# from contextlib import redirect_stdout

def init_db():
    conn = sqlite3.connect("DB_FILE")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS cli_history (
                    id INTEGER PRIMARY KEY,
                    command TEXT,
                    timestamp TEXT
                )""")
    conn.commit()
    conn.close()

init_db()

def render():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("CLI Terminal").classes("text-2xl font-semibold text-gray-100 mb-4")
        command_input = ui.input("Enter command").props("clearable").classes("bg-gray-600 text-white rounded w-full mb-2")
        output_area = ui.textarea("Output").props("readonly").classes("w-full h-40 bg-gray-600 text-gray-100 mb-4")
        history_list = ui.list().classes("w-full h-40 overflow-auto bg-gray-600 text-gray-100 rounded p-2 mb-4")

        def load_history():
            conn = sqlite3.connect("cli.db")
            c = conn.cursor()
            c.execute("SELECT id, command, timestamp FROM cli_history ORDER BY timestamp DESC LIMIT 10")
            return c.fetchall()

        def save_command(command):
            conn = sqlite3.connect("cli.db")
            c = conn.cursor()
            timestamp = datetime.datetime.now().isoformat()
            c.execute("INSERT INTO cli_history (command, timestamp) VALUES (?, ?)", (command, timestamp))
            conn.commit()
            conn.close()

        def refresh_history():
            history_list.clear()
            for cmd_id, cmd, ts in load_history():
                with history_list:
                    with ui.row().classes("items-center justify-between"):
                        ui.label(f"[{ts}] {cmd}").classes("whitespace-pre-wrap")
                        ui.button("Load", on_click=lambda e=cmd: command_input.set_value(e)).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-2 py-1")

        def run_command():
            try:
                result = subprocess.run(
                    command_input.value,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                output_area.value = result.stdout + result.stderr
                save_command(command_input.value)
                refresh_history()
            except Exception as e:
                output_area.value = f"Error: {str(e)}"

        ui.button("Run", on_click=run_command).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")
        refresh_history()

# Marketplace metadata
def marketplace_info():
    return {
        "name": "CLI Terminal",
        "description": "Command line interface terminal",
        "icon": "terminal",
        "author": "nice-web",
        "author_url": "https://github.com/nice-web",
        "license": "MIT",
        "homepage": "https://example.com"
    }
