/**
 * src/store/notificationStore.ts
 * ───────────────────────────────
 * Zustand store for a global toast notification queue.
 */

import { create } from 'zustand'
import type { NotificationItem, NotificationType } from '../types'

interface NotificationStore {
  notifications: NotificationItem[]
  addNotification: (title: string, type: NotificationType, message?: string, durationMs?: number) => void
  dismissNotification: (id: string) => void
  clearAll: () => void
}

export const useNotificationStore = create<NotificationStore>((set) => ({
  notifications: [],

  addNotification: (title, type, message, durationMs = 5000) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newNotification: NotificationItem = {
      id,
      type,
      title,
      message,
      durationMs,
      timestamp: Date.now(),
    }

    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }))
  },

  dismissNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  clearAll: () => set({ notifications: [] }),
}))
