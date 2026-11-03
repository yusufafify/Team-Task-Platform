import { useQueryClient, type QueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { AppState } from 'react-native';

import { addMessage, syncOpenChats } from '@/features/chat/query';
import { NOTIFICATIONS_KEY } from '@/features/notifications/query';
import { API_URL, http } from '@/lib/http';
import { getTokens } from '@/lib/session';

import type { LiveEvent } from './types';

// React Native's WebSocket takes headers as a third argument, which the DOM typings in scope don't know.
const NativeWebSocket = WebSocket as unknown as new (
  url: string,
  protocols: null,
  options: { headers: Record<string, string> },
) => WebSocket;

const LIVE_URL = `${API_URL.replace(/^http/, 'ws')}/api/v1/ws/`;
const TOKEN_EXPIRED = 4401;
const MAX_DELAY_MS = 30_000;
const POLL_EVERY_MS = 10_000;
const POLL_IDLE_LIMIT_MS = 120_000;
// A blip can pass unnoticed. The first drop isn't a failed reconnect, so 3 failed reconnects is 4.
const SHOW_DOWN_AFTER = 2;
const POLL_AFTER = 4;

let down = false;
const listeners = new Set<() => void>();

function setDown(next: boolean) {
  if (next === down) return;
  down = next;
  listeners.forEach((listener) => listener());
}

// For the "live updates paused" note on chat.
export function useLiveDown(): boolean {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    () => down,
    () => false,
  );
}

// 1s doubling to 30s, with up to 20% jitter.
function reconnectDelay(failures: number) {
  return Math.min(1000 * 2 ** (failures - 1), MAX_DELAY_MS) * (1 + Math.random() * 0.2);
}

// Unknown types fall through untouched, so the API can add new ones.
function applyEvent(client: QueryClient, event: LiveEvent) {
  if (event.type === 'message') addMessage(client, event.data);
  if (event.type === 'notification') {
    void client.invalidateQueries({ queryKey: NOTIFICATIONS_KEY });
    if (event.data.kind === 'report_ready') void client.invalidateQueries({ queryKey: ['reports'] });
    if (event.data.task !== null) {
      void client.invalidateQueries({ queryKey: ['tasks'] });
      void client.invalidateQueries({ queryKey: ['comments', event.data.task] });
    }
  }
}

// REST stays the record, so this runs after every connect and on each fallback poll.
function catchUp(client: QueryClient) {
  void client.invalidateQueries({ queryKey: NOTIFICATIONS_KEY });
  void syncOpenChats(client);
}

// One socket per signed-in person. Mount once, inside the signed-in part of the app.
export function useLiveSocket() {
  const queryClient = useQueryClient();
  const [failures, setFailures] = useState(0);
  const noteInput = useRef<() => void>(() => undefined);
  const shouldPoll = failures >= POLL_AFTER;

  useEffect(() => {
    let socket: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let dropped = 0;
    let stopped = false;
    let background = AppState.currentState === 'background';

    function report(count: number) {
      setFailures(count);
      setDown(count >= SHOW_DOWN_AFTER);
    }

    function close() {
      const open = socket;
      socket = null;
      open?.close();
    }

    function connect() {
      const access = getTokens()?.access;
      if (!access || socket) return;
      const opened = new NativeWebSocket(LIVE_URL, null, { headers: { Authorization: `Bearer ${access}` } });
      socket = opened;
      opened.onopen = () => {
        dropped = 0;
        report(0);
        catchUp(queryClient);
      };
      opened.onmessage = ({ data }) => {
        try {
          applyEvent(queryClient, JSON.parse(String(data)) as LiveEvent);
        } catch {
          // A frame that isn't JSON is ignored; the next catch-up recovers anything it held.
        }
      };
      opened.onclose = ({ code }) => void onClose(opened, code);
    }

    async function onClose(closed: WebSocket, code?: number) {
      // Closed on purpose, by going to the background or unmounting.
      if (socket !== closed) return;
      socket = null;
      // Goes through the facade, which refreshes the token, or signs out if the refresh is refused.
      if (code === TOKEN_EXPIRED) await http.get('auth/me/').catch(() => undefined);
      if (stopped || background) return;
      dropped += 1;
      report(dropped);
      retry = setTimeout(connect, reconnectDelay(dropped));
    }

    // The overview's mobile rule: no socket in the background, and a fresh one on return.
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'background') {
        background = true;
        clearTimeout(retry);
        close();
      } else if (state === 'active' && background) {
        background = false;
        connect();
      }
    });

    if (!background) connect();
    return () => {
      stopped = true;
      clearTimeout(retry);
      close();
      subscription.remove();
      setDown(false);
    };
  }, [queryClient]);

  // The fallback while sockets seem blocked: at most every 10s, only in the foreground,
  // and only within 2 minutes of the last touch.
  useEffect(() => {
    if (!shouldPoll) return;
    let timer: ReturnType<typeof setInterval> | undefined;
    let lastInput = Date.now();

    function stop() {
      clearInterval(timer);
      timer = undefined;
    }
    function poll() {
      if (Date.now() - lastInput > POLL_IDLE_LIMIT_MS) stop();
      else catchUp(queryClient);
    }
    function onInput() {
      lastInput = Date.now();
      if (AppState.currentState === 'active') timer ??= setInterval(poll, POLL_EVERY_MS);
    }

    noteInput.current = onInput;
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') onInput();
      else stop();
    });
    onInput();
    return () => {
      stop();
      noteInput.current = () => undefined;
      subscription.remove();
    };
  }, [shouldPoll, queryClient]);

  return { noteInput: () => noteInput.current() };
}
