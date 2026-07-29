from pydantic import BaseModel
from typing import Optional, List


class QueueItemPayload(BaseModel):
    id: int
    singer: Optional[str]
    status: str
    requested_at: str
    song: dict


class LibraryUpdatedPayload(BaseModel):
    created: int
    created_ids: List[int]
    removed: int
    removed_ids: List[int]
    scanned: int


class PlayerStatePayload(BaseModel):
    current_queue_id: int | None
    current_song_id: int | None
    status: str
    estimated_wait_seconds: float


class SongEventPayload(BaseModel):
    song_id: int
    queue_item_id: int
    singer: Optional[str]
