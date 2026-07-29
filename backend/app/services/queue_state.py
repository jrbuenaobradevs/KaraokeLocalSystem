from ..database import SessionLocal
from ..models.models import QueueItem
from .player import playback_controller


def get_queue_state() -> list[dict]:
    db = SessionLocal()
    try:
        items = db.query(QueueItem).order_by(QueueItem.requested_at).all()
        return [
            {
                'id': item.id,
                'singer': item.singer,
                'status': item.status,
                'requested_at': item.requested_at.isoformat(),
                'song': {
                    'id': item.song.id,
                    'title': item.song.title,
                    'artist': item.song.artist,
                    'filename': item.song.filename,
                    'duration': item.song.duration,
                },
            }
            for item in items
        ]
    finally:
        db.close()


def get_player_state() -> dict:
    db = SessionLocal()
    try:
        current_id = playback_controller.get_current()
        current_item = db.get(QueueItem, current_id) if current_id is not None else None
            status = 'paused' if playback_controller.is_paused() else 'playing'
        if current_item is None:
            status = 'paused' if playback_controller.is_paused() else 'idle'
        return {
            'current_queue_id': current_id,
            'current_song_id': current_item.song_id if current_item else None,
            'status': status,
            'estimated_wait_seconds': playback_controller.estimated_wait_seconds(current_id),
        }
    finally:
        db.close()
