import os
from pathlib import Path
from backend.app.services import scanner
from backend.app.utils import ffprobe
from backend.app.database import SessionLocal
from backend.app.models.models import Song


def test_scan_creates_records(tmp_path):
    media_dir = tmp_path / 'media'
    media_dir.mkdir()
    # create sample files
    f1 = media_dir / 'Artist A - Song One.webm'
    f2 = media_dir / 'SongTwo.webm'
    f1.write_text('dummy')
    f2.write_text('dummy')

    # mock ffprobe to return durations by patching scanner's imported reference
    real_get = scanner.get_metadata
    def fake_get(p):
        if 'Song One' in p:
            return {'duration': 123.4, 'tags': {'artist': 'Artist A', 'title': 'Song One'}}
        return {'duration': 200.0, 'tags': {}}

    scanner.get_metadata = fake_get
    db = SessionLocal()
    # ensure test DB is clean for songs table
    try:
        db.query(Song).delete()
        db.commit()
    except Exception:
        db.rollback()
    try:
        res = scanner.scan_media(media_dir=str(media_dir), db_session=db)
        assert res['created'] == 2
        # run again - no new creations
        res2 = scanner.scan_media(media_dir=str(media_dir), db_session=db)
        assert res2['created'] == 0
        # remove one file
        f1.unlink()
        res3 = scanner.scan_media(media_dir=str(media_dir), db_session=db)
        assert res3['removed'] == 1
    finally:
        db.close()
        scanner.get_metadata = real_get
