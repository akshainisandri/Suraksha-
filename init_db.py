import sqlite3

def create_database():
    # Connect to SQLite (creates file if it does not exist)
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event_type TEXT,
            confidence REAL,
            clip_path TEXT
        );
    """)

    # Save and close
    conn.commit()
    conn.close()
    print("Database and table created successfully.")

if __name__ == "__main__":
    create_database()
