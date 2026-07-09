import { useState, useRef, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'

const navLinks = [
  { label: 'DASHBOARD',   to: '/dashboard'   },
  { label: 'MAINTENANCE', to: '/maintenance' },
  { label: 'HISTORY',     to: '/history'     },
  { label: 'CAMERA',      to: '/inspect'     },
  { label: 'COPILOT',     to: '/copilot'     },
  { label: 'REGISTRY',    to: '/registry'    },
  { label: 'INFERENCE',   to: '/inference'   },
  { label: 'AUDIT',       to: '/audit'       },
]

export default function TopBar() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const [showSettings, setShowSettings] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const settingsRef = useRef<HTMLDivElement>(null)
  const profileRef = useRef<HTMLDivElement>(null)

  const token = localStorage.getItem('nika_token')
  const username = token ? (() => {
    try { return JSON.parse(atob(token.split('.')[1])).sub || 'User' }
    catch { return 'User' }
  })() : null

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (settingsRef.current && !settingsRef.current.contains(e.target as Node)) setShowSettings(false)
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) setShowProfile(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleLogout = () => { localStorage.removeItem('nika_token'); window.location.reload() }

  return (
    <header className="fixed top-0 w-full z-50 bg-surface/80 backdrop-blur-xl border-b border-primary/30 shadow-glass">
      <nav className="flex justify-between items-center px-6 md:px-margin-desktop h-16 w-full max-w-[1600px] mx-auto">
        <Link to="/" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-primary-container/20 flex items-center justify-center border border-primary/40">
            <span className="material-symbols-outlined filled text-primary text-[18px]">security</span>
          </div>
          <span className="font-display-mono text-display-mono tracking-widest text-primary-fixed-dim uppercase select-none">NIKA AI</span>
        </Link>

        <div className="hidden md:flex gap-6 items-center">
          {navLinks.map(({ label, to }) => {
            const isActive = pathname.startsWith(to)
            return (
              <Link key={to} to={to} className={`font-label-sm text-label-sm transition-colors duration-300 ${isActive ? 'text-primary font-bold' : 'text-on-surface-variant hover:text-primary'}`}>
                {label}
              </Link>
            )
          })}
        </div>

        <div className="flex items-center gap-4">
          <div className="relative" ref={settingsRef}>
            <span className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors cursor-pointer select-none"
              onClick={() => { setShowSettings(v => !v); setShowProfile(false) }}>settings</span>
            <AnimatePresence>
              {showSettings && (
                <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
                  className="absolute right-0 top-10 w-56 bg-surface-container border border-primary/20 rounded-xl shadow-2xl overflow-hidden z-50">
                  <div className="p-3 border-b border-white/5">
                    <p className="font-display-mono text-[10px] text-primary uppercase tracking-widest">Settings</p>
                  </div>
                  {[
                    { icon: 'dashboard', label: 'Dashboard', to: '/dashboard' },
                    { icon: 'folder', label: 'Model Registry', to: '/registry' },
                    { icon: 'history', label: 'Audit Logs', to: '/audit' },
                    { icon: 'analytics', label: 'Inference History', to: '/inference' },
                  ].map(({ icon, label, to }) => (
                    <button key={to} onClick={() => { navigate(to); setShowSettings(false) }}
                      className="w-full flex items-center gap-3 px-4 py-3 text-sm text-on-surface-variant hover:text-primary hover:bg-primary/5 transition-colors text-left">
                      <span className="material-symbols-outlined text-[18px]">{icon}</span>{label}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="relative" ref={profileRef}>
            <motion.div whileHover={{ scale: 1.05 }} onClick={() => { setShowProfile(v => !v); setShowSettings(false) }}
              className="w-8 h-8 rounded-full bg-primary-container/20 border border-primary/30 flex items-center justify-center overflow-hidden cursor-pointer">
              <span className="material-symbols-outlined text-primary-fixed-dim text-[18px]">person</span>
            </motion.div>
            <AnimatePresence>
              {showProfile && (
                <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
                  className="absolute right-0 top-10 w-56 bg-surface-container border border-primary/20 rounded-xl shadow-2xl overflow-hidden z-50">
                  <div className="p-4 border-b border-white/5 bg-primary/5">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center">
                        <span className="material-symbols-outlined text-primary text-[20px]">person</span>
                      </div>
                      <div>
                        <p className="font-display-mono text-sm text-white font-bold">{username || 'Guest'}</p>
                        <p className="font-display-mono text-[10px] text-primary uppercase tracking-widest">{token ? 'Admin' : 'Not logged in'}</p>
                      </div>
                    </div>
                  </div>
                  {token ? (
                    <>
                      <button onClick={() => { navigate('/dashboard'); setShowProfile(false) }}
                        className="w-full flex items-center gap-3 px-4 py-3 text-sm text-on-surface-variant hover:text-primary hover:bg-primary/5 transition-colors text-left">
                        <span className="material-symbols-outlined text-[18px]">account_circle</span>My Profile
                      </button>
                      <button onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-4 py-3 text-sm text-error hover:bg-error/5 transition-colors text-left border-t border-white/5">
                        <span className="material-symbols-outlined text-[18px]">logout</span>Sign Out
                      </button>
                    </>
                  ) : (
                    <div className="p-4 text-center"><p className="text-xs text-on-surface-variant">Not authenticated</p></div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </nav>
    </header>
  )
}
