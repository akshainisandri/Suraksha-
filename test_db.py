from datetime import datetime
import db_manager

# Insert a test event
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
event_type = "motion"
clip_path = "recordings/test_clip.mp4"
confidence = 0.95

db_manager.insert_event(timestamp, event_type, clip_path, confidence)

# Retrieve all events
events = db_manager.get_all_events()
for event in events:
    print(event)
