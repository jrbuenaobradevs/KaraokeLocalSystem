import { Song, QueueItem, PlayerState } from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

async function handleResponse(response: Response) {
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || response.statusText || 'API request failed');
  }
  return response.json();
}

export async function fetchPlayerState(): Promise<PlayerState> {
  const res = await fetch(`${API_BASE}/player/state`, {
    credentials: 'include',
  });
  return handleResponse(res);
}

export async function fetchQueue(): Promise<QueueItem[]> {
  const res = await fetch(`${API_BASE}/queue`, {
    credentials: 'include',
  });
  return handleResponse(res);
}

export async function fetchLibrary(): Promise<Song[]> {
  const res = await fetch(`${API_BASE}/songs`, {
    credentials: 'include',
  });
  return handleResponse(res);
}

export async function fetchAuthStatus(): Promise<{ authenticated: boolean }> {
  const res = await fetch(`${API_BASE}/auth/status`, {
    credentials: 'include',
  });
  return handleResponse(res);
}

export async function login(pin: string): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pin }),
  });
  await handleResponse(res);
}

export async function logout(): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  await handleResponse(res);
}

export async function addSongToQueue(songId: number, singer: string): Promise<QueueItem> {
  const res = await fetch(`${API_BASE}/queue`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ song_id: songId, singer }),
  });
  return handleResponse(res);
}

export async function removeQueueItem(queueId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/queue/${queueId}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  await handleResponse(res);
}

export async function moveQueueItem(queueId: number, position: number): Promise<void> {
  const res = await fetch(`${API_BASE}/queue/${queueId}/move`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ position }),
  });
  await handleResponse(res);
}

export async function play(): Promise<void> {
  const res = await fetch(`${API_BASE}/player/play`, {
    method: 'POST',
    credentials: 'include',
  });
  await handleResponse(res);
}

export async function pause(): Promise<void> {
  const res = await fetch(`${API_BASE}/player/pause`, {
    method: 'POST',
    credentials: 'include',
  });
  await handleResponse(res);
}

export async function skip(): Promise<void> {
  const res = await fetch(`${API_BASE}/player/skip`, {
    method: 'POST',
    credentials: 'include',
  });
  await handleResponse(res);
}
