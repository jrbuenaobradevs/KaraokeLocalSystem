import { useEffect, useRef } from 'react';
import { DashboardEvent } from './types';

export function useWebsocket(onMessage: (event: DashboardEvent) => void) {
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const base = import.meta.env.VITE_API_BASE ?? window.location.origin;
    const wsUrl = base.replace(/^http/, 'ws') + '/ws/library';
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.addEventListener('message', (event) => {
      try {
        const payload = JSON.parse(event.data) as DashboardEvent;
        onMessage(payload);
      } catch (error) {
        console.warn('Invalid websocket event', error);
      }
    });

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [onMessage]);
}
