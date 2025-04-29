from nicegui import ui
import sqlite3
from pathlib import Path
import os
import yt_dlp
import re
from urllib.parse import urlparse, parse_qs  # noqa: F401


def init_db():
    conn = sqlite3.connect("db/media.db")
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS playlists (id INTEGER PRIMARY KEY, name TEXT, type TEXT)"
    )  # type: local, m3u, youtube
    c.execute(
        "CREATE TABLE IF NOT EXISTS playlist_items (id INTEGER PRIMARY KEY, playlist_id INTEGER, file_path TEXT, url TEXT, title TEXT)"
    )
    conn.commit()
    conn.close()


init_db()


def render():
    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("Media Player").classes("text-2xl font-semibold text-gray-100 mb-4")

        # Media playback
        media = ui.video(src="").classes("w-full h-64 mb-4")
        media_type = {"current": "video"}

        # Playlist management
        playlist_select = ui.select([], label="Playlist").classes(
            "bg-gray-600 text-white rounded w-full mb-2"
        )
        playlist_items = ui.list().classes("w-full mb-4")
        new_playlist_name = (
            ui.input("New Playlist Name")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )

        # YouTube download
        youtube_url = (
            ui.input("YouTube URL (video/playlist)")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )

        # Track selected playlist item
        selected_item = {"id": None, "file_path": None, "url": None, "title": None}

        # M3U import
        ui.upload(
            auto_upload=True, on_upload=lambda e: import_m3u(e)
        ).props("accept=.m3u label=Upload M3U Playlist").classes(
            "bg-gray-600 text-white rounded mb-2"
        )

        def load_playlists():
            conn = sqlite3.connect("media.db")
            c = conn.cursor()
            c.execute("SELECT id, name, type FROM playlists")
            playlists = c.fetchall()
            conn.close()
            return {f"{row[1]} ({row[2]})": row[0] for row in playlists}

        def load_playlist_items(playlist_id):
            conn = sqlite3.connect("media.db")
            c = conn.cursor()
            c.execute(
                "SELECT id, file_path, url, title FROM playlist_items WHERE playlist_id = ?",
                (playlist_id,),
            )
            items = c.fetchall()
            conn.close()
            return items

        def add_playlist(name, playlist_type="local"):
            if name:
                conn = sqlite3.connect("media.db")
                c = conn.cursor()
                c.execute(
                    "INSERT INTO playlists (name, type) VALUES (?, ?)",
                    (name, playlist_type),
                )
                conn.commit()
                conn.close()
                new_playlist_name.value = ""
                refresh_playlists()

        def add_local_file(e):
            playlist_id = playlist_select.value
            if not playlist_id:
                ui.notify("Select a playlist first", type="warning")
                return
            file_path = Path("media") / e.name
            os.makedirs("media", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(e.content.read())
            conn = sqlite3.connect("media.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO playlist_items (playlist_id, file_path, title) VALUES (?, ?, ?)",
                (playlist_id, str(file_path), e.name),
            )
            conn.commit()
            conn.close()
            refresh_playlist_items()

        def delete_playlist_item(item_id):
            conn = sqlite3.connect("media.db")
            c = conn.cursor()
            c.execute("SELECT file_path FROM playlist_items WHERE id = ?", (item_id,))
            file_path = c.fetchone()[0]
            c.execute("DELETE FROM playlist_items WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            if file_path and Path(file_path).exists():
                Path(file_path).unlink()
            refresh_playlist_items()

        def download_youtube():
            url = youtube_url.value.strip()
            if not url:
                ui.notify("Enter a YouTube URL", type="warning")
                return
            playlist_id = playlist_select.value
            if not playlist_id:
                ui.notify("Select a playlist first", type="warning")
                return
            os.makedirs("media", exist_ok=True)
            ydl_opts = {
                "outtmpl": "media/%(title)s.%(ext)s",
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "quiet": True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if "entries" in info:  # Playlist
                        for entry in info["entries"]:
                            file_path = ydl.prepare_filename(entry)
                            conn = sqlite3.connect("media.db")
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO playlist_items (playlist_id, file_path, url, title) VALUES (?, ?, ?, ?)",
                                (
                                    playlist_id,
                                    file_path,
                                    entry["webpage_url"],
                                    entry["title"],
                                ),
                            )
                            conn.commit()
                            conn.close()
                    else:  # Single video
                        file_path = ydl.prepare_filename(info)
                        conn = sqlite3.connect("media.db")
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO playlist_items (playlist_id, file_path, url, title) VALUES (?, ?, ?, ?)",
                            (playlist_id, file_path, url, info["title"]),
                        )
                        conn.commit()
                        conn.close()
                ui.notify("Download complete", type="positive")
                refresh_playlist_items()
            except Exception as e:
                ui.notify(f"Download failed: {str(e)}", type="negative")

        def import_m3u(e):
            playlist_name = new_playlist_name.value.strip() or e.name
            add_playlist(playlist_name, "m3u")
            playlist_id = max(load_playlists().values())
            content = e.content.read().decode("utf-8")
            for line in content.splitlines():
                if line.strip() and not line.startswith("#"):
                    if re.match(r"^(https?://|file://|rtsp://|mms://)", line.strip()):
                        conn = sqlite3.connect("media.db")
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO playlist_items (playlist_id, url, title) VALUES (?, ?, ?)",
                            (playlist_id, line.strip(), line.strip()),
                        )
                        conn.commit()
                        conn.close()
            refresh_playlists()

        def play_media(file_path, url, title):
            if file_path:
                if re.search(r"\.(mp3|wav)$", file_path, re.IGNORECASE):
                    if media_type["current"] != "audio":
                        media.clear()
                        with media:
                            media = ui.audio(src=str(file_path)).classes("w-full mb-4")
                        media_type["current"] = "audio"
                    else:
                        media.set_source(str(file_path))
                elif re.search(r"\.(mp4|mkv)$", file_path, re.IGNORECASE):
                    if media_type["current"] != "video":
                        media.clear()
                        with media:
                            media = ui.video(src=str(file_path)).classes(
                                "w-full h-64 mb-4"
                            )
                        media_type["current"] = "video"
                    else:
                        media.set_source(str(file_path))
            elif url:
                if media_type["current"] != "video":
                    media.clear()
                    with media:
                        media = ui.video(src=url).classes("w-full h-64 mb-4")
                    media_type["current"] = "video"
                else:
                    media.set_source(url)
            ui.notify(f"Playing {title}", type="positive")

        def refresh_playlists():
            playlists = load_playlists()
            playlist_select.options = list(playlists.keys())
            playlist_select.update()
            if playlists:
                playlist_select.value = list(playlists.keys())[0]
                refresh_playlist_items()

        def refresh_playlist_items():
            playlist_items.clear()
            playlist_id = load_playlists().get(playlist_select.value)
            if playlist_id:
                for item_id, file_path, url, title in load_playlist_items(playlist_id):
                    with playlist_items:
                        # Highlight if selected
                        row_classes = "items-center"
                        if selected_item["id"] == item_id:
                            row_classes += " bg-blue-900"
                        with ui.row().classes(row_classes):
                            # Make label clickable to select
                            ui.label(title or (file_path or url)).classes(
                                "text-gray-100 cursor-pointer"
                            ).on(
                                "click",
                                lambda e=None, i=item_id, f=file_path, u=url, t=title: select_item(
                                    i, f, u, t
                                ),
                            )
                            ui.button(
                                "Play",
                                on_click=lambda f=file_path, u=url, t=title: play_media(
                                    f, u, t
                                ),
                            ).classes(
                                "bg-blue-600 hover:bg-blue-500 text-white rounded px-2 py-1"
                            )
                            ui.button(
                                "Delete",
                                on_click=lambda i=item_id: delete_playlist_item(i),
                            ).classes(
                                "bg-red-600 hover:bg-red-500 text-white rounded px-2 py-1"
                            )

        def select_item(item_id, file_path, url, title):
            selected_item["id"] = item_id
            selected_item["file_path"] = file_path
            selected_item["url"] = url
            selected_item["title"] = title
            refresh_playlist_items()

        playlist_select.on("change", refresh_playlist_items)
        ui.button(
            "Add Playlist",
            on_click=lambda: add_playlist(new_playlist_name.value.strip()),
        ).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")
        ui.button("Start Download", on_click=download_youtube).classes(
            "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4"
        )
        ui.upload(
            on_upload=add_local_file, auto_upload=True
        ).props("accept=.mp3,.wav,.mp4,.mkv label=Select Media from Computer").classes(
            "bg-gray-600 text-white rounded mb-4"
        )
        ui.button(
            "Play Selected",
            on_click=lambda: play_media(
                selected_item["file_path"], selected_item["url"], selected_item["title"]
            ),
        ).classes("bg-green-600 hover:bg-green-500 text-white rounded px-4 py-2 mb-4")

        # Add Browse Files button
        ui.button(
            "Browse Files",
            on_click=lambda: ui.navigate.to("/files"),
        ).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")

        # Add Convert button
        def convert_item(item):
            from modules.mediaconverter import convert_file
            from pathlib import Path
            if item and item.get("file_path"):
                with open(item["file_path"], "rb") as f:
                    convert_file(type("Event", (), {"name": Path(item["file_path"]).name, "content": f}))

        ui.button(
            "Convert",
            on_click=lambda: convert_item(selected_item),
        ).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-2 py-1 mb-4")

        # Add Import Radio Stations button
        def import_radio():
            from modules.radio import load_stations
            playlist_name = new_playlist_name.value.strip() or "Radio Stations"
            add_playlist(playlist_name, "m3u")
            playlist_id = max(load_playlists().values())
            for _, name, url, _ in load_stations():
                conn = sqlite3.connect("media.db")
                c = conn.cursor()
                c.execute(
                    "INSERT INTO playlist_items (playlist_id, url, title) VALUES (?, ?, ?)",
                    (playlist_id, url, name)
                )
                conn.commit()
                conn.close()
            refresh_playlists()

        ui.button(
            "Import Radio Stations",
            on_click=import_radio,
        ).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")

        # Add Shuffle button
        ui.button(
            "Shuffle",
            on_click=lambda: shuffle_playlist(),
        ).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")

        # Add Repeat checkbox bound to media.loop
        ui.checkbox("Repeat").bind_value_to(media, "loop").classes("text-gray-100 mb-4")

        # Add volume control slider bound to media.volume
        ui.slider(min=0, max=1, step=0.1, value=1).bind_value_to(media, "volume").classes(
            "w-full mb-4"
        )

        # Add Sync to Drive button
        ui.button(
            "Sync to Drive",
            on_click=lambda: sync_to_drive(),
        ).classes("bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4")


        def shuffle_playlist():
            import random

            items = load_playlist_items(playlist_select.value)
            random.shuffle(items)
            conn = sqlite3.connect("media.db")
            c = conn.cursor()
            c.execute("DELETE FROM playlist_items WHERE playlist_id = ?", (playlist_select.value,))
            for item in items:
                c.execute(
                    "INSERT INTO playlist_items (playlist_id, file_path, url, title) VALUES (?, ?, ?, ?)",
                    (playlist_select.value, item[1], item[2], item[3]),
                )
            conn.commit()
            conn.close()
            refresh_playlist_items()

        def sync_to_drive():
            from core.gdrive import upload_file_stub
            from pathlib import Path

            for item in Path("media").iterdir():
                upload_file_stub(str(item))
            ui.notify("Media synced to Drive", type="positive")

        # Support YouTube streaming without downloading
        def stream_youtube():
            url = youtube_url.value.strip()
            if not url:
                ui.notify("Enter a YouTube URL", type="warning")
                return
            playlist_id = playlist_select.value
            if not playlist_id:
                ui.notify("Select a playlist first", type="warning")
                return
            ydl_opts = {
                "quiet": True,
                "format": "best",
                "noplaylist": True,
                "skip_download": True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    stream_url = info.get("url")
                    title = info.get("title", "YouTube Stream")
                    play_media(None, stream_url, title)
            except Exception as e:
                ui.notify(f"Streaming failed: {str(e)}", type="negative")

        refresh_playlists()

def add_to_playlist(playlist_id, file_path, title):
    conn = sqlite3.connect("media.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO playlist_items (playlist_id, file_path, title) VALUES (?, ?, ?)",
        (playlist_id, file_path, title),
    )
    conn.commit()
    conn.close()
# Marketplace metadata
def marketplace_info():
    return {
        "name": "Media Player",
        "description": "Play and manage media files and playlists",
        "icon": "play_circle_filled",
        "author": "nice-web",
        "author_url": "https://github.com/nice-web",
        "license": "MIT",
        "homepage": "https://example.com"
    }
