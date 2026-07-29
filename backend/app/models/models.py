from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
import datetime


class Song(Base):
    __tablename__ = 'songs'
    id = Column(Integer, primary_key=True, index=True)
    song_number = Column(String, index=True)
    title = Column(String, index=True)
    artist = Column(String, index=True)
    filename = Column(String, unique=True, index=True)
    duration = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class QueueItem(Base):
    __tablename__ = 'queue'
    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, ForeignKey('songs.id'))
    singer = Column(String, nullable=True)
    status = Column(String, default='queued')
    requested_at = Column(DateTime, default=datetime.datetime.utcnow)
    song = relationship('Song')


class PlaybackLog(Base):
    __tablename__ = 'playback_logs'
    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, ForeignKey('songs.id'))
    singer = Column(String, nullable=True)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    song = relationship('Song')
