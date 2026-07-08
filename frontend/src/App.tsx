/**
 * src/App.tsx
 * ────────────
 * Root application component with code splitting, error boundaries,
 * network status banners, and global notification stacks.
 */

import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'

// Global Components
import ErrorBoundary from './components/ErrorBoundary'
import OfflineBanner from './components/OfflineBanner'
import NotificationStack from './components/NotificationStack'

// Code splitting / Lazy loading components
const Home = lazy(() => import('./pages/Home'))
const LiveInspection = lazy(() => import('./pages/LiveInspection'))
const InspectionResult = lazy(() => import('./pages/InspectionResult'))
const FactoryMemory = lazy(() => import('./pages/FactoryMemory'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Maintenance = lazy(() => import('./pages/Maintenance'))

// Sprint 8 Pages
const Copilot = lazy(() => import('./pages/Copilot'))
const ModelRegistry = lazy(() => import('./pages/ModelRegistry'))
const InferenceHistory = lazy(() => import('./pages/InferenceHistory'))
const AuditLogs = lazy(() => import('./pages/AuditLogs'))
const VisualizationViewer = lazy(() => import('./pages/VisualizationViewer'))

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        {/* Network and Toast Status Overlays */}
        <OfflineBanner />
        <NotificationStack />

        <Suspense
          fallback={
            <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 space-y-4">
              <div className="w-12 h-12 border-4 border-dashed border-primary rounded-full animate-spin" />
              <p className="text-on-surface-variant font-display-mono text-xs uppercase tracking-wider">
                Loading Application Layer...
              </p>
            </div>
          }
        >
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/inspect" element={<LiveInspection />} />
              <Route path="/inspect/result" element={<InspectionResult />} />
              <Route path="/history" element={<FactoryMemory />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/maintenance" element={<Maintenance />} />
              
              {/* Sprint 8 Routes */}
              <Route path="/copilot" element={<Copilot />} />
              <Route path="/registry" element={<ModelRegistry />} />
              <Route path="/inference" element={<InferenceHistory />} />
              <Route path="/audit" element={<AuditLogs />} />
              <Route path="/visualization/:id" element={<VisualizationViewer />} />
              
              {/* Fallback routing */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AnimatePresence>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
