from pydantic import BaseModel
from typing import Optional
import datetime


class SongBase(BaseModel):
    song_number: Optional[str]
    title: Optional[str]
    artist: Optional[str]
    filename: Optional[str]
    duration: Optional[int]


class SongCreate(SongBase):
    filename: str


class SongOut(SongBase):
    id: int
    created_at: datetime.datetime

    class Config:
        orm_mode = True


class QueueItemCreate(BaseModel):
    song_id: int
    singer: Optional[str]


class QueueItemOut(BaseModel):
    id: int
    song: SongOut
    singer: Optional[str]
    status: str
    requested_at: datetime.datetime

    class Config:
        orm_mode = True
