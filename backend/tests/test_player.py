import time
from backend.app.services import player
from backend.app.database import SessionLocal
from backend.app.models.models import Song, QueueItem


def test_estimated_wait_and_queue_manipulation():
    db = SessionLocal()
    try:
        # clean up
        db.query(QueueItem).delete()
        db.query(Song).delete()
        db.commit()
        # create songs
        s1 = Song(song_number='1', title='A', artist='X', filename='a.webm', duration=10)
        s2 = Song(song_number='2', title='B', artist='Y', filename='b.webm', duration=20)
        db.add_all([s1, s2])
        db.commit()
        db.refresh(s1)
        db.refresh(s2)
        # add queue items
        q1 = QueueItem(song_id=s1.id, singer='S1')
        q2 = QueueItem(song_id=s2.id, singer='S2')
        db.add_all([q1, q2])
        db.commit()
        db.refresh(q1)
        db.refresh(q2)

        # estimate wait for second item should be duration of first
        est = player.playback_controller.estimated_wait_seconds(queue_item_id=q2.id)
        assert int(est) == 10

        # move q2 to front
        from backend.app.main import move_queue, clear_queue
        # position 0
        move_queue(q2.id, 0, db_session if False else db)
        items = db.query(QueueItem).order_by(QueueItem.requested_at).all()
        assert items[0].id == q2.id

        # clear
        clear_queue(db)
        assert db.query(QueueItem).count() == 0
    finally:
        db.close()
