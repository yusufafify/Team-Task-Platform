import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { QueryClient } from '@tanstack/react-query'
import { addMessage, syncOpenChats } from '@/features/chat/query'
import { NOTIFICATIONS_KEY } from '@/features/notifications/query'
import { API_ROOT, BASE_URL } from '@/lib/http/const'
import { endExpiredSession } from '@/lib/http/errors'
import { http } from '@/lib/http/fetch_instance'
import type { LiveEvent } from './types'

const TOKEN_EXPIRED = 4401
const MAX_DELAY_MS = 30_000
const POLL_EVERY_MS = 10_000
const POLL_IDLE_LIMIT_MS = 120_000
// A blip can pass unnoticed. The first drop isn't a failed reconnect, so 3 failed reconnects is 4.
const SHOW_DOWN_AFTER = 2
const POLL_AFTER = 4

function liveUrl() {
  const url = new URL(`${API_ROOT}ws/`, BASE_URL || window.location.origin)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return url
}

// 1s doubling to 30s, with up to 20% jitter.
function reconnectDelay(failures: number) {
  const delay = Math.min(1000 * 2 ** (failures - 1), MAX_DELAY_MS)
  return delay * (1 + Math.random() * 0.2)
}

// Any other type falls through untouched, so the API can add new ones.
function applyEvent(client: QueryClient, event: LiveEvent) {
  if (event.type === 'message') addMessage(client, event.data)
  if (event.type === 'notification') {
    void client.invalidateQueries({ queryKey: NOTIFICATIONS_KEY })
    if (event.data.kind === 'report_ready') {
      void client.invalidateQueries({ queryKey: ['reports'] })
    }
    if (event.data.task !== null) {
      void client.invalidateQueries({ queryKey: ['tasks'] })
      void client.invalidateQueries({
        queryKey: ['comments', event.data.task],
      })
    }
  }
}

// REST stays the record, so this runs after every connect and on each fallback poll.
function catchUp(client: QueryClient) {
  void client.invalidateQueries({ queryKey: NOTIFICATIONS_KEY })
  void syncOpenChats(client)
}

export function useLiveSocket() {
  const queryClient = useQueryClient()
  const [failures, setFailures] = useState(0)
  const shouldPoll = failures >= POLL_AFTER

  useEffect(() => {
    let socket: WebSocket | null = null
    let retry: ReturnType<typeof setTimeout> | undefined
    let dropped = 0
    let stopped = false

    function connect() {
      const opened = new WebSocket(liveUrl())
      socket = opened
      opened.onopen = () => {
        dropped = 0
        setFailures(0)
        catchUp(queryClient)
      }
      opened.onmessage = ({ data }) => {
        applyEvent(queryClient, JSON.parse(String(data)) as LiveEvent)
      }
      opened.onclose = ({ code }) => void onClose(code)
    }

    async function onClose(code: number) {
      socket = null
      // Goes through the facade's refresh, so a token another tab rotated still counts.
      if (code === TOKEN_EXPIRED && !stopped) {
        await http.get('auth/me/').catch(endExpiredSession)
      }
      if (stopped) return

      dropped += 1
      setFailures(dropped)
      if (!document.hidden) retry = setTimeout(connect, reconnectDelay(dropped))
    }

    function onVisibilityChange() {
      if (document.hidden || socket || stopped) return
      clearTimeout(retry)
      connect()
    }

    connect()
    document.addEventListener('visibilitychange', onVisibilityChange)
    return () => {
      stopped = true
      clearTimeout(retry)
      socket?.close()
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
  }, [queryClient])

  useEffect(() => {
    if (!shouldPoll) return

    let timer: ReturnType<typeof setInterval> | undefined
    let lastInput = Date.now()

    function stop() {
      clearInterval(timer)
      timer = undefined
    }
    function poll() {
      if (Date.now() - lastInput > POLL_IDLE_LIMIT_MS) stop()
      else catchUp(queryClient)
    }
    function onInput() {
      lastInput = Date.now()
      timer ??= setInterval(poll, POLL_EVERY_MS)
    }
    function onVisibilityChange() {
      if (document.hidden) stop()
      else onInput()
    }

    if (!document.hidden) onInput()
    window.addEventListener('pointerdown', onInput)
    window.addEventListener('keydown', onInput)
    window.addEventListener('focus', onInput)
    document.addEventListener('visibilitychange', onVisibilityChange)
    return () => {
      stop()
      window.removeEventListener('pointerdown', onInput)
      window.removeEventListener('keydown', onInput)
      window.removeEventListener('focus', onInput)
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
  }, [shouldPoll, queryClient])

  return { isDown: failures >= SHOW_DOWN_AFTER }
}
