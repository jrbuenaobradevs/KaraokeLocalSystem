import asyncio
from typing import Set
from fastapi import WebSocket
from ..utils.logger import logger


_connections: Set[WebSocket] = set()
loop = None


def register(ws: WebSocket):
    _connections.add(ws)
    logger.info('WebSocket connected, total=%d', len(_connections))


def unregister(ws: WebSocket):
    _connections.discard(ws)
    logger.info('WebSocket disconnected, total=%d', len(_connections))


async def broadcast_library_updated(result: dict):
    payload = {"event": "library_updated", "result": result}
    to_remove = []
    for ws in list(_connections):
        try:
            await ws.send_json(payload)
        except Exception:
            logger.exception('Failed to send websocket message')
            to_remove.append(ws)
    for ws in to_remove:
        unregister(ws)


def notify_library_updated(result: dict):
    """Schedule a broadcast on the event loop if available."""
    global loop
    if loop is None:
        logger.debug('No event loop for websocket broadcasts')
        return
    try:
        asyncio.run_coroutine_threadsafe(broadcast_library_updated(result), loop)
    except Exception:
        logger.exception('Failed to schedule websocket broadcast')
