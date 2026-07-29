from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .models import Song, QueueItem, PlaybackLog
from . import schemas
from sqlalchemy.orm import Session
from .utils.logger import logger

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Videoke Karaoke Server")

# Basic CORS for LAN access (tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.middleware('http')
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url} -> {response.status_code}")
    return response


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get('/songs', response_model=list[schemas.SongOut])
def list_songs(db: Session = Depends(get_db)):
    return db.query(Song).all()


@app.get('/songs/{song_id}', response_model=schemas.SongOut)
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail='Song not found')
    return song


@app.post('/queue', response_model=schemas.QueueItemOut)
def add_queue(item: schemas.QueueItemCreate, db: Session = Depends(get_db)):
    song = db.get(Song, item.song_id)
    if not song:
        raise HTTPException(status_code=404, detail='Song not found')
    qi = QueueItem(song_id=item.song_id, singer=item.singer)
    db.add(qi)
    db.commit()
    db.refresh(qi)
    return qi


@app.get('/queue', response_model=list[schemas.QueueItemOut])
def get_queue(db: Session = Depends(get_db)):
    return db.query(QueueItem).order_by(QueueItem.requested_at).all()


@app.delete('/queue/{item_id}', status_code=204)
def delete_queue(item_id: int, db: Session = Depends(get_db)):
    item = db.get(QueueItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail='Queue item not found')
    db.delete(item)
    db.commit()
    return


@app.post('/player/play')
def play():
    return {"status": "playing"}


@app.post('/player/pause')
def pause():
    return {"status": "paused"}


@app.post('/player/skip')
def skip():
    return {"status": "skipped"}


@app.post('/library/rescan')
def rescan_library():
    # placeholder for media scanning implementation
    return {"status": "rescan_started"}


@app.get('/stats')
def stats(db: Session = Depends(get_db)):
    song_count = db.query(Song).count()
    queue_count = db.query(QueueItem).count()
    return {"songs": song_count, "queue": queue_count}
