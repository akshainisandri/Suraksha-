import sqlite3

def connect_db():
    """
    Connects to the SQLite database file.
    Returns a connection object.
    """
    conn = sqlite3.connect("events.db")
    return conn

def insert_event(timestamp, event_type, clip_path, confidence=None):
    """
    Inserts a new detection event into the detection_events table.
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO detection_events (timestamp, event_type, confidence, clip_path)
            VALUES (?, ?, ?, ?)
            """,
            (timestamp, event_type, confidence, clip_path)
        )
        conn.commit()
        conn.close()
        print(f"[INSERTED] {event_type} event at {timestamp}")
    except Exception as e:
        print("[ERROR] Failed to insert event:", e)

def get_all_events():
    """
    Retrieves all detection events ordered by most recent.
    Returns a list of tuples.
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM detection_events ORDER BY timestamp DESC")
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print("[ERROR] Failed to retrieve events:", e)
        return []
