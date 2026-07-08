/**
 * components/BottomNav.tsx
 * ─────────────────────────
 * Mobile-only bottom pill navigation bar.
 * Visible only on screens < md breakpoint (hidden md:hidden).
 */

import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'

const items = [
  { icon: 'photo_camera', label: 'Camera',      to: '/inspect'      },
  { icon: 'history',      label: 'History',     to: '/history'      },
  { icon: 'build',        label: 'Maintenance', to: '/maintenance'  },
  { icon: 'dashboard',    label: 'Dashboard',   to: '/dashboard'    },
  { icon: 'smart_toy',    label: 'Copilot',     to: '/copilot'      },
]

export default function BottomNav() {
  const { pathname } = useLocation()

  return (
    <nav className="md:hidden fixed bottom-6 left-1/2 -translate-x-1/2 w-[90%] z-50
                    bg-surface-container-low/80 backdrop-blur-[20px] rounded-full
                    border border-primary/20 shadow-glass h-16
                    flex justify-around items-center px-4 max-w-lg">
      {items.map(({ icon, label, to }) => {
        const isActive = pathname.startsWith(to)
        return (
          <Link key={to} to={to}>
            <motion.div
              whileTap={{ scale: 0.92 }}
              className={`flex flex-col items-center justify-center px-3 py-1.5 rounded-full transition-all duration-200 ${
                isActive
                  ? 'text-primary-fixed-dim bg-primary-container/20 shadow-primary-glow scale-90'
                  : 'text-on-surface-variant/60 hover:text-primary-fixed'
              }`}
            >
              <span
                className="material-symbols-outlined text-[20px]"
                style={isActive ? { fontVariationSettings: "'FILL' 1" } : undefined}
              >
                {icon}
              </span>
              <span className={`font-label-sm text-[10px] mt-0.5 ${isActive ? 'font-bold' : ''}`}>
                {label}
              </span>
            </motion.div>
          </Link>
        )
      })}
    </nav>
  )
}
