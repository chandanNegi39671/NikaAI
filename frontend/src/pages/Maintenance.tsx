/**
 * pages/Maintenance.tsx
 * ──────────────────────
 * Sprint 7: AI Manufacturing Intelligence Dashboard
 *
 * Sections:
 *   1. Fleet Overview — health score cards for all machines
 *   2. Machine Detail — animated health gauge + recommendation card
 *   3. Trend Charts   — daily/weekly/monthly pass rate + defect breakdown
 *   4. Machine Comparison — per-machine failure rate table
 *
 * Design system:
 *   - Uses existing Tailwind tokens (primary: #fbba64, surface: #17130d)
 *   - GlassCard, TopBar, BottomNav from existing components
 *   - Recharts (already in project via Dashboard.tsx)
 *   - Framer Motion for all animations
 */

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  RadialBarChart,
  RadialBar,
  PieChart,
  Pie,
} from 'recharts'

import TopBar from '../components/TopBar'
import BottomNav from '../components/BottomNav'
import GlassCard from '../components/GlassCard'
import SkeletonLoader from '../components/SkeletonLoader'

import {
  getFleetOverview,
  getDailyTrend,
  getDefectTypeTrend,
  getMachineTrend,
  getTrendSummary,
  predictMachineHealth,
} from '../lib/apiClient'

import type {
  FleetOverview,
  MaintenancePrediction,
  TrendDay,
  DefectTypeTrend,
  MachineTrend,
  TrendSummary,
  RiskLevel,
} from '../types'

// ── Helpers ─────────────────────────────────────────────────────────────────

const RISK_COLORS: Record<RiskLevel, string> = {
  low:      '#4ade80',
  moderate: '#fbba64',
  high:     '#fb923c',
  critical: '#f87171',
}

const RISK_BG: Record<RiskLevel, string> = {
  low:      'bg-green-500/10 border-green-500/30 text-green-400',
  moderate: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
  high:     'bg-orange-500/10 border-orange-500/30 text-orange-400',
  critical: 'bg-red-500/10 border-red-500/30 text-red-400',
}

const TREND_ICON: Record<string, string> = {
  improving: 'trending_up',
  stable:    'trending_flat',
  degrading: 'trending_down',
}

const TREND_COLOR: Record<string, string> = {
  improving: 'text-green-400',
  stable:    'text-amber-400',
  degrading: 'text-red-400',
}

const PRIORITY_ICON: Record<string, string> = {
  low:    'info',
  medium: 'warning',
  high:   'error',
  urgent: 'emergency',
}

function HealthGauge({ score }: { score: number }) {
  const data = [{ name: 'health', value: score, fill: score > 70 ? '#4ade80' : score > 40 ? '#fbba64' : '#f87171' }]
  return (
    <div className="relative w-40 h-40 mx-auto">
      <RadialBarChart
        cx="50%"
        cy="50%"
        innerRadius="65%"
        outerRadius="90%"
        startAngle={210}
        endAngle={-30}
        data={data}
        width={160}
        height={160}
      >
        <RadialBar dataKey="value" cornerRadius={8} background={{ fill: '#2f2923' }} />
      </RadialBarChart>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold text-on-surface">{score.toFixed(0)}</span>
        <span className="text-xs text-on-surface-variant uppercase tracking-widest">Health</span>
      </div>
    </div>
  )
}

function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase border ${RISK_BG[level]}`}>
      {level}
    </span>
  )
}

const tooltipStyle = {
  backgroundColor: '#241f19',
  border: '1px solid rgba(251,186,100,0.2)',
  borderRadius: '8px',
  color: '#ece0d6',
  fontSize: '12px',
}

const DEFECT_PALETTE = [
  '#fbba64', '#ff6a00', '#f87171', '#4ade80', '#60a5fa', '#c084fc', '#34d399',
]


// ── Sub-Components ───────────────────────────────────────────────────────────

function SummaryKpi({
  icon, label, value, sub, color = 'text-primary-fixed-dim',
}: {
  icon: string; label: string; value: string; sub?: string; color?: string
}) {
  return (
    <GlassCard className="p-5 flex items-center gap-4">
      <div className="w-12 h-12 rounded-xl bg-primary-container/10 flex items-center justify-center shrink-0">
        <span className={`material-symbols-outlined filled text-2xl ${color}`}>{icon}</span>
      </div>
      <div>
        <p className="text-xs text-on-surface-variant uppercase tracking-wider">{label}</p>
        <p className={`text-2xl font-bold ${color}`}>{value}</p>
        {sub && <p className="text-xs text-on-surface-variant mt-0.5">{sub}</p>}
      </div>
    </GlassCard>
  )
}

function MachineCard({
  prediction,
  onAnalyze,
  selected,
}: {
  prediction: MaintenancePrediction
  onAnalyze: (id: string) => void
  selected: boolean
}) {
  return (
    <motion.div
      layout
      whileHover={{ scale: 1.01 }}
      onClick={() => onAnalyze(prediction.machine_id!)}
      className={`cursor-pointer rounded-2xl border p-5 transition-all duration-200 ${
        selected
          ? 'border-primary bg-primary/5 shadow-[0_0_20px_rgba(251,186,100,0.15)]'
          : 'border-outline-variant/40 bg-surface-container-low hover:border-primary/40'
      }`}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-semibold text-on-surface">{prediction.machine_name ?? 'Unknown'}</h3>
          <p className="text-xs text-on-surface-variant mt-0.5">
            {prediction.machine_location ?? '—'}
          </p>
        </div>
        <RiskBadge level={prediction.risk_level} />
      </div>

      <HealthGauge score={prediction.health_score} />

      <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
        <div className="bg-surface-container p-3 rounded-xl">
          <p className="text-on-surface-variant">RUL</p>
          <p className="text-on-surface font-semibold mt-1">{prediction.rul_days}d</p>
        </div>
        <div className="bg-surface-container p-3 rounded-xl">
          <p className="text-on-surface-variant">Defect Rate</p>
          <p className="text-on-surface font-semibold mt-1">
            {(prediction.defect_rate * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 mt-4">
        <span className={`material-symbols-outlined text-base ${TREND_COLOR[prediction.trend]}`}>
          {TREND_ICON[prediction.trend]}
        </span>
        <span className={`text-xs capitalize ${TREND_COLOR[prediction.trend]}`}>
          {prediction.trend}
        </span>
        <span className="ml-auto text-xs text-on-surface-variant">
          {prediction.computed_at
            ? new Date(prediction.computed_at).toLocaleDateString()
            : 'Not analyzed'}
        </span>
      </div>
    </motion.div>
  )
}

function RecommendationPanel({ prediction }: { prediction: MaintenancePrediction }) {
  return (
    <GlassCard className="p-6">
      <div className="flex items-center gap-3 mb-5">
        <span
          className={`material-symbols-outlined filled text-2xl ${
            TREND_COLOR[prediction.trend]
          }`}
        >
          {PRIORITY_ICON[prediction.priority] ?? 'info'}
        </span>
        <div>
          <h3 className="font-semibold text-on-surface">
            {prediction.machine_name ?? 'Machine'}
          </h3>
          <p className="text-xs text-on-surface-variant capitalize">{prediction.priority} priority</p>
        </div>
        <RiskBadge level={prediction.risk_level} />
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          { label: 'Health Score', value: `${prediction.health_score.toFixed(0)}/100` },
          { label: 'RUL',          value: `${prediction.rul_days} days` },
          { label: 'Defect Rate',  value: `${(prediction.defect_rate * 100).toFixed(1)}%` },
        ].map(({ label, value }) => (
          <div key={label} className="bg-surface-container p-3 rounded-xl text-center">
            <p className="text-xs text-on-surface-variant">{label}</p>
            <p className="text-base font-bold text-on-surface mt-1">{value}</p>
          </div>
        ))}
      </div>

      <div className="bg-surface-container-high rounded-xl p-4">
        <p className="text-xs text-on-surface-variant uppercase tracking-wider mb-2">
          AI Recommendation
        </p>
        <p className="text-sm text-on-surface leading-relaxed">
          {prediction.recommendation ?? 'No recommendation available.'}
        </p>
        <div className="flex items-center gap-2 mt-3">
          <span className="px-2 py-0.5 rounded text-xs font-mono bg-primary/10 text-primary-fixed-dim border border-primary/20">
            {prediction.recommendation_code ?? '—'}
          </span>
        </div>
      </div>

      {prediction.total_inspections > 0 && (
        <div className="grid grid-cols-2 gap-4 mt-4 text-xs">
          <div>
            <span className="text-on-surface-variant">Total Inspections</span>
            <span className="ml-2 text-on-surface font-semibold">{prediction.total_inspections}</span>
          </div>
          <div>
            <span className="text-on-surface-variant">Failed</span>
            <span className="ml-2 text-red-400 font-semibold">{prediction.failed_inspections}</span>
          </div>
        </div>
      )}
    </GlassCard>
  )
}


// ── Main Page ────────────────────────────────────────────────────────────────

export default function Maintenance() {
  // State
  const [fleet, setFleet] = useState<FleetOverview | null>(null)
  const [selectedMachineId, setSelectedMachineId] = useState<string | null>(null)
  const [selectedPrediction, setSelectedPrediction] = useState<MaintenancePrediction | null>(null)
  const [dailyTrend, setDailyTrend] = useState<TrendDay[]>([])
  const [defectTrend, setDefectTrend] = useState<DefectTypeTrend[]>([])
  const [machineTrend, setMachineTrend] = useState<MachineTrend[]>([])
  const [summary, setSummary] = useState<TrendSummary | null>(null)
  const [trendPeriod, setTrendPeriod] = useState<'7' | '30' | '90'>('30')
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load fleet + trend data
  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const days = parseInt(trendPeriod)
      const [fleetData, daily, defects, machines, sum] = await Promise.all([
        getFleetOverview(),
        getDailyTrend(days),
        getDefectTypeTrend(days),
        getMachineTrend(days),
        getTrendSummary(days),
      ])
      setFleet(fleetData)
      setDailyTrend(daily)
      setDefectTrend(defects)
      setMachineTrend(machines)
      setSummary(sum)

      // Auto-select worst machine
      if (fleetData.fleet.length > 0 && !selectedMachineId) {
        const worst = fleetData.fleet.reduce((a, b) =>
          a.health_score < b.health_score ? a : b
        )
        if (worst.machine_id) {
          setSelectedMachineId(worst.machine_id)
          setSelectedPrediction(worst as MaintenancePrediction)
        }
      }
    } catch (e: any) {
      setError(e?.message ?? 'Failed to load maintenance data.')
    } finally {
      setLoading(false)
    }
  }, [trendPeriod])

  useEffect(() => { fetchData() }, [fetchData])

  const handleAnalyze = useCallback(async (machineId: string) => {
    setSelectedMachineId(machineId)
    setAnalyzing(true)
    try {
      const pred = await predictMachineHealth(machineId)
      setSelectedPrediction(pred)
      // Refresh fleet after new prediction
      const updated = await getFleetOverview()
      setFleet(updated)
    } catch (e: any) {
      setError(e?.message ?? 'Analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }, [])

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.07 } },
  }
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  }

  return (
    <div className="min-h-screen bg-background text-on-surface">
      <TopBar />
      <BottomNav />

      <main className="pt-20 pb-28 px-4 md:px-margin-desktop max-w-[1600px] mx-auto">

        {/* ── Page Header ────────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center">
              <span className="material-symbols-outlined filled text-primary text-lg">build</span>
            </div>
            <h1 className="text-2xl font-bold gradient-text">Maintenance Intelligence</h1>
          </div>
          <p className="text-sm text-on-surface-variant">
            AI-powered predictive maintenance — health scores, risk assessment, and recommendations
          </p>
        </motion.div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-center gap-2">
            <span className="material-symbols-outlined text-base">error</span>
            {error}
            <button onClick={fetchData} className="ml-auto underline text-xs">Retry</button>
          </div>
        )}

        {/* ── Summary KPIs ────────────────────────────────────────────── */}
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {Array.from({ length: 4 }).map((_, i) => (
              <SkeletonLoader key={i} className="h-24 rounded-2xl" />
            ))}
          </div>
        ) : summary && (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
          >
            <motion.div variants={itemVariants}>
              <SummaryKpi
                icon="verified"
                label="Pass Rate"
                value={`${summary.pass_rate.toFixed(1)}%`}
                sub={`${summary.total_inspections.toLocaleString()} inspections`}
                color={summary.pass_rate > 95 ? 'text-green-400' : summary.pass_rate > 85 ? 'text-amber-400' : 'text-red-400'}
              />
            </motion.div>
            <motion.div variants={itemVariants}>
              <SummaryKpi
                icon="warning"
                label="Machines at Risk"
                value={`${summary.machines_at_risk} / ${summary.total_machines}`}
                sub="Defect rate > 25%"
                color={summary.machines_at_risk === 0 ? 'text-green-400' : 'text-red-400'}
              />
            </motion.div>
            <motion.div variants={itemVariants}>
              <SummaryKpi
                icon="troubleshoot"
                label="Top Defect"
                value={summary.top_defect_name}
                sub={`${summary.top_defect_count} occurrences`}
                color="text-amber-400"
              />
            </motion.div>
            <motion.div variants={itemVariants}>
              <SummaryKpi
                icon="speed"
                label="Avg Confidence"
                value={`${(summary.avg_confidence * 100).toFixed(1)}%`}
                sub={`${summary.avg_latency_ms.toFixed(0)}ms avg latency`}
              />
            </motion.div>
          </motion.div>
        )}

        {/* ── Trend Period Toggle ───────────────────────────────────────── */}
        <div className="flex items-center gap-2 mb-6">
          <span className="text-xs text-on-surface-variant uppercase tracking-wider mr-2">Period</span>
          {(['7', '30', '90'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setTrendPeriod(p)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                trendPeriod === p
                  ? 'bg-primary text-on-primary'
                  : 'bg-surface-container text-on-surface-variant hover:text-primary'
              }`}
            >
              {p === '7' ? '7 Days' : p === '30' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>

        {/* ── Main Grid ────────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Left: Fleet cards */}
          <div className="lg:col-span-1 space-y-4">
            <h2 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider flex items-center gap-2">
              <span className="material-symbols-outlined text-base text-primary">factory</span>
              Fleet Health
              {fleet && (
                <span className="ml-auto text-xs font-normal">
                  {fleet.total_machines} machines
                </span>
              )}
            </h2>

            {loading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <SkeletonLoader key={i} className="h-64 rounded-2xl" />
              ))
            ) : (
              <AnimatePresence>
                {(fleet?.fleet ?? []).map((pred, i) => (
                  <motion.div
                    key={pred.machine_id ?? i}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <MachineCard
                      prediction={pred as MaintenancePrediction}
                      onAnalyze={handleAnalyze}
                      selected={selectedMachineId === pred.machine_id}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            )}
          </div>

          {/* Right: Charts + Recommendation */}
          <div className="lg:col-span-2 space-y-6">

            {/* Recommendation Panel */}
            <AnimatePresence mode="wait">
              {analyzing ? (
                <motion.div
                  key="analyzing"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="h-48 rounded-2xl bg-surface-container flex items-center justify-center gap-3"
                >
                  <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm text-on-surface-variant">Running analysis…</span>
                </motion.div>
              ) : selectedPrediction ? (
                <motion.div
                  key={selectedPrediction.machine_id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  <RecommendationPanel prediction={selectedPrediction} />
                </motion.div>
              ) : null}
            </AnimatePresence>

            {/* Daily Trend Chart */}
            <GlassCard className="p-6">
              <h3 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-base text-primary">area_chart</span>
                Daily Pass Rate Trend
              </h3>
              {loading ? (
                <SkeletonLoader className="h-52" />
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={dailyTrend} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                    <defs>
                      <linearGradient id="passGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#fbba64" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#fbba64" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="failGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f87171" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#f87171" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#3a342d" />
                    <XAxis dataKey="date" tick={{ fill: '#9d8e7e', fontSize: 10 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: '#9d8e7e', fontSize: 10 }} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Area
                      type="monotone"
                      dataKey="pass_rate"
                      name="Pass Rate %"
                      stroke="#fbba64"
                      strokeWidth={2}
                      fill="url(#passGrad)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </GlassCard>

            {/* Bottom row: Defect breakdown + Machine comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

              {/* Defect Type Breakdown */}
              <GlassCard className="p-6">
                <h3 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider mb-4 flex items-center gap-2">
                  <span className="material-symbols-outlined text-base text-primary">donut_large</span>
                  Defect Distribution
                </h3>
                {loading ? (
                  <SkeletonLoader className="h-44" />
                ) : defectTrend.length === 0 ? (
                  <div className="h-44 flex items-center justify-center text-xs text-on-surface-variant">
                    No defect data for this period
                  </div>
                ) : (
                  <>
                    <ResponsiveContainer width="100%" height={140}>
                      <PieChart>
                        <Pie
                          data={defectTrend}
                          dataKey="count"
                          nameKey="defect_name"
                          cx="50%"
                          cy="50%"
                          innerRadius={40}
                          outerRadius={65}
                          paddingAngle={3}
                        >
                          {defectTrend.map((_, idx) => (
                            <Cell key={idx} fill={DEFECT_PALETTE[idx % DEFECT_PALETTE.length]} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={tooltipStyle} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="mt-2 space-y-1">
                      {defectTrend.slice(0, 4).map((d, idx) => (
                        <div key={d.defect_class} className="flex items-center gap-2 text-xs">
                          <div
                            className="w-2.5 h-2.5 rounded-full shrink-0"
                            style={{ backgroundColor: DEFECT_PALETTE[idx % DEFECT_PALETTE.length] }}
                          />
                          <span className="text-on-surface-variant truncate flex-1">{d.defect_name}</span>
                          <span className="text-on-surface font-semibold">{d.percentage.toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </GlassCard>

              {/* Machine Failure Rate Comparison */}
              <GlassCard className="p-6">
                <h3 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider mb-4 flex items-center gap-2">
                  <span className="material-symbols-outlined text-base text-primary">bar_chart</span>
                  Machine Failure Rate
                </h3>
                {loading ? (
                  <SkeletonLoader className="h-44" />
                ) : machineTrend.length === 0 ? (
                  <div className="h-44 flex items-center justify-center text-xs text-on-surface-variant">
                    No machine data available
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart
                      data={machineTrend.slice(0, 6)}
                      margin={{ top: 4, right: 4, bottom: 20, left: -20 }}
                      layout="vertical"
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#3a342d" horizontal={false} />
                      <XAxis type="number" domain={[0, 100]} tick={{ fill: '#9d8e7e', fontSize: 9 }} />
                      <YAxis
                        type="category"
                        dataKey="machine_name"
                        tick={{ fill: '#9d8e7e', fontSize: 9 }}
                        width={80}
                      />
                      <Tooltip
                        contentStyle={tooltipStyle}
                        formatter={(v: number) => [`${v.toFixed(1)}%`, 'Defect Rate']}
                      />
                      <Bar dataKey="defect_rate_pct" radius={[0, 4, 4, 0]}>
                        {machineTrend.map((m, idx) => (
                          <Cell
                            key={idx}
                            fill={
                              m.status === 'critical' ? '#f87171'
                              : m.status === 'warning' ? '#fbba64'
                              : '#4ade80'
                            }
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </GlassCard>
            </div>

            {/* Fleet Risk Summary Bar */}
            {!loading && fleet && (
              <GlassCard className="p-5">
                <h3 className="text-sm font-semibold text-on-surface-variant uppercase tracking-wider mb-4">
                  Fleet Risk Distribution
                </h3>
                <div className="flex gap-3 flex-wrap">
                  {[
                    { label: 'Critical', count: fleet.machines_critical, color: 'bg-red-500' },
                    { label: 'High',     count: fleet.machines_high,     color: 'bg-orange-500' },
                    { label: 'Moderate', count: fleet.machines_moderate,  color: 'bg-amber-500' },
                    { label: 'Healthy',  count: fleet.machines_healthy,   color: 'bg-green-500' },
                  ].map(({ label, count, color }) => (
                    <div key={label} className="flex items-center gap-2 bg-surface-container px-4 py-2 rounded-xl">
                      <div className={`w-3 h-3 rounded-full ${color}`} />
                      <span className="text-xs text-on-surface-variant">{label}</span>
                      <span className="text-sm font-bold text-on-surface">{count}</span>
                    </div>
                  ))}
                  <button
                    onClick={fetchData}
                    className="ml-auto flex items-center gap-1.5 px-4 py-2 rounded-xl bg-primary/10 border border-primary/30 text-primary-fixed-dim text-xs font-semibold hover:bg-primary/20 transition-colors"
                  >
                    <span className="material-symbols-outlined text-sm">refresh</span>
                    Refresh
                  </button>
                </div>
              </GlassCard>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
