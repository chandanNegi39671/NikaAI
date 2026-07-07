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
import SkeletonLoader from './components/SkeletonLoader'

// Code splitting / Lazy loading components
const Home = lazy(() => import('./pages/Home'))
const LiveInspection = lazy(() => import('./pages/LiveInspection'))
const InspectionResult = lazy(() => import('./pages/InspectionResult'))
const FactoryMemory = lazy(() => import('./pages/FactoryMemory'))
const Dashboard = lazy(() => import('./pages/Dashboard'))

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
              
              {/* Fallback routing */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AnimatePresence>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
