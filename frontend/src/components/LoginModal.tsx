import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface Props { isOpen: boolean; onClose: () => void }

export default function LoginModal({ isOpen, onClose }: Props) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!username || !password) { setError('Enter username and password'); return }
    setLoading(true); setError('')
    try {
      const body = new URLSearchParams()
      body.append('username', username)
      body.append('password', password)
      const res = await fetch('/api/v1/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: body.toString() })
      const data = await res.json()
      if (!res.ok) { setError(data.detail || 'Login failed'); return }
      localStorage.setItem('nika_token', data.access_token)
      onClose()
      window.location.reload()
    } catch { setError('Network error') } finally { setLoading(false) }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
          <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }}
            onClick={e => e.stopPropagation()}
            className="w-full max-w-sm mx-4 bg-surface-container border border-primary/20 rounded-2xl shadow-2xl overflow-hidden">
            <div className="p-6 border-b border-white/5 bg-primary/5 text-center">
              <div className="w-12 h-12 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center mx-auto mb-3">
                <span className="material-symbols-outlined text-primary text-2xl">security</span>
              </div>
              <h2 className="font-display-mono text-white text-lg font-bold tracking-widest uppercase">NIKA AI</h2>
              <p className="text-on-surface-variant text-xs mt-1">Sign in to continue</p>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="font-display-mono text-[10px] text-primary uppercase tracking-widest block mb-2">Username</label>
                <input type="text" value={username} onChange={e => setUsername(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSubmit()} placeholder="admin1"
                  className="w-full bg-surface-container-high border border-white/10 rounded-lg px-4 py-3 text-white text-sm font-display-mono outline-none focus:border-primary/50 transition-colors placeholder:text-on-surface-variant/30" />
              </div>
              <div>
                <label className="font-display-mono text-[10px] text-primary uppercase tracking-widest block mb-2">Password</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSubmit()} placeholder="••••••••"
                  className="w-full bg-surface-container-high border border-white/10 rounded-lg px-4 py-3 text-white text-sm font-display-mono outline-none focus:border-primary/50 transition-colors placeholder:text-on-surface-variant/30" />
              </div>
              {error && <div className="bg-error/10 border border-error/30 text-error text-xs px-3 py-2 rounded-lg font-display-mono">{error}</div>}
              <div className="text-xs text-on-surface-variant/50 font-display-mono bg-surface-container-high/50 rounded-lg p-3">
                <p className="mb-1 text-primary/70">Demo accounts:</p>
                <p>admin1 / admin123</p>
                <p>operator1 / operator123</p>
              </div>
              <button onClick={handleSubmit} disabled={loading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-primary-container to-secondary-container text-on-primary font-label-sm uppercase tracking-wider font-bold flex items-center justify-center gap-2 disabled:opacity-50">
                {loading ? <><span className="material-symbols-outlined animate-spin text-[18px]">sync</span>Authenticating...</> : <><span className="material-symbols-outlined text-[18px]">login</span>Sign In</>}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
