import { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchPlayerState, fetchQueue, fetchSongs, requestSong } from './api';
import { PlayerState, QueueItem, Song } from './types';
import { useWebsocket } from './useWebsocket';

const formatDuration = (seconds?: number | null) => {
  if (seconds == null) return '--:--';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

function App() {
  const [songs, setSongs] = useState<Song[]>([]);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [playerState, setPlayerState] = useState<PlayerState>({
    current_queue_id: null,
    current_song_id: null,
    status: 'idle',
    estimated_wait_seconds: 0,
  });
  const [songId, setSongId] = useState<number | ''>('');
  const [singer, setSinger] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [songRes, queueRes, playerRes] = await Promise.all([fetchSongs(), fetchQueue(), fetchPlayerState()]);
      setSongs(songRes);
      setQueue(queueRes);
      setPlayerState(playerRes);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleWsMessage = useCallback((event: any) => {
    if (event.event === 'queue_updated') {
      setQueue(event.queue);
    }
    if (event.event === 'player_state') {
      setPlayerState(event.state);
    }
  }, []);

  useWebsocket(handleWsMessage);

  const handleRequest = async () => {
    if (!songId || !singer) {
      setError('Please choose a song and enter a singer name.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await requestSong(Number(songId), singer);
      setSongId('');
      setSinger('');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const availableSongs = useMemo(
    () => songs.filter((song) => {
      const label = `${song.title ?? song.filename ?? ''} ${song.artist ?? ''}`.toLowerCase();
      return label.includes(search.toLowerCase());
    }),
    [search, songs]
  );

  const currentSong = useMemo(
    () => songs.find((song) => song.id === playerState.current_song_id) ?? null,
    [songs, playerState.current_song_id]
  );

  return (
    <div className="min-h-screen bg-slate-950 text-white p-4">
      <div className="mx-auto flex max-w-5xl flex-col gap-6">
        <header className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-slate-950/20">
          <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Mobile Client</p>
          <h1 className="mt-3 text-3xl font-semibold">Karaoke Request App</h1>
          <p className="mt-2 text-slate-400">Search songs, request a queue spot, and follow the live playback status.</p>
        </header>

        {error ? <div className="rounded-3xl border border-rose-500 bg-rose-500/10 p-4 text-rose-200">{error}</div> : null}

        <section className="grid gap-4 xl:grid-cols-[1.4fr,0.9fr]">
          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-slate-950/20">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">Now Playing</h2>
                <p className="mt-1 text-slate-400">Live status from the karaoke server.</p>
              </div>
              <span className="rounded-2xl bg-slate-800 px-3 py-1 text-sm text-slate-300">{playerState.status.toUpperCase()}</span>
            </div>
            <div className="mt-5 space-y-3">
              {currentSong ? (
                <>
                  <p className="text-lg font-semibold text-white">{currentSong.title ?? currentSong.filename}</p>
                  <p className="text-sm text-slate-400">{currentSong.artist ?? 'Unknown Artist'}</p>
                </>
              ) : (
                <p className="text-slate-400">No song is playing right now.</p>
              )}
              <p className="text-sm text-slate-400">Estimated wait: {formatDuration(playerState.estimated_wait_seconds)}</p>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-slate-950/20">
            <h2 className="text-xl font-semibold">Your request</h2>
            <div className="mt-4 space-y-4">
              <label className="block text-sm text-slate-400">
                Search songs
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  className="mt-2 w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-slate-500"
                  placeholder="Search title or artist"
                />
              </label>

              <label className="block text-sm text-slate-400">
                Song
                <select
                  value={songId}
                  onChange={(event) => setSongId(Number(event.target.value) || '')}
                  className="mt-2 w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-slate-500"
                >
                  <option value="">Choose a song</option>
                  {availableSongs.map((song) => (
                    <option key={song.id} value={song.id}>
                      {song.title ?? song.filename} {song.artist ? `- ${song.artist}` : ''}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block text-sm text-slate-400">
                Singer name
                <input
                  value={singer}
                  onChange={(event) => setSinger(event.target.value)}
                  className="mt-2 w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-slate-500"
                  placeholder="Your name"
                />
              </label>

              <button
                onClick={handleRequest}
                className="w-full rounded-2xl bg-sky-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-400"
              >
                Request Song
              </button>
            </div>
          </div>
        </section>

        <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-slate-950/20">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">Queue Position</h2>
              <p className="mt-1 text-slate-400">See the next songs waiting to play.</p>
            </div>
            <span className="rounded-2xl bg-slate-800 px-3 py-1 text-sm text-slate-300">{queue.length} items</span>
          </div>
          <div className="mt-5 space-y-3">
            {loading ? (
              <p className="text-slate-500">Loading queue...</p>
            ) : queue.length ? (
              queue.slice(0, 5).map((item, index) => (
                <div key={item.id} className="rounded-3xl border border-slate-800 bg-slate-950/80 p-4">
                  <p className="font-semibold text-white">#{index + 1} {item.song.title ?? item.song.filename}</p>
                  <p className="text-sm text-slate-400">Singer: {item.singer || 'Unknown'}</p>
                </div>
              ))
            ) : (
              <p className="text-slate-400">No requests in queue yet.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;
