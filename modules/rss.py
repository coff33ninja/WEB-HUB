from nicegui import ui
import sqlite3
import feedparser


def init_db():
    conn = sqlite3.connect("links.db")
    c = conn.cursor()
    # Add category column if it doesn't exist
    c.execute("PRAGMA table_info(rss_feeds)")
    columns = [col[1] for col in c.fetchall()]
    if "category" not in columns:
        c.execute("ALTER TABLE rss_feeds ADD COLUMN category TEXT")
    c.execute(
        "CREATE TABLE IF NOT EXISTS rss_feeds (id INTEGER PRIMARY KEY, name TEXT, url TEXT, category TEXT)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS rss_items (id INTEGER PRIMARY KEY, feed_id INTEGER, title TEXT, link TEXT, published TEXT, read BOOLEAN)"
    )
    conn.commit()
    conn.close()


init_db()


def render():
    def add_feed():
        name = name_input.value.strip() or url_input.value.strip()
        url = url_input.value.strip()
        category = category_input.value.strip()
        if url:
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO rss_feeds (name, url, category) VALUES (?, ?, ?)", (name, url, category)
            )
            conn.commit()
            conn.close()
            name_input.value = ""
            url_input.value = ""
            category_input.value = ""
            refresh_feeds()

    def export_rss():
        from core.gdrive import upload_file_stub
        conn = sqlite3.connect("links.db")
        c = conn.cursor()
        c.execute("SELECT id, name, url, category FROM rss_feeds")
        feeds = c.fetchall()
        c.execute("SELECT feed_id, title, link, published, read FROM rss_items")
        items = c.fetchall()
        with open("rss.json", "w") as f:
            import json

            json.dump({"feeds": feeds, "items": items}, f)
        conn.close()
        upload_file_stub("rss.json")

    with ui.card().classes("p-6 bg-gray-700"):
        ui.label("RSS Feed Reader").classes("text-2xl font-semibold text-gray-100 mb-4")
        name_input = (
            ui.input("Feed Name")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )
        url_input = (
            ui.input("Feed URL")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )
        category_input = (
            ui.input("Category")
            .props("clearable")
            .classes("bg-gray-600 text-white rounded w-full mb-2")
        )
        ui.button("Add Feed", on_click=add_feed).classes(
            "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4"
        )
        ui.button("Export to Drive", on_click=export_rss).classes(
            "bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-2 mb-4"
        )
        feeds_list = ui.list().classes("w-full")

        def load_feeds():
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute("SELECT id, name, url, category FROM rss_feeds")
            return c.fetchall()

        def delete_feed(feed_id):
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute("DELETE FROM rss_feeds WHERE id = ?", (feed_id,))
            c.execute("DELETE FROM rss_items WHERE feed_id = ?", (feed_id,))
            conn.commit()
            conn.close()
            refresh_feeds()

        def toggle_read(item_id, read):
            conn = sqlite3.connect("links.db")
            c = conn.cursor()
            c.execute("UPDATE rss_items SET read = ? WHERE id = ?", (not read, item_id))
            conn.commit()
            conn.close()
            refresh_feeds()

    def refresh_feeds():
        feeds_list.clear()
        for feed_id, name, url, category in load_feeds():
            with feeds_list:
                with ui.card().classes("p-4 bg-gray-600 mb-2"):
                    ui.label(f"{name} ({category})").classes("text-lg font-semibold text-gray-100")
                    ui.button(
                        "Delete", on_click=lambda f=feed_id: delete_feed(f)
                    ).classes(
                        "bg-red-600 hover:bg-red-500 text-white rounded px-2 py-1 mb-2"
                    )
                    try:
                        feed = feedparser.parse(url)
                        conn = sqlite3.connect("links.db")
                        c = conn.cursor()
                        for entry in feed.entries[:5]:  # Limit to 5 items
                            c.execute(
                                "SELECT id, read FROM rss_items WHERE link = ?",
                                (entry.link,),
                            )
                            item = c.fetchone()
                            if not item:
                                c.execute(
                                    "INSERT INTO rss_items (feed_id, title, link, published, read) VALUES (?, ?, ?, ?, ?)",
                                    (
                                        feed_id,
                                        entry.title,
                                        entry.link,
                                        entry.get("published", ""),
                                        False,
                                    ),
                                )
                                conn.commit()
                                item_id, read = c.lastrowid, False
                            else:
                                item_id, read = item
                            with ui.row().classes("items-center"):
                                ui.checkbox(
                                    value=read,
                                    on_change=lambda e, i=item_id, r=read: toggle_read(
                                        i, r
                                    ),
                                ).classes("mr-2")
                                ui.link(entry.title, entry.link).props(
                                    "target=_blank"
                                ).classes(
                                    "text-blue-400 hover:text-blue-300"
                                    if not read
                                    else "text-gray-400"
                                )
                        conn.close()
                    except Exception:
                        ui.label("Error fetching feed").classes("text-red-500")

    ui.timer(3600, refresh_feeds)  # Refresh every hour

# Marketplace metadata
def marketplace_info():
    return {
        "name": "RSS Feed Reader",
        "description": "A simple RSS feed reader",
        "icon": "rss_feed",
        "author": "nice-web",
        "author_url": "https://github.com/nice-web",
        "license": "MIT",
        "homepage": "https://example.com"
    }
