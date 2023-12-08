import sys
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        print(f"Change detected: {event.src_path}")
        self.restart_spider()

    def restart_spider(self):
        global process
        if process:
            process.terminate()
            process.wait()
        process = subprocess.Popen([sys.executable, "app.py"])

def start_watching():
    path = '.'  # Set the path to your Scrapy project directory
    observer = Observer()
    observer.schedule(ChangeHandler(), path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    process = None
    start_watching()
