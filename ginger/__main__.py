import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .conf import args, settings
from .build import build


class FileEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        build()


def ginger():
    """
    The main ginger entry point
    """
    build()

    if args.watch:
        event_handler = FileEventHandler()
        observer = Observer()

        observer.schedule(event_handler,
                          path=settings.input_dir,
                          recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

if __name__ == '__main__':
    import sys
    print(sys.path)
    ginger()
