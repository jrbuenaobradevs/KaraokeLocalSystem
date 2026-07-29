import os
from pathlib import Path
import datetime
from typing import Optional

from ..database import SessionLocal
from ..models.models import Song
from ..utils.logger import logger
from ..utils.ffprobe import get_metadata


def parse_filename(path: Path) -> tuple[str, str]:
    # Try to parse "Artist - Title.ext" otherwise use stem as title
    stem = path.stem
    if ' - ' in stem:
        parts = stem.split(' - ', 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    else:
        artist = ''
        title = stem
    return title, artist


def scan_media(media_dir: str = 'media', db_session: Optional[SessionLocal] = None) -> dict:
    created = 0
    removed = 0
    created_ids: list[int] = []
    removed_ids: list[int] = []
    media_path = Path(media_dir)
    files = []
    if media_path.exists() and media_path.is_dir():
        files = [p for p in media_path.iterdir() if p.suffix.lower() in ('.webm', '.mp4', '.mkv')]

    external_db = db_session is not None
    db = db_session or SessionLocal()
    try:
        existing = {s.filename: s for s in db.query(Song).all()}
        file_names = set()
        for p in files:
            filename = str(p.name)
            file_names.add(filename)
            if filename in existing:
                # update duration if possible
                meta = get_metadata(str(p))
                if meta.get('duration'):
                    existing[filename].duration = int(meta['duration'])
                continue
            title, artist = parse_filename(p)
            meta = get_metadata(str(p))
            duration = int(meta['duration']) if meta.get('duration') else 0
            # prefer tags for artist/title when available
            tags = meta.get('tags') or {}
            ttitle = tags.get('title') or title
            tartist = tags.get('artist') or artist
            song = Song(
                song_number=None,
                title=ttitle,
                artist=tartist,
                filename=filename,
                duration=duration,
                created_at=datetime.datetime.utcnow(),
            )
            db.add(song)
            # flush to get id
            db.flush()
            db.refresh(song)
            created_ids.append(song.id)
            created += 1
        # delete songs whose files are missing
        for fname, song in existing.items():
            if fname not in file_names:
                removed_ids.append(song.id)
                db.delete(song)
                removed += 1
        if created or removed:
            db.commit()
        return {"created": created, "created_ids": created_ids, "removed": removed, "removed_ids": removed_ids, "scanned": len(files)}
    finally:
        if not external_db:
            db.close()


def rescan_and_report(media_dir: str = 'media') -> dict:
    logger.info("Rescanning media directory: %s", media_dir)
    result = scan_media(media_dir=media_dir)
    logger.info("Rescan result: %s", result)
    return result
