from fastapi import FastAPI, Depends, HTTPException, Request
import datetime
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .models import Song, QueueItem, PlaybackLog
from . import schemas
from .api import auth as auth_api
from .auth.dependencies import admin_guard
from sqlalchemy.orm import Session
from .utils.logger import logger
from .services import scanner, watcher, player
from .websocket import manager as ws_manager
import asyncio
from fastapi import WebSocket, WebSocketDisconnect

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


_media_watcher = None


@app.on_event('startup')
def _startup():
    global _media_watcher
    try:
        _media_watcher = watcher.start_watcher('media')
    except Exception:
        logger.exception('Failed to start media watcher')
    # capture event loop for websocket broadcasts
    try:
        ws_manager.loop = asyncio.get_event_loop()
    except Exception:
        logger.exception('Failed to set websocket event loop')
    # start playback controller
    try:
        player.playback_controller.start()
    except Exception:
        logger.exception('Failed to start playback controller')


@app.on_event('shutdown')
def _shutdown():
    global _media_watcher
    if _media_watcher is not None:
        watcher.stop_watcher(_media_watcher)
    try:
        player.playback_controller.stop()
    except Exception:
        logger.exception('Failed to stop playback controller')


@app.websocket('/ws/library')
async def websocket_library(ws: WebSocket):
    await ws.accept()
    ws_manager.register(ws)
    try:
        while True:
            # keep connection alive; clients may send pings
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.unregister(ws)


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


app.include_router(auth_api.router)


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


@app.post('/queue/{item_id}/move')
def move_queue(item_id: int, position: int, db: Session = Depends(get_db), _: None = Depends(admin_guard)):
    items = db.query(QueueItem).order_by(QueueItem.requested_at).all()
    idx = next((i for i, it in enumerate(items) if it.id == item_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail='Queue item not found')
    item = items.pop(idx)
    if position < 0:
        position = 0
    if position > len(items):
        position = len(items)
    items.insert(position, item)
    # rewrite requested_at to reflect new ordering
    now = datetime.datetime.utcnow()
    for i, it in enumerate(items):
        it.requested_at = now + datetime.timedelta(seconds=i)
        db.add(it)
    db.commit()
    return {"status": "moved"}


@app.post('/queue/clear')
def clear_queue(db: Session = Depends(get_db), _: None = Depends(admin_guard)):
    db.query(QueueItem).delete()
    db.commit()
    return {"status": "cleared"}


@app.post('/player/play')
def play(_: None = Depends(admin_guard)):
    try:
        player.playback_controller.resume()
        player.playback_controller.start()
        return {"status": "playing"}
    except Exception:
        logger.exception('Play failed')
        raise HTTPException(status_code=500, detail='Failed to start playback')


@app.post('/player/pause')
def pause(_: None = Depends(admin_guard)):
    try:
        player.playback_controller.pause()
        return {"status": "paused"}
    except Exception:
        logger.exception('Pause failed')
        raise HTTPException(status_code=500, detail='Failed to pause playback')


@app.post('/player/skip')
def skip(_: None = Depends(admin_guard)):
    try:
        player.playback_controller.skip()
        return {"status": "skipped"}
    except Exception:
        logger.exception('Skip failed')
        raise HTTPException(status_code=500, detail='Failed to skip')


@app.post('/library/rescan')
def rescan_library(_: None = Depends(admin_guard)):
    result = scanner.rescan_and_report('media')
    return {"status": "rescan_finished", "result": result}


@app.get('/stats')
def stats(db: Session = Depends(get_db)):
    song_count = db.query(Song).count()
    queue_count = db.query(QueueItem).count()
    return {"songs": song_count, "queue": queue_count}
