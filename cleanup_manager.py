import os
import time
from datetime import datetime

def cleanup_old_clips(root_folder="recordings", days=7):
    """
    Deletes video files older than 'days' days in the recordings folder.
    """
    now = time.time()
    cutoff = now - (days * 86400)  # 86400 seconds in a day

    deleted_files = []

    for foldername, subfolders, filenames in os.walk(root_folder):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)
                if file_mtime < cutoff:
                    os.remove(file_path)
                    deleted_files.append(file_path)

    if deleted_files:
        print(f"[CLEANUP] Deleted {len(deleted_files)} old files.")
    else:
        print("[CLEANUP] No old files to delete.")

if __name__ == "__main__":
    # Test cleanup: delete files older than 7 days
    cleanup_old_clips(days=7)
