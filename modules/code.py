from nicegui import ui
import io
from contextlib import redirect_stdout
import ast
import sqlite3
from datetime import datetime
import subprocess
import platform

DB_FILE = "db/code.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS snippets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            code TEXT,
            timestamp TEXT
        )
    """)
    c.execute("""CREATE TABLE IF NOT EXISTS cli_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT,
                    timestamp TEXT
                )""")
    conn.commit()
    conn.close()

def save_snippet(title, code):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO snippets (title, code, timestamp) VALUES (?, ?, ?)",
              (title, code, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_command(command):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute("INSERT INTO cli_history (command, timestamp) VALUES (?, ?)", (command, timestamp))
    conn.commit()
    conn.close()

def load_history():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, command, timestamp FROM cli_history ORDER BY timestamp DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    return rows

def render():
    init_db()

    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Code Editor (Jupyter-like)").classes("text-2xl font-semibold text-gray-100 mb-4")

        cells = []

        def add_cell(code_text=""):
            with ui.card().classes("mb-4 p-4 bg-gray-800"):
                cell_input = ui.textarea(code_text).classes("w-full h-32 bg-gray-900 text-white")
                run_button = ui.button("Run Cell").classes("mt-2 mb-2")
                cell_output = ui.textarea("").props("readonly").classes("w-full h-24 bg-gray-700 text-gray-100")

                def run_cell():
                    code = cell_input.value
                    try:
                        tree = ast.parse(code)
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Call)):
                                raise ValueError("Imports and function calls are restricted")
                        f = io.StringIO()
                        with redirect_stdout(f):
                            exec(code, {})
                        cell_output.value = f.getvalue()
                    except Exception as e:
                        cell_output.value = f"Error: {str(e)}"

                run_button.on("click", run_cell)

                cells.append((cell_input, cell_output, run_button))

        add_cell()

        ui.button("Add New Cell", on_click=lambda: add_cell()).classes("mb-4")

    # Terminal and CLI history UI
    with ui.card().classes("p-6 bg-gray-800 mt-6"):
        ui.label("Terminal").classes("text-2xl font-semibold text-gray-200 mb-4")

        command_input = ui.input(label="Command").classes("w-full mb-2")
        terminal_output = ui.textarea("Terminal Output").props("readonly").classes("w-full h-40 bg-black text-green-400")

        history_list = ui.list().classes("w-full h-40 overflow-auto bg-gray-700 text-gray-100 rounded p-2 mb-4")

        def refresh_history():
            history_list.clear()
            for cmd_id, cmd, ts in load_history():
                with history_list:
                    with ui.row().classes("items-center justify-between"):
                        ui.label(f"[{ts}] {cmd}").classes("whitespace-pre-wrap")
                        ui.button("Load", on_click=lambda e=cmd: command_input.set_value(e)).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-2 py-1")

        def run_terminal_command():
            cmd = command_input.value.strip()
            if not cmd:
                terminal_output.value = "Error: Command cannot be empty."
                return
            try:
                # Determine shell based on platform
                if platform.system() == "Windows":
                    shell = True
                    process = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
                else:
                    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                output = process.stdout + process.stderr
                terminal_output.value = output
                save_command(cmd)
                refresh_history()
            except Exception as e:
                terminal_output.value = f"Error running command: {str(e)}"

        ui.button("Run Command", on_click=run_terminal_command).classes("mt-2 mb-4")

        refresh_history()

# Marketplace metadata
def marketplace_info():
    return {
        "name": "Code Editor",
        "description": "Jupyter-like code editor with terminal",
        "icon": "code",
        "author": "nice-web",
        "author_url": "https://github.com/nice-web",
        "license": "MIT",
        "homepage": "https://example.com"
    }
