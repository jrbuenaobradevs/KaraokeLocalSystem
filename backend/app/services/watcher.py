import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from .scanner import rescan_and_report
from ..utils.logger import logger
from ..websocket import manager as ws_manager


class Debouncer:
    def __init__(self, delay: float, func, *args, **kwargs):
        self.delay = delay
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._timer = None

    def call(self):
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(self.delay, self._run)
        self._timer.daemon = True
        self._timer.start()

    def _run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            # notify websockets
            try:
                ws_manager.notify_library_updated(result)
            except Exception:
                logger.exception('Failed to notify websockets')
        except Exception:
            logger.exception('Error running debounced function')


class MediaChangeHandler(FileSystemEventHandler):
    def __init__(self, media_dir: str, debouncer: Debouncer):
        super().__init__()
        self.media_dir = media_dir
        self.debouncer = debouncer

    def on_any_event(self, event):
        logger.debug("Media change detected: %s", event.src_path)
        self.debouncer.call()


def start_watcher(media_dir: str = 'media'):
    p = Path(media_dir)
    p.mkdir(parents=True, exist_ok=True)
    observer = Observer()
    debouncer = Debouncer(1.0, rescan_and_report, media_dir)
    event_handler = MediaChangeHandler(media_dir, debouncer)
    observer.schedule(event_handler, str(p), recursive=False)
    observer_thread = threading.Thread(target=observer.start, daemon=True)
    observer_thread.start()
    logger.info("Started media watcher on %s", media_dir)
    return observer


def stop_watcher(observer: Observer):
    try:
        observer.stop()
        observer.join(timeout=2)
    except Exception:
        logger.exception("Error stopping watcher")
