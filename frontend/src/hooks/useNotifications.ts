/**
 * src/hooks/useNotifications.ts
 * ──────────────────────────────
 * Hook exposing simplified triggers for the notificationStore.
 */

import { useCallback } from 'react'
import { useNotificationStore } from '../store/notificationStore'

export function useNotifications() {
  const { notifications, addNotification, dismissNotification, clearAll } =
    useNotificationStore()

  const success = useCallback(
    (title: string, message?: string, durationMs?: number) => {
      addNotification(title, 'success', message, durationMs)
    },
    [addNotification]
  )

  const error = useCallback(
    (title: string, message?: string, durationMs?: number) => {
      addNotification(title, 'error', message, durationMs)
    },
    [addNotification]
  )

  const warning = useCallback(
    (title: string, message?: string, durationMs?: number) => {
      addNotification(title, 'warning', message, durationMs)
    },
    [addNotification]
  )

  const info = useCallback(
    (title: string, message?: string, durationMs?: number) => {
      addNotification(title, 'info', message, durationMs)
    },
    [addNotification]
  )

  return {
    notifications,
    success,
    error,
    warning,
    info,
    dismissNotification,
    clearAll,
  }
}
