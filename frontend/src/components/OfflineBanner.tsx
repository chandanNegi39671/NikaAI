/**
 * src/components/OfflineBanner.tsx
 * ────────────────────────────────
 * Monitors the browser's connectivity status and shows a premium floating offline warning.
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function OfflineBanner() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return (
    <AnimatePresence>
      {!isOnline && (
        <motion.div
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -50 }}
          className="fixed top-18 left-1/2 -translate-x-1/2 z-50 w-[90%] max-w-md pointer-events-auto"
        >
          <div className="glass-panel border border-error/35 bg-error-container/30 backdrop-blur-xl px-4 py-3 rounded-full flex items-center justify-between shadow-glass">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-error animate-pulse" style={{ fontVariationSettings: "'FILL' 1" }}>
                wifi_off
              </span>
              <div>
                <p className="text-on-error-container font-semibold text-xs leading-none">
                  Factory Offline
                </p>
                <p className="text-on-error-container/60 text-[10px] font-display-mono mt-0.5 uppercase">
                  Inspections running locally. Sync disabled.
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOnline(navigator.onLine)}
              className="text-xs bg-error text-on-error font-display-mono uppercase font-bold px-3 py-1 rounded-full hover:bg-error/90 active:scale-95 transition-all"
            >
              Retry
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
