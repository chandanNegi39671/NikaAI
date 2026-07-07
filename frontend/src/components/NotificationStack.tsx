/**
 * src/components/NotificationStack.tsx
 * ────────────────────────────────────
 * Layout container hosting the live toast list.
 */

import { AnimatePresence } from 'framer-motion'
import { useNotificationStore } from '../store/notificationStore'
import Notification from './Notification'

export default function NotificationStack() {
  const { notifications, dismissNotification } = useNotificationStore()

  return (
    <div className="fixed top-20 right-6 z-50 flex flex-col gap-3 pointer-events-none w-full max-w-sm">
      <AnimatePresence>
        {notifications.map((n) => (
          <Notification
            key={n.id}
            item={n}
            onDismiss={dismissNotification}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}
