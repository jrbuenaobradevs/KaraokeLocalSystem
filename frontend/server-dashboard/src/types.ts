export interface Song {
  id: number;
  song_number?: string | null;
  title?: string | null;
  artist?: string | null;
  filename?: string | null;
  duration?: number | null;
  created_at?: string;
}

export interface QueueItem {
  id: number;
  singer?: string | null;
  status: string;
  requested_at: string;
  song: Song;
}

export interface PlayerState {
  current_queue_id: number | null;
  current_song_id: number | null;
  status: 'idle' | 'playing' | 'paused';
  estimated_wait_seconds: number;
}

export interface LibraryUpdate {
  created: number;
  created_ids: number[];
  removed: number;
  removed_ids: number[];
  scanned: number;
}

export type DashboardEvent =
  | { event: 'queue_updated'; queue: QueueItem[] }
  | { event: 'player_state'; state: PlayerState }
  | { event: 'library_updated'; result: LibraryUpdate }
  | { event: 'song_started'; song_id: number; queue_item_id: number; singer?: string | null }
  | { event: 'song_finished'; song_id: number; queue_item_id: number; singer?: string | null };
