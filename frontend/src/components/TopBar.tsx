/**
 * components/TopBar.tsx
 * ─────────────────────
 * Fixed top navigation bar — shared across all pages.
 * Desktop: logo + nav links + settings + avatar
 * Mobile: logo + settings + avatar (nav moves to BottomNav)
 */

import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'

const navLinks = [
  { label: 'DASHBOARD', to: '/dashboard' },
  { label: 'HISTORY',   to: '/history'   },
  { label: 'CAMERA',    to: '/inspect'   },
]

export default function TopBar() {
  const { pathname } = useLocation()

  return (
    <header className="fixed top-0 w-full z-50 bg-surface/80 backdrop-blur-xl border-b border-primary/30 shadow-glass">
      <nav className="flex justify-between items-center px-6 md:px-margin-desktop h-16 w-full max-w-[1600px] mx-auto">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-primary-container/20 flex items-center justify-center border border-primary/40">
            <span className="material-symbols-outlined filled text-primary text-[18px]">security</span>
          </div>
          <span className="font-display-mono text-display-mono tracking-widest text-primary-fixed-dim uppercase select-none">
            NIKA AI
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex gap-8 items-center">
          {navLinks.map(({ label, to }) => {
            const isActive = pathname.startsWith(to)
            return (
              <Link
                key={to}
                to={to}
                className={`font-label-sm text-label-sm transition-colors duration-300 ${
                  isActive
                    ? 'text-primary font-bold'
                    : 'text-on-surface-variant hover:text-primary'
                }`}
              >
                {label}
              </Link>
            )
          })}
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-4">
          <span className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors cursor-pointer select-none">
            settings
          </span>
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="w-8 h-8 rounded-full bg-primary-container/20 border border-primary/30 flex items-center justify-center overflow-hidden cursor-pointer"
          >
            <span className="material-symbols-outlined text-primary-fixed-dim text-[18px]">person</span>
          </motion.div>
        </div>
      </nav>
    </header>
  )
}
