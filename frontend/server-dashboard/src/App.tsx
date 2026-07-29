import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  addSongToQueue,
  fetchAuthStatus,
  fetchLibrary,
  fetchPlayerState,
  fetchQueue,
  login,
  logout,
  play,
  pause,
  removeQueueItem,
  skip,
} from './api';
import { PlayerState, QueueItem, Song, DashboardEvent } from './types';
import { useWebsocket } from './useWebsocket';
import StatusCard from './components/StatusCard';

const formatDuration = (seconds?: number | null) => {
  if (seconds == null) return '--:--';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [playerState, setPlayerState] = useState<PlayerState>({
    current_queue_id: null,
    current_song_id: null,
    status: 'idle',
    estimated_wait_seconds: 0,
  });
  const [library, setLibrary] = useState<Song[]>([]);
  const [pin, setPin] = useState('');
  const [songId, setSongId] = useState<number | ''>('');
  const [singer, setSinger] = useState('');
  const [error, setError] = useState<string | null>(null);

  const loadState = useCallback(async () => {
    try {
      const [auth, queueRes, playerRes, libraryRes] = await Promise.all([
        fetchAuthStatus(),
        fetchQueue(),
        fetchPlayerState(),
        fetchLibrary(),
      ]);
      setAuthenticated(auth.authenticated);
      setQueue(queueRes);
      setPlayerState(playerRes);
      setLibrary(libraryRes);
    } catch (err) {
      console.error(err);
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadState();
  }, [loadState]);

  const handleWsMessage = useCallback((event: DashboardEvent) => {
    if (event.event === 'queue_updated') {
      setQueue(event.queue);
    }

    if (event.event === 'player_state') {
      setPlayerState(event.state);
    }
  }, []);

  useWebsocket(handleWsMessage);

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      await login(pin);
      setAuthenticated(true);
      await loadState();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    setLoading(true);
    setError(null);
    try {
      await logout();
      setAuthenticated(false);
      setQueue([]);
      setPlayerState({ current_queue_id: null, current_song_id: null, status: 'idle', estimated_wait_seconds: 0 });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSong = async () => {
    if (!songId || !singer) {
      setError('Song and singer are required');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await addSongToQueue(Number(songId), singer);
      setSongId('');
      setSinger('');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (id: number) => {
    setError(null);
    try {
      await removeQueueItem(id);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleSkip = async () => {
    setError(null);
    try {
      await skip();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handlePlayPause = async () => {
    setError(null);
    try {
      if (playerState.status === 'playing') {
        await pause();
      } else {
        await play();
      }
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const currentSong = useMemo(
    () => library.find((song) => song.id === playerState.current_song_id) ?? null,
    [library, playerState.current_song_id]
  );

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <header className="flex flex-col gap-4 rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-lg shadow-slate-950/20 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Admin Dashboard</p>
            <h1 className="mt-3 text-4xl font-semibold">Karaoke Server</h1>
            <p className="mt-2 text-slate-400">Monitor queue, playback, and library activity in real time.</p>
          </div>
          <div className="flex items-center gap-3">
            {authenticated ? (
              <button
                onClick={handleLogout}
                className="rounded-2xl bg-slate-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-600"
              >
                Logout
              </button>
            ) : null}
            <div className="rounded-2xl bg-slate-800 px-4 py-2 text-sm text-slate-300">
              Status: {authenticated ? 'Authenticated' : 'Guest'}
            </div>
          </div>
        </header>

        {error ? (
          <div className="rounded-3xl border border-rose-500 bg-rose-500/10 p-4 text-rose-200">{error}</div>
        ) : null}

        {loading ? (
          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-10 text-center text-slate-400">Loading dashboard...</div>
        ) : authenticated ? (
          <>
            <section className="grid gap-4 xl:grid-cols-[1.5fr,1fr]">
              <div className="space-y-4">
                <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-lg shadow-slate-950/20">
                  <h2 className="text-xl font-semibold">Now Playing</h2>
                  {currentSong ? (
                    <div className="mt-4 space-y-3">
                      <p className="text-slate-400">Song: <span className="text-white">{currentSong.title ?? currentSong.filename}</span></p>
                      <p className="text-slate-400">Artist: <span className="text-white">{currentSong.artist ?? 'Unknown'}</span></p>
                      <p className="text-slate-400">Status: <span className="text-white capitalize">{playerState.status}</span></p>
                      <p className="text-slate-400">Wait Estimate: <span className="text-white">{formatDuration(playerState.estimated_wait_seconds)}</span></p>
                    </div>
                  ) : (
                    <p className="mt-4 text-slate-400">No song is currently playing.</p>
                  )}
                  <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                    <button
                      onClick={handlePlayPause}
                      className="rounded-2xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
                    >
                      {playerState.status === 'playing' ? 'Pause' : 'Play'}
                    </button>
                    <button
                      onClick={handleSkip}
                      className="rounded-2xl bg-amber-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-amber-400"
                    >
                      Skip
                    </button>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  <StatusCard label="Queue Length" value={queue.length} />
                  <StatusCard label="Active Song" value={currentSong ? currentSong.title ?? 'Unknown' : 'Idle'} />
                  <StatusCard label="Player Status" value={playerState.status} />
                </div>
              </div>

              <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-lg shadow-slate-950/20">
                <h2 className="text-xl font-semibold">Request New Song</h2>
                <div className="mt-5 space-y-4">
                  <label className="block text-sm text-slate-400">
                    Song
                    <select
                      value={songId}
                      onChange={(event) => setSongId(Number(event.target.value) || '')}
                      className="mt-2 w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-slate-500"
                    >
                      <option value="">Select a song</option>
                      {library.map((song) => (
                        <option key={song.id} value={song.id}>
                          {song.title ?? song.filename} {song.artist ? `- ${song.artist}` : ''}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="block text-sm text-slate-400">
                    Singer
                    <input
                      value={singer}
                      onChange={(event) => setSinger(event.target.value)}
                      className="mt-2 w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-slate-500"
                      placeholder="Singer name"
                    />
                  </label>
                  <button
                    onClick={handleAddSong}
                    className="w-full rounded-2xl bg-sky-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-400"
                  >
                    Add to Queue
                  </button>
                </div>
              </div>
            </section>

            <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-lg shadow-slate-950/20">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Upcoming Queue</h2>
                  <p className="mt-2 text-slate-400">Manage requests before they play.</p>
                </div>
              </div>
              <div className="mt-6 flow-root">
                <ul className="divide-y divide-slate-800">
                  {queue.map((item) => (
                    <li key={item.id} className="flex flex-col gap-4 py-4 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="text-base font-semibold text-white">{item.song.title ?? item.song.filename}</p>
                        <p className="mt-1 text-sm text-slate-400">Singer: {item.singer || 'Unknown'}</p>
                        <p className="mt-1 text-sm text-slate-400">Requested: {new Date(item.requested_at).toLocaleString()}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button
                          onClick={() => handleRemove(item.id)}
                          className="rounded-2xl border border-rose-500 px-4 py-2 text-sm font-semibold text-rose-300 transition hover:bg-rose-500/10"
                        >
                          Remove
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
                {!queue.length ? (
                  <p className="mt-6 text-center text-slate-500">No queued songs yet.</p>
                ) : null}
              </div>
            </section>
          </>
        ) : (
          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-8 shadow-lg shadow-slate-950/20">
            <h2 className="text-2xl font-semibold">Admin Login</h2>
            <p className="mt-3 text-slate-400">Enter the 4-digit PIN to access dashboard controls.</p>
            <div className="mt-6 grid gap-4 sm:grid-cols-[1fr,auto]">
              <input
                value={pin}
                onChange={(event) => setPin(event.target.value)}
                className="rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-slate-500"
                placeholder="Enter PIN"
                type="password"
                maxLength={4}
              />
              <button
                onClick={handleLogin}
                className="rounded-2xl bg-sky-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-400"
              >
                Sign In
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
