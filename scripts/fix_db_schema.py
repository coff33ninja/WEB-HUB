import sqlite3

def add_type_column():
    conn = sqlite3.connect('links.db')
    c = conn.cursor()
    # Check if 'type' column exists
    c.execute("PRAGMA table_info(playlists)")
    columns = [col[1] for col in c.fetchall()]
    if 'type' not in columns:
        c.execute("ALTER TABLE playlists ADD COLUMN type TEXT DEFAULT 'local'")
        print("Added 'type' column to playlists table.")
    else:
        print("'type' column already exists.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_type_column()
