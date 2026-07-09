import { lazy, Suspense, useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import ErrorBoundary from './components/ErrorBoundary'
import OfflineBanner from './components/OfflineBanner'
import NotificationStack from './components/NotificationStack'
import LoginModal from './components/LoginModal'

const Home = lazy(() => import('./pages/Home'))
const LiveInspection = lazy(() => import('./pages/LiveInspection'))
const InspectionResult = lazy(() => import('./pages/InspectionResult'))
const FactoryMemory = lazy(() => import('./pages/FactoryMemory'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Maintenance = lazy(() => import('./pages/Maintenance'))
const Copilot = lazy(() => import('./pages/Copilot'))
const ModelRegistry = lazy(() => import('./pages/ModelRegistry'))
const InferenceHistory = lazy(() => import('./pages/InferenceHistory'))
const AuditLogs = lazy(() => import('./pages/AuditLogs'))
const VisualizationViewer = lazy(() => import('./pages/VisualizationViewer'))

export default function App() {
  const [showLogin, setShowLogin] = useState(false)
  useEffect(() => { if (!localStorage.getItem('nika_token')) setShowLogin(true) }, [])

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <OfflineBanner />
        <NotificationStack />
        <LoginModal isOpen={showLogin} onClose={() => setShowLogin(false)} />
        <Suspense fallback={
          <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 space-y-4">
            <div className="w-12 h-12 border-4 border-dashed border-primary rounded-full animate-spin" />
            <p className="text-on-surface-variant font-display-mono text-xs uppercase tracking-wider">Loading Application Layer...</p>
          </div>
        }>
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/inspect" element={<LiveInspection />} />
              <Route path="/inspect/result" element={<InspectionResult />} />
              <Route path="/history" element={<FactoryMemory />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/maintenance" element={<Maintenance />} />
              <Route path="/copilot" element={<Copilot />} />
              <Route path="/registry" element={<ModelRegistry />} />
              <Route path="/inference" element={<InferenceHistory />} />
              <Route path="/audit" element={<AuditLogs />} />
              <Route path="/visualization/:id" element={<VisualizationViewer />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AnimatePresence>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
