import { Song, QueueItem, PlayerState } from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || response.statusText || 'API request failed');
  }
  return response.json();
}

export async function fetchSongs(): Promise<Song[]> {
  const res = await fetch(`${API_BASE}/songs`, { credentials: 'include' });
  return handleResponse<Song[]>(res);
}

export async function fetchQueue(): Promise<QueueItem[]> {
  const res = await fetch(`${API_BASE}/queue`, { credentials: 'include' });
  return handleResponse<QueueItem[]>(res);
}

export async function fetchPlayerState(): Promise<PlayerState> {
  const res = await fetch(`${API_BASE}/player/state`, { credentials: 'include' });
  return handleResponse<PlayerState>(res);
}

export async function requestSong(songId: number, singer: string): Promise<QueueItem> {
  const res = await fetch(`${API_BASE}/queue`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ song_id: songId, singer }),
  });
  return handleResponse<QueueItem>(res);
}
