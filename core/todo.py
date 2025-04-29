from nicegui import ui
import sqlite3
from datetime import datetime
import json
from core.gdrive import upload_file_stub

def init_db():
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    # Add columns due_date and priority if they don't exist
    c.execute("CREATE TABLE IF NOT EXISTS todos (id INTEGER PRIMARY KEY, task TEXT, done BOOLEAN, created_at TEXT, due_date TEXT, priority INTEGER)")
    # Check if columns exist, add if missing (SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS)
    c.execute("PRAGMA table_info(todos)")
    columns = [info[1] for info in c.fetchall()]
    if "due_date" not in columns:
        c.execute("ALTER TABLE todos ADD COLUMN due_date TEXT")
    if "priority" not in columns:
        c.execute("ALTER TABLE todos ADD COLUMN priority INTEGER")
    conn.commit()
    conn.close()

init_db()

def render():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Todo List").classes("text-2xl font-semibold text-gray-100 mb-4")
        task_input = ui.input("New Task").props("clearable").classes("bg-gray-600 text-white rounded w-full mb-2")
        due_date_input = ui.input("Due Date (YYYY-MM-DD)").classes("bg-gray-600 text-white rounded w-full mb-2")
        priority_select = ui.select(["Low", "Medium", "High"], value="Medium").classes("bg-gray-600 text-white rounded w-full mb-2")
        filter_select = ui.select(["All", "Pending", "Done"], value="All").classes("bg-gray-600 text-white rounded w-full mb-4")
        todos_list = ui.list().classes("w-full")

        def add_todo():
            task = task_input.value.strip()
            due_date = due_date_input.value.strip()
            priority_map = {"Low": 1, "Medium": 2, "High": 3}
            priority = priority_map.get(priority_select.value, 2)
            if task:
                conn = sqlite3.connect("links.db")
                c = conn.cursor()
                c.execute("INSERT INTO todos (task, done, created_at, due_date, priority) VALUES (?, ?, ?, ?, ?)", (task, False, datetime.now().isoformat(), due_date, priority))
                conn.commit()
                conn.close()
                task_input.value = ""
                due_date_input.value = ""
                priority_select.value = "Medium"
                refresh_todos()

        def toggle_todo(id, done):
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute("UPDATE todos SET done = ? WHERE id = ?", (not done, id))
            conn.commit()
            conn.close()
            refresh_todos()

        def refresh_todos():
            todos_list.clear()
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            filter_value = filter_select.value
            query = "SELECT id, task, done, due_date, priority FROM todos"
            if filter_value == "Pending":
                query += " WHERE done = 0"
            elif filter_value == "Done":
                query += " WHERE done = 1"
            query += " ORDER BY created_at DESC"
            c.execute(query)
            for id, task, done, due_date, priority in c.fetchall():
                with todos_list:
                    with ui.row().classes("items-center justify-between"):
                        with ui.row().classes("items-center"):
                            ui.checkbox(value=done, on_change=lambda e, i=id, d=done: toggle_todo(i, d)).classes("mr-2")
                            label_text = f"{task} (Due: {due_date})" if due_date else task
                            label_classes = "text-gray-100" if not done else "text-gray-400 line-through"
                            ui.label(label_text).classes(label_classes)
                        priority_map_rev = {1: "Low", 2: "Medium", 3: "High"}
                        ui.label(priority_map_rev.get(priority, "Medium")).classes("text-gray-300 ml-4")
            conn.close()

        def export_todos():
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute("SELECT id, task, done, created_at, due_date, priority FROM todos")
            todos = c.fetchall()
            conn.close()
            todos_list_json = []
            priority_map_rev = {1: "Low", 2: "Medium", 3: "High"}
            for t in todos:
                todos_list_json.append({
                    "id": t[0],
                    "task": t[1],
                    "done": bool(t[2]),
                    "created_at": t[3],
                    "due_date": t[4],
                    "priority": priority_map_rev.get(t[5], "Medium")
                })
            with open("todos.json", "w", encoding="utf-8") as f:
                json.dump(todos_list_json, f, indent=4)
            upload_file_stub("todos.json")

        ui.button("Add Task", on_click=add_todo).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mr-2")
        ui.button("Export to Drive", on_click=export_todos).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2")
        filter_select.on("change", lambda e: refresh_todos())
        refresh_todos()
