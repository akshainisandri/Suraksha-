import db_manager

events = db_manager.get_all_events()
for e in events:
    print(e)
