'use client';
import { useState, useEffect, useCallback } from 'react';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/traffic';

type MessageHandler = (data: Record<string, unknown>) => void;

interface WSHook {
  connected: boolean;
  lastMessage: Record<string, unknown> | null;
  sendMessage: (msg: string) => void;
}

export function useWebSocket(onMessage?: MessageHandler): WSHook {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<Record<string, unknown> | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    let socket: WebSocket;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    function connect() {
      try {
        socket = new WebSocket(WS_URL);
        socket.onopen = () => {
          setConnected(true);
          // Start heartbeat
          const ping = setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) socket.send('ping');
          }, 25000);
          (socket as WebSocket & { _ping?: ReturnType<typeof setInterval> })._ping = ping;
        };
        socket.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            setLastMessage(data);
            onMessage?.(data);
          } catch {}
        };
        socket.onclose = () => {
          setConnected(false);
          reconnectTimer = setTimeout(connect, 3000);
        };
        socket.onerror = () => {
          socket.close();
        };
        setWs(socket);
      } catch {
        reconnectTimer = setTimeout(connect, 5000);
      }
    }

    connect();
    return () => {
      clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []); // eslint-disable-line

  const sendMessage = useCallback((msg: string) => {
    if (ws?.readyState === WebSocket.OPEN) ws.send(msg);
  }, [ws]);

  return { connected, lastMessage, sendMessage };
}
