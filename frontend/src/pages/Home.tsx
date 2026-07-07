/**
 * pages/Home.tsx
 * ───────────────
 * Landing page — faithfully converted from design/nika_ai_home/code.html
 *
 * Sections:
 *   1. Hero — animated headline, magnetic CTA button, live stats glass card
 *   2. Scroll indicator
 *   3. Product Story — 2-col text + image with progress bar
 *   4. Bento Grid — 3-card tech specs
 *   5. Footer
 */

import { useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, useInView } from 'framer-motion'
import TopBar from '../components/TopBar'
import BottomNav from '../components/BottomNav'
import LedPulse from '../components/LedPulse'

// ── Framer Motion variants ────────────────────────────────────────────────────
const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (delay = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.8, delay, ease: [0.2, 0.8, 0.2, 1] },
  }),
}

// ── Magnetic button hook ───────────────────────────────────────────────────────
function useMagneticButton() {
  const ref = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const btn = ref.current
    if (!btn) return

    const onMove = (e: MouseEvent) => {
      const rect = btn.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top
      const deltaX = (x - rect.width / 2) / 5
      const deltaY = (y - rect.height / 2) / 5
      btn.style.transform = `translate(${deltaX}px, ${deltaY}px)`
    }
    const onLeave = () => {
      btn.style.transform = 'translate(0, 0)'
    }

    btn.addEventListener('mousemove', onMove)
    btn.addEventListener('mouseleave', onLeave)
    return () => {
      btn.removeEventListener('mousemove', onMove)
      btn.removeEventListener('mouseleave', onLeave)
    }
  }, [])

  return ref
}

// ── Section wrapper with scroll reveal ────────────────────────────────────────
function RevealSection({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={inView ? 'visible' : 'hidden'}
      custom={delay}
      variants={fadeUp}
    >
      {children}
    </motion.div>
  )
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function Home() {
  const navigate = useNavigate()
  const magneticRef = useMagneticButton()

  return (
    <div className="text-on-surface font-body-md">
      <TopBar />

      {/* ── Hero Section ─────────────────────────────────────────────── */}
      <main className="relative min-h-screen w-full flex flex-col items-center justify-center pt-16 overflow-hidden">

        {/* Background ambient glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-primary/5 blur-[120px] rounded-full" />
          <div className="absolute bottom-0 right-1/4 w-[400px] h-[300px] bg-secondary-container/10 blur-[80px] rounded-full" />
        </div>

        {/* Hero content */}
        <div className="relative z-10 container mx-auto px-6 text-center">

          {/* Headline */}
          <motion.div
            initial="hidden"
            animate="visible"
            custom={0.1}
            variants={fadeUp}
          >
            <h1 className="font-headline-xl text-headline-xl md:text-[120px] md:leading-[0.9]
                           text-on-surface font-extrabold tracking-tighter mb-4">
              NIKA AI
            </h1>
            <p className="font-display-mono text-display-mono text-primary-fixed-dim
                          tracking-[0.3em] uppercase mb-12">
              Your AI Quality Engineer
            </p>
          </motion.div>

          {/* CTA + Stats Card */}
          <motion.div
            initial="hidden"
            animate="visible"
            custom={0.3}
            variants={fadeUp}
            className="flex flex-col items-center gap-8"
          >
            {/* Magnetic CTA button */}
            <button
              ref={magneticRef}
              id="cta-button"
              onClick={() => navigate('/inspect')}
              className="magnetic-button group relative px-10 py-5
                         bg-gradient-to-r from-primary-container to-secondary-container
                         rounded-full text-on-primary font-bold text-lg overflow-hidden
                         shadow-primary-glow hover:shadow-primary-glow-lg transition-all"
            >
              <span className="relative z-10 flex items-center gap-2">
                Start Inspection
                <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">
                  arrow_forward
                </span>
              </span>
              <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
            </button>

            {/* Floating glass stats card */}
            <div className="glass-card p-6 rounded-2xl max-w-sm w-full relative">
              <div className="rim-light absolute inset-0 rounded-2xl pointer-events-none opacity-50" />
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <LedPulse />
                  <span className="font-display-mono text-[10px] text-on-surface-variant tracking-widest uppercase">
                    Live Factory Stats
                  </span>
                </div>
                <span className="material-symbols-outlined text-primary-fixed-dim text-sm">factory</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-left border-l border-primary/20 pl-4">
                  <p className="font-display-mono text-primary text-xl">99.8%</p>
                  <p className="font-label-sm text-label-sm text-on-surface-variant/60 uppercase">Accuracy</p>
                </div>
                <div className="text-left border-l border-primary/20 pl-4">
                  <p className="font-display-mono text-on-surface text-xl">12.4k</p>
                  <p className="font-label-sm text-label-sm text-on-surface-variant/60 uppercase">Inspected</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 opacity-50">
          <span className="font-display-mono text-[10px] tracking-[0.2em] uppercase">Scroll</span>
          <div className="w-[1px] h-12 bg-gradient-to-b from-primary to-transparent" />
        </div>
      </main>

      {/* ── Product Story Section ─────────────────────────────────────── */}
      <section className="relative bg-surface py-xl border-t border-white/5">
        <div className="container mx-auto px-6 md:px-margin-desktop">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-gutter items-center">

            {/* Text column */}
            <RevealSection delay={0.1}>
              <div className="space-y-md">
                <h2 className="font-headline-lg text-headline-lg text-on-surface max-w-md">
                  Precision engineering meets neural architecture.
                </h2>
                <p className="text-on-surface-variant text-body-lg font-body-lg leading-relaxed max-w-lg">
                  NIKA AI provides sub-millimeter visual inspection at line speeds, identifying structural
                  micro-fractures and surface irregularities that escape the human eye. Our proprietary
                  industrial vision models are trained on millions of aerospace-grade components.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-8">
                  {[
                    {
                      icon: 'biotech',
                      title: 'Neural Scan',
                      desc: 'Deep learning analysis of material surface density.',
                    },
                    {
                      icon: 'speed',
                      title: 'Line Velocity',
                      desc: 'Zero-latency processing for high-volume manufacturing.',
                    },
                  ].map(({ icon, title, desc }) => (
                    <motion.div
                      key={title}
                      whileHover={{ borderColor: 'rgba(251,186,100,0.3)' }}
                      className="p-6 border border-primary/10 rounded-xl transition-all group"
                    >
                      <span className="material-symbols-outlined text-primary-fixed-dim mb-4 block group-hover:scale-110 transition-transform">
                        {icon}
                      </span>
                      <h4 className="font-display-mono text-primary mb-2 uppercase text-xs tracking-widest">
                        {title}
                      </h4>
                      <p className="text-on-surface-variant/70 text-sm">{desc}</p>
                    </motion.div>
                  ))}
                </div>
              </div>
            </RevealSection>

            {/* Image column */}
            <RevealSection delay={0.25}>
              <div className="relative group">
                <div className="absolute -inset-4 bg-primary/5 rounded-3xl blur-3xl group-hover:bg-primary/10 transition-all duration-700" />
                <div className="relative rounded-2xl overflow-hidden border border-primary/20 aspect-video shadow-2xl bg-surface-container-high flex items-center justify-center">
                  {/* Stylized placeholder for robotic inspection */}
                  <div className="w-full h-full bg-gradient-to-br from-surface-container-high to-surface-container relative">
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="material-symbols-outlined text-primary/20 text-[180px]">
                        precision_manufacturing
                      </span>
                    </div>
                    <div className="absolute inset-0 bg-gradient-to-t from-primary/10 to-transparent" />
                  </div>
                  {/* Progress bar overlay */}
                  <div className="absolute bottom-0 left-0 w-full h-1 bg-surface-variant">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: '66%' }}
                      transition={{ delay: 0.8, duration: 1.5, ease: 'easeOut' }}
                      className="h-full bg-primary shadow-[0_0_10px_#fbba64]"
                    />
                  </div>
                </div>
              </div>
            </RevealSection>
          </div>
        </div>
      </section>

      {/* ── Bento Grid Tech Specs ─────────────────────────────────────── */}
      <section className="py-xl bg-surface-dim">
        <div className="container mx-auto px-6 md:px-margin-desktop">
          <RevealSection>
            <div className="text-center mb-16">
              <span className="font-display-mono text-primary-fixed-dim text-xs tracking-[0.5em] uppercase">
                Core Integration
              </span>
              <h3 className="font-headline-lg text-headline-lg text-on-surface mt-4">
                The Intelligence layer.
              </h3>
            </div>
          </RevealSection>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

            {/* Large feature card */}
            <RevealSection delay={0.1}>
              <div className="md:col-span-2 glass-card rounded-2xl p-8 flex flex-col justify-between min-h-[320px]">
                <div>
                  <span className="material-symbols-outlined text-primary text-4xl mb-6 block">
                    query_stats
                  </span>
                  <h4 className="text-2xl font-bold mb-4">Predictive Failure Modeling</h4>
                  <p className="text-on-surface-variant max-w-md">
                    Our AI doesn't just find defects; it predicts maintenance windows by analyzing
                    wear patterns across your entire production fleet.
                  </p>
                </div>
                <div className="mt-8 flex gap-4">
                  {['Edge Optimized', 'No-Cloud Option'].map((tag) => (
                    <span
                      key={tag}
                      className="px-4 py-2 bg-primary/10 border border-primary/20 rounded-full
                                 font-display-mono text-[10px] uppercase text-primary"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </RevealSection>

            {/* Security card */}
            <RevealSection delay={0.2}>
              <div className="bg-surface-container-high rounded-2xl p-8 border border-white/5 flex flex-col items-center text-center justify-center min-h-[320px]">
                <div className="w-20 h-20 rounded-full border border-primary/20 flex items-center justify-center mb-6">
                  <span className="material-symbols-outlined text-primary text-3xl">security</span>
                </div>
                <h4 className="text-xl font-bold mb-2">Vault-Grade Security</h4>
                <p className="text-on-surface-variant text-sm">
                  On-premise deployment ensures your proprietary designs never leave your network.
                </p>
              </div>
            </RevealSection>

            {/* ERP card */}
            <RevealSection delay={0.3}>
              <div className="bg-surface-container rounded-2xl p-8 border border-white/5">
                <span className="material-symbols-outlined text-primary-fixed-dim mb-4 block">hub</span>
                <h4 className="font-bold mb-2">Unified ERP Sync</h4>
                <p className="text-on-surface-variant text-sm">
                  Direct bridge to SAP, Oracle, and Microsoft Dynamics.
                </p>
              </div>
            </RevealSection>

            {/* Adaptive learning card */}
            <RevealSection delay={0.35}>
              <div className="md:col-span-2 glass-card rounded-2xl p-8 overflow-hidden relative group">
                <div className="absolute right-0 top-0 w-1/2 h-full opacity-30 group-hover:opacity-60 transition-all duration-500">
                  <div className="w-full h-full bg-gradient-to-l from-primary/20 to-transparent flex items-center justify-end pr-8">
                    <span className="material-symbols-outlined text-primary/40 text-[160px]">hub</span>
                  </div>
                </div>
                <div className="relative z-10 w-full md:w-1/2">
                  <h4 className="text-2xl font-bold mb-4">Adaptive Learning</h4>
                  <p className="text-on-surface-variant text-sm">
                    The system learns new defect categories in as few as 10 sample images,
                    reducing commissioning time from weeks to hours.
                  </p>
                </div>
              </div>
            </RevealSection>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="bg-surface py-xl border-t border-white/5">
        <div className="container mx-auto px-6 md:px-margin-desktop">
          <div className="flex flex-col md:flex-row justify-between items-start gap-12">
            <div>
              <span className="font-display-mono text-primary tracking-widest uppercase mb-6 block">
                NIKA AI
              </span>
              <p className="text-on-surface-variant/60 text-sm max-w-xs">
                Engineered for the future of intelligent manufacturing. Precision, security,
                and velocity at the core of every frame.
              </p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-12">
              {[
                { title: 'Navigation', links: ['Platform', 'Case Studies', 'Pricing'] },
                { title: 'Connect',    links: ['LinkedIn', 'Twitter', 'GitHub'] },
                { title: 'Legal',      links: ['Privacy', 'Compliance'] },
              ].map(({ title, links }) => (
                <div key={title} className="flex flex-col gap-4">
                  <span className="font-display-mono text-[10px] text-primary-fixed-dim uppercase tracking-widest">
                    {title}
                  </span>
                  {links.map((link) => (
                    <a
                      key={link}
                      href="#"
                      className="text-sm text-on-surface-variant hover:text-primary transition-colors"
                    >
                      {link}
                    </a>
                  ))}
                </div>
              ))}
            </div>
          </div>
          <div className="mt-xl pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4">
            <span className="text-[10px] font-display-mono text-on-surface-variant/40">
              © 2024 NIKA INTELLIGENCE SYSTEMS INC.
            </span>
            <span className="text-[10px] font-display-mono text-on-surface-variant/40">
              BUILD VERSION 2.0.0-SPRINT2
            </span>
          </div>
        </div>
      </footer>

      <BottomNav />
    </div>
  )
}
