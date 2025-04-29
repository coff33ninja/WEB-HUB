from nicegui import ui
import os
import shutil
from pathlib import Path
import platform
import psutil

def render():
    from core.gdrive import upload_file_stub

    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("File Management").classes("text-2xl font-semibold text-gray-100 mb-4")

        system = platform.system()
        drives = []

        if system == "Windows":
            # List all drives by checking drive letters
            for drive_letter in range(ord('A'), ord('Z') + 1):
                drive = f"{chr(drive_letter)}:\\"
                if os.path.exists(drive):
                    drives.append(Path(drive))
        else:
            # For Unix-like systems, use root as drive
            drives.append(Path("/"))

        current_path = {"path": None}  # Use dict for mutable closure
        search_text = {"text": ""}  # For search filter

        file_list = ui.list().classes("w-full")

        def get_drive_info(drive_path):
            try:
                usage = psutil.disk_usage(str(drive_path))
                used_gb = usage.used / (1024 ** 3)
                total_gb = usage.total / (1024 ** 3)
                return f"{used_gb:.1f} GB / {total_gb:.1f} GB"
            except Exception:
                return "N/A"

        def upload_to_drive(item):
            upload_file_stub(str(item))
            ui.notify(f"Uploaded {item.name} to Google Drive", type="positive")

        def refresh():
            file_list.clear()
            if current_path["path"] is None:
                # Show drives
                for drive in drives:
                    with file_list:
                        with ui.row().classes("items-center justify-between"):
                            ui.label(str(drive))
                            ui.label(get_drive_info(drive))
                            ui.button("Open", on_click=lambda d=drive: open_path(d)).classes("bg-blue-600 text-white rounded px-2 py-1")
            else:
                # Show files and folders in current_path filtered by search_text
                try:
                    # Add back button if not root drives
                    if current_path["path"] not in drives:
                        with file_list:
                            with ui.row().classes("items-center justify-between"):
                                ui.button(".. (Up)", on_click=go_up).classes("bg-gray-600 text-white rounded px-2 py-1")
                                ui.label("")
                                ui.label("")
                    for item in sorted(current_path["path"].iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                        if search_text["text"].lower() not in item.name.lower():
                            continue
                        with file_list:
                            with ui.row().classes("items-center justify-between"):
                                ui.label(item.name)
                                if item.is_file():
                                    ui.button("Download", on_click=lambda i=item: ui.download(str(i))).classes("bg-green-600 text-white rounded px-2 py-1")
                                    ui.button("Delete", on_click=lambda i=item: delete_item(i)).classes("bg-red-600 text-white rounded px-2 py-1")
                                    ui.button("Sync to Drive", on_click=lambda i=item: upload_to_drive(i)).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-2 py-1")
                                else:
                                    ui.button("Open", on_click=lambda i=item: open_path(i)).classes("bg-blue-600 text-white rounded px-2 py-1")
                except PermissionError:
                    ui.notify("Permission denied to access this directory", type="negative")

        def open_path(path):
            current_path["path"] = path
            refresh()

        def go_up():
            if current_path["path"] is None:
                return
            parent = current_path["path"].parent
            # If parent is root drive, go back to drives list
            if parent in drives or str(parent) == str(current_path["path"]):
                current_path["path"] = None
            else:
                current_path["path"] = parent
            refresh()

        def delete_item(item):
            try:
                if item.is_file():
                    item.unlink()
                else:
                    shutil.rmtree(item)
                ui.notify(f"Deleted {item.name}", type="positive")
            except Exception as e:
                ui.notify(f"Error deleting {item.name}: {str(e)}", type="negative")
            refresh()

        def handle_upload(e):
            allowed_extensions = {".txt", ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".docx", ".xlsx", ".pptx"}
            if current_path["path"] is None:
                ui.notify("Please open a drive or directory first", type="warning")
                return
            if not any(e.name.lower().endswith(ext) for ext in allowed_extensions):
                ui.notify(f"File type not allowed: {e.name}", type="negative")
                return
            try:
                with open(current_path["path"] / e.name, "wb") as f:
                    f.write(e.content.read())
                ui.notify(f"Uploaded {e.name}", type="positive")
            except Exception as e:
                ui.notify(f"Error uploading {e.name}: {str(e)}", type="negative")
            refresh()

        ui.input(placeholder="Search files and folders...", on_change=lambda e: (search_text.update({"text": e.value}), refresh())).classes("mb-4 w-full")
        ui.upload(on_upload=handle_upload).props("label=Upload file").classes("mb-4")
        ui.button("Back to Drives", on_click=lambda: open_path(None)).classes("mb-4 bg-gray-600 text-white rounded px-4 py-2")
        refresh()
