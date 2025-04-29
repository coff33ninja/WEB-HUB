from nicegui import ui
import psutil
import time
import sqlite3
from datetime import datetime
import csv
from core import gdrive

def init_db():
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS process_logs (id INTEGER PRIMARY KEY, pid INTEGER, name TEXT, action TEXT, timestamp TEXT)")
    conn.commit()
    conn.close()

init_db()

def set_priority(pid, value):
    try:
        psutil.Process(pid).nice(value)
        ui.notify(f"Set priority for PID {pid}", type="positive")
    except Exception as e:
        ui.notify(f"Failed to set priority: {str(e)}", type="negative")

def export_logs():
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    c.execute("SELECT pid, name, action, timestamp FROM process_logs")
    with open("process_logs.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["PID", "Name", "Action", "Timestamp"])
        writer.writerows(c.fetchall())
    conn.close()
    gdrive.upload_file_stub("process_logs.csv")

def render():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("System Stats and Process Manager").classes("text-2xl font-semibold text-gray-100 mb-4")

        with ui.tabs() as tabs:
            tabs.active = 0  # Set default active tab to the first tab
            with ui.tab("Stats & Processes"):
                # Computer stats labels
                cpu_label = ui.label()
                mem_label = ui.label()
                disk_label = ui.label()

                # Process manager UI components
                filter_input = ui.input("Filter by name").props("clearable").classes("bg-gray-600 text-white rounded w-full mb-4")
                process_table = ui.table(
                    columns=[
                        {"name": "pid", "label": "PID", "field": "pid"},
                        {"name": "name", "label": "Name", "field": "name"},
                        {"name": "cpu", "label": "CPU %", "field": "cpu"},
                        {"name": "memory", "label": "Memory %", "field": "memory"},
                        {"name": "priority", "label": "Priority", "field": "priority"},
                        {"name": "actions", "label": "Actions", "field": "actions"}
                    ],
                    rows=[]
                ).classes("w-full bg-gray-600 text-gray-100")

                def update_stats():
                    start_time = time.perf_counter()
                    cpu = psutil.cpu_percent()
                    mem = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    cpu_label.set_text(f"CPU Usage: {cpu}%")
                    mem_label.set_text(f"Memory Usage: {mem.used / mem.total * 100:.1f}%")
                    disk_label.set_text(f"Disk Usage: {disk.used / disk.total * 100:.1f}%")
                    elapsed = time.perf_counter() - start_time
                    print(f"update_stats took {elapsed:.4f} seconds")

                def refresh_processes():
                    start_time = time.perf_counter()
                    filter_text = filter_input.value.lower() if filter_input.value else ""
                    rows = []
                    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "nice"]):
                        try:
                            if filter_text in proc.info["name"].lower():
                                # Determine priority label
                                nice_val = proc.info.get("nice", 0)
                                if nice_val < 0:
                                    priority_label = "High"
                                elif nice_val == 0:
                                    priority_label = "Normal"
                                else:
                                    priority_label = "Low"
                                rows.append({
                                    "pid": proc.info["pid"],
                                    "name": proc.info["name"],
                                    "cpu": round(proc.info["cpu_percent"], 1),
                                    "memory": round(proc.info["memory_percent"], 1),
                                    "priority": priority_label,
                                    "actions": ""
                                })
                        except Exception:
                            continue
                    process_table.rows = rows
                    process_table.update()
                    elapsed = time.perf_counter() - start_time
                    print(f"refresh_processes took {elapsed:.4f} seconds")

                def terminate_process(pid, name):
                    # Restrict termination of critical system processes
                    try:
                        proc = psutil.Process(pid)
                        if proc.username() == "SYSTEM" or proc.pid == 0 or proc.pid == 4:
                            ui.notify(f"Cannot terminate critical system process {name} (PID: {pid})", type="negative")
                            return
                    except Exception:
                        pass
                    try:
                        proc.terminate()
                        conn = sqlite3.connect("links.db")
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO process_logs (pid, name, action, timestamp) VALUES (?, ?, ?, ?)",
                            (pid, name, "terminated", datetime.now().isoformat())
                        )
                        conn.commit()
                        conn.close()
                        ui.notify(f"Terminated process {name} (PID: {pid})", type="positive")
                        refresh_processes()
                    except Exception as e:
                        ui.notify(f"Failed to terminate process {name}: {str(e)}", type="negative")

                def show_terminate_dialog(e):
                    dialog = ui.dialog().props("persistent")
                    with dialog:
                        with ui.card().classes("p-4 bg-gray-700"):
                            ui.label(f"Terminate process {e.args['row']['name']} (PID: {e.args['row']['pid']})?").classes("text-gray-100")
                            with ui.row():
                                ui.button("Confirm", on_click=lambda: [terminate_process(e.args['row']['pid'], e.args['row']['name']), dialog.close()]).classes("bg-red-600 hover:bg-red-500 text-white rounded px-4 py-2")
                                ui.button("Cancel", on_click=dialog.close).classes("bg-gray-600 hover:bg-gray-500 text-white rounded px-4 py-2")
                    dialog.open()

                def on_priority_change(e):
                    pid = e.sender.props.get("pid")
                    if pid is not None:
                        priority_map = {"High": -10, "Normal": 0, "Low": 10}
                        set_priority(pid, priority_map.get(e.value, 0))

                process_table.on("row-click", show_terminate_dialog)
                filter_input.on("change", refresh_processes)

                # Add priority select in each row after table update
                def add_priority_selects():
                    for row in process_table.rows:
                        pid = row["pid"]
                        priority = row.get("priority", "Normal")
                        select = ui.select(["High", "Normal", "Low"], value=priority, on_change=on_priority_change).classes("bg-gray-600 text-white rounded")
                        select.props["pid"] = pid
                        # Attach select to the corresponding row's priority cell
                        # This is a workaround since nicegui table does not support widgets in cells directly
                        # So we will add selects below the table for demonstration
                        select.style("margin-right: 8px;")
                        ui.add(select)

                ui.timer(1.0, update_stats)
                ui.timer(2.0, refresh_processes)

                update_stats()
                refresh_processes()

            with ui.tab("Process Logs"):
                ui.button("Export Logs to Drive", on_click=export_logs).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")
                with ui.table(
                    columns=[
                        {"name": "pid", "label": "PID", "field": "pid"},
                        {"name": "name", "label": "Name", "field": "name"},
                        {"name": "action", "label": "Action", "field": "action"},
                        {"name": "timestamp", "label": "Timestamp", "field": "timestamp"},
                    ],
                    rows=[]
                ) as logs_table:

                    def refresh_logs():
                        conn = sqlite3.connect("links.db")
                        c = conn.cursor()
                        c.execute("SELECT pid, name, action, timestamp FROM process_logs ORDER BY timestamp DESC")
                        logs = c.fetchall()
                        conn.close()
                        logs_table.rows = [{"pid": row[0], "name": row[1], "action": row[2], "timestamp": row[3]} for row in logs]
                        logs_table.update()

                    ui.timer(5.0, refresh_logs)
                    refresh_logs()

# Marketplace metadata
def marketplace_info():
    return {
        "name": "System Stats",
        "description": "Monitor CPU, memory, disk, and manage processes",
        "icon": "bar_chart",
        "author": "nice-web",
        "author_url": "https://github.com/nice-web",
        "license": "MIT",
        "homepage": "https://example.com"
    }
