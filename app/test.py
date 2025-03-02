from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os

class TestEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        print(f"Created: {event.src_path}")

    def on_deleted(self, event):
        print(f"Deleted: {event.src_path}")

    def on_modified(self, event):
        print(f"Modified: {event.src_path}")

def test_watchdog():
    path = os.getcwd()
    print(f"Watching: {path}")

    event_handler = TestEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    test_watchdog()
