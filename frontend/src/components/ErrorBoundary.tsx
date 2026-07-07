/**
 * src/components/ErrorBoundary.tsx
 * ────────────────────────────────
 * Catch-all React error boundary displaying a premium recovery layout.
 */

import React, { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error in component tree:', error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.href = '/'
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 text-center">
          <div className="glass-card max-w-md w-full p-8 rounded-2xl border-t border-error/45 shadow-glass">
            <span className="material-symbols-outlined text-error text-6xl mb-4 animate-bounce">
              gavel
            </span>
            <h1 className="font-headline-lg text-white mb-2 leading-tight">
              Interface Pipeline Failure
            </h1>
            <p className="text-on-surface-variant/80 text-sm mb-6 leading-relaxed">
              An unexpected exception was thrown inside the visual engine. Error logs have been captured.
            </p>
            <div className="bg-black/30 p-3 rounded-lg border border-white/5 font-display-mono text-[10px] text-left text-error overflow-auto max-h-36 mb-6">
              {this.state.error?.stack || this.state.error?.toString()}
            </div>
            <button
              onClick={this.handleReset}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-primary to-secondary text-on-primary font-label-sm uppercase tracking-wider shadow-primary-glow hover:shadow-primary-glow-lg transition-all font-bold active:scale-[0.98]"
            >
              Reinitialize System
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
