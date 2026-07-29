import threading
import time
import datetime
import os
from typing import Optional

from ..database import SessionLocal
from ..models.models import QueueItem, PlaybackLog, Song
from ..utils.logger import logger
from ..websocket import manager as ws_manager


PLAYBACK_TIME_SCALE = float(os.getenv('PLAYBACK_TIME_SCALE', '1.0'))
COUNTDOWN_SECONDS = float(os.getenv('PLAYBACK_COUNTDOWN', '5.0'))


class PlaybackController:
    def __init__(self):
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._skip = threading.Event()
        self._current_item_id: Optional[int] = None

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                logger.info('Playback already running')
                return
            self._stop.clear()
            self._pause.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            logger.info('Playback controller started')

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)

    def pause(self):
        self._pause.set()
        logger.info('Playback paused')

    def resume(self):
        self._pause.clear()
        logger.info('Playback resumed')

    def skip(self):
        self._skip.set()
        logger.info('Skip requested')

    def get_current(self):
        return self._current_item_id

    def estimated_wait_seconds(self, queue_item_id: Optional[int] = None) -> float:
        db = SessionLocal()
        try:
            q = db.query(QueueItem).filter(QueueItem.status == 'queued').order_by(QueueItem.requested_at).all()
            total = 0.0
            for item in q:
                if queue_item_id is not None and item.id == queue_item_id:
                    break
                song = db.get(Song, item.song_id)
                if song:
                    total += (song.duration or 0)
            return total
        finally:
            db.close()

    def _run_loop(self):
        while not self._stop.is_set():
            # wait if paused
            if self._pause.is_set():
                time.sleep(0.1)
                continue

            db = SessionLocal()
            try:
                item = db.query(QueueItem).filter(QueueItem.status == 'queued').order_by(QueueItem.requested_at).first()
                if not item:
                    time.sleep(0.2)
                    continue
                # begin countdown
                self._current_item_id = item.id
                logger.info('Preparing to play queue item %s', item.id)
                for _ in range(int(max(1, COUNTDOWN_SECONDS * PLAYBACK_TIME_SCALE))):
                    if self._skip.is_set() or self._stop.is_set():
                        break
                    time.sleep(1 * PLAYBACK_TIME_SCALE)
                if self._skip.is_set() or self._stop.is_set():
                    self._skip.clear()
                    self._current_item_id = None
                    continue

                # mark playing
                item.status = 'playing'
                db.add(item)
                db.commit()
                db.refresh(item)

                # create playback log
                log = PlaybackLog(song_id=item.song_id, singer=item.singer, started_at=datetime.datetime.utcnow())
                db.add(log)
                db.commit()
                db.refresh(log)

                # notify websocket song_started
                try:
                    ws_manager.notify_event('song_started', {'song_id': item.song_id, 'queue_item_id': item.id, 'singer': item.singer})
                except Exception:
                    logger.exception('Failed to notify song_started')

                # play duration
                song = db.get(Song, item.song_id)
                duration = (song.duration or 0) * PLAYBACK_TIME_SCALE
                start = time.time()
                while time.time() - start < duration:
                    if self._pause.is_set() or self._skip.is_set() or self._stop.is_set():
                        break
                    time.sleep(0.1)

                # finish
                log.finished_at = datetime.datetime.utcnow()
                db.add(log)
                # mark item as done
                item.status = 'done'
                db.add(item)
                db.commit()

                # notify websocket song_finished
                try:
                    ws_manager.notify_event('song_finished', {'song_id': item.song_id, 'queue_item_id': item.id, 'singer': item.singer})
                except Exception:
                    logger.exception('Failed to notify song_finished')

                self._current_item_id = None
                self._skip.clear()
            except Exception:
                logger.exception('Error in playback loop')
            finally:
                db.close()
            # small sleep between items
            time.sleep(0.1)


playback_controller = PlaybackController()
