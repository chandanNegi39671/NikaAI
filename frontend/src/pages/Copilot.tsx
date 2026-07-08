/**
 * pages/Copilot.tsx
 * ──────────────────
 * Upgraded AI Quality Copilot Panel.
 * Implements persistent chat logs, keyword RAG manual suggestions,
 * and high-fidelity glassmorphism console controls.
 */

import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import TopBar from '../components/TopBar'
import BottomNav from '../components/BottomNav'
import GlassCard from '../components/GlassCard'
import LedPulse from '../components/LedPulse'
import { askCopilot, getCopilotHistory, clearCopilotHistory } from '../lib/apiClient'
import type { ConversationMessage } from '../types'

export default function Copilot() {
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [input, setInput] = useState('')
  const [sessionKey, setSessionKey] = useState('')
  const [loading, setLoading] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  // Initialize unique session key
  useEffect(() => {
    let key = localStorage.getItem('nika_copilot_session')
    if (!key) {
      key = `session_${Math.random().toString(36).substring(2, 11)}`
      localStorage.setItem('nika_copilot_session', key)
    }
    setSessionKey(key)
    loadHistory(key)
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadHistory = async (key: string) => {
    try {
      const history = await getCopilotHistory(key)
      setMessages(history)
    } catch (err) {
      console.error('Failed to load chat history', err)
    }
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: ConversationMessage = {
      id: `temp_u_${Date.now()}`,
      role: 'user',
      content: input,
    }
    setMessages((prev) => [...prev, userMessage])
    const promptText = input
    setInput('')
    setLoading(true)

    try {
      const response = await askCopilot(promptText, sessionKey)
      const assistantMessage: ConversationMessage = {
        id: `temp_a_${Date.now()}`,
        role: 'assistant',
        content: response.answer,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      console.error(err)
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          role: 'assistant',
          content: '⚠️ Failed to connect to Copilot engine. Verify backend is active.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleClearHistory = async () => {
    if (!window.confirm('Wipe chat log from registry database?')) return
    try {
      await clearCopilotHistory(sessionKey)
      setMessages([])
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="min-h-screen bg-background text-on-surface flex flex-col pt-20 pb-24 md:pb-8">
      <TopBar />

      <main className="flex-1 max-w-[1400px] w-full mx-auto px-6 md:px-margin-desktop grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Side: System Context */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <GlassCard rimLight className="p-6 border-t border-primary/30 flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <LedPulse active={true} />
              <span className="font-display-mono text-label-sm text-primary tracking-wider uppercase">
                Copilot System Ready
              </span>
            </div>
            <h2 className="font-headline-lg text-2xl text-on-surface">Factory Intelligence</h2>
            <p className="font-body-md text-sm text-on-surface-variant leading-relaxed">
              Grounding is provided dynamically by active Knowledge base manuals and standard defect actions stored in Factory Memory.
            </p>
            
            <div className="border-t border-outline-variant/30 my-2" />
            
            <div className="space-y-3">
              <span className="font-display-mono text-[11px] text-on-surface-variant uppercase tracking-widest block">
                Active Session
              </span>
              <code className="text-xs bg-surface-container-lowest/50 p-2 rounded block select-all font-display-mono text-primary border border-outline-variant/20">
                {sessionKey}
              </code>
            </div>

            <button
              onClick={handleClearHistory}
              className="mt-4 font-label-sm text-label-sm uppercase tracking-wider text-error hover:text-white bg-error-container/20 hover:bg-error-container border border-error/30 rounded-full px-4 py-2 transition-all"
            >
              Clear Session
            </button>
          </GlassCard>

          <GlassCard className="p-6 flex flex-col gap-4">
            <h3 className="font-headline-lg text-lg text-on-surface">Quick Prompts</h3>
            <div className="flex flex-col gap-2">
              <button
                onClick={() => setInput('SOP guidelines for surface cracks')}
                className="text-xs text-left p-2.5 rounded bg-surface-variant/25 hover:bg-primary-container/10 border border-outline-variant/10 text-on-surface-variant hover:text-primary transition-all"
              >
                SOP guidelines for surface cracks
              </button>
              <button
                onClick={() => setInput('Conveyor guide rail scratch fixes')}
                className="text-xs text-left p-2.5 rounded bg-surface-variant/25 hover:bg-primary-container/10 border border-outline-variant/10 text-on-surface-variant hover:text-primary transition-all"
              >
                Conveyor guide rail scratch fixes
              </button>
              <button
                onClick={() => setInput('Hydraulic dent pressure limits')}
                className="text-xs text-left p-2.5 rounded bg-surface-variant/25 hover:bg-primary-container/10 border border-outline-variant/10 text-on-surface-variant hover:text-primary transition-all"
              >
                Hydraulic dent pressure limits
              </button>
            </div>
          </GlassCard>
        </div>

        {/* Right Side: Chat Console */}
        <div className="lg:col-span-3 flex flex-col h-[70vh] lg:h-[78vh]">
          <GlassCard rimLight className="flex-1 flex flex-col overflow-hidden border-t border-primary/30 p-6">
            
            {/* Header */}
            <div className="flex justify-between items-center pb-4 border-b border-outline-variant/30 mb-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">smart_toy</span>
                <span className="font-display-mono text-display-mono tracking-widest text-primary uppercase">
                  Quality Copilot Console
                </span>
              </div>
              <span className="text-[10px] font-display-mono bg-primary-container/20 text-primary border border-primary/30 px-2 py-0.5 rounded">
                Gemma RAG v1.2
              </span>
            </div>

            {/* Chat Body */}
            <div className="flex-1 overflow-y-auto pr-2 space-y-4 scrollbar-thin scrollbar-thumb-surface-variant">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center opacity-40 py-12">
                  <span className="material-symbols-outlined text-[60px] text-primary mb-3">forum</span>
                  <p className="font-display-mono text-sm tracking-wider uppercase">Console Session Empty</p>
                  <p className="text-xs max-w-sm mt-1">Ask the assistant about manufacturing defect SOPs, machine calibration guidelines, or line analytics.</p>
                </div>
              ) : (
                messages.map((msg, index) => {
                  const isUser = msg.role === 'user'
                  return (
                    <motion.div
                      key={msg.id || index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[85%] md:max-w-[70%] p-4 rounded-2xl relative border ${
                          isUser
                            ? 'bg-primary-container/20 border-primary/30 text-on-surface rounded-tr-none'
                            : 'bg-surface-variant/20 border-outline-variant/30 text-on-surface rounded-tl-none'
                        }`}
                      >
                        <span className="absolute -top-3 left-3 text-[9px] font-display-mono text-primary uppercase bg-surface px-1.5 rounded border border-outline-variant/20">
                          {isUser ? 'Operator' : 'Copilot'}
                        </span>
                        <div className="text-sm leading-relaxed whitespace-pre-line mt-1">
                          {msg.content}
                        </div>
                      </div>
                    </motion.div>
                  )
                })
              )}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-surface-variant/20 border border-outline-variant/30 p-4 rounded-2xl rounded-tl-none flex items-center gap-2">
                    <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:0.2s]" />
                    <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:0.4s]" />
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input Form */}
            <form onSubmit={handleSend} className="mt-4 flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask Nika AI Copilot..."
                className="flex-1 bg-surface-container-lowest/80 border border-outline-variant/35 rounded-full px-5 py-3 text-sm focus:outline-none focus:border-primary text-white transition-all font-sans placeholder-on-surface-variant/40"
              />
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={loading || !input.trim()}
                className="w-12 h-12 rounded-full bg-primary hover:bg-primary-container border border-primary/20 text-on-primary flex items-center justify-center shadow-primary-glow cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <span className="material-symbols-outlined">send</span>
              </motion.button>
            </form>
          </GlassCard>
        </div>
      </main>
      <BottomNav />
    </div>
  )
}
