from backend.app.main import list_songs, stats
from backend.app.database import SessionLocal


def test_stats_endpoint():
    db = SessionLocal()
    try:
        data = stats(db=db)
        assert 'songs' in data and 'queue' in data
    finally:
        db.close()


def test_songs_empty():
    db = SessionLocal()
    try:
        res = list_songs(db=db)
        assert isinstance(res, list)
    finally:
        db.close()
