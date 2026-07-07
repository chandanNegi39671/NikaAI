/**
 * src/lib/reportUtils.ts
 * ───────────────────────
 * Utilities for exporting inspection reports:
 *  - JSON download
 *  - PDF placeholder
 *  - Formatted report generation
 */

import type { PredictResponse, HistoryEntry } from '../types'

// ── JSON Report ────────────────────────────────────────────────────────────────

export interface InspectionReport {
  reportVersion: string
  generatedAt: string
  sessionId: string
  result: PredictResponse
  summary: {
    overallStatus: 'PASS' | 'FAIL'
    detectionCount: number
    topDefect: string | null
    topConfidence: number | null
    inferenceTimeMs: number
  }
  detections: Array<{
    rank: number
    class: string
    confidence: number
    confidencePct: string
    boundingBox: {
      x1: number
      y1: number
      x2: number
      y2: number
      widthPx: number
      heightPx: number
    }
  }>
}

export function buildReport(
  result: PredictResponse,
  sessionId: string,
): InspectionReport {
  const top = result.detections[0] ?? null

  return {
    reportVersion: '3.0.0',
    generatedAt: new Date().toISOString(),
    sessionId,
    result,
    summary: {
      overallStatus: result.detections.length > 0 ? 'FAIL' : 'PASS',
      detectionCount: result.detections.length,
      topDefect: top?.class ?? null,
      topConfidence: top ? Math.round(top.confidence * 1000) / 10 : null,
      inferenceTimeMs: result.inference_time_ms,
    },
    detections: result.detections.map((d, i) => ({
      rank: i + 1,
      class: d.class,
      confidence: d.confidence,
      confidencePct: `${(d.confidence * 100).toFixed(1)}%`,
      boundingBox: {
        x1: Math.round(d.bounding_box.x1),
        y1: Math.round(d.bounding_box.y1),
        x2: Math.round(d.bounding_box.x2),
        y2: Math.round(d.bounding_box.y2),
        widthPx: Math.round(d.bounding_box.x2 - d.bounding_box.x1),
        heightPx: Math.round(d.bounding_box.y2 - d.bounding_box.y1),
      },
    })),
  }
}

/**
 * Trigger a JSON file download in the browser.
 */
export function downloadJSON(data: unknown, filename: string): void {
  const json = JSON.stringify(data, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 5000)
}

/**
 * Download the inspection report as JSON.
 */
export function downloadInspectionReport(
  result: PredictResponse,
  sessionId: string,
): void {
  const report = buildReport(result, sessionId)
  const filename = `nika-inspection-${sessionId}-${Date.now()}.json`
  downloadJSON(report, filename)
}

/**
 * Export the entire history as JSON.
 */
export function downloadHistoryExport(history: HistoryEntry[]): void {
  const data = {
    exportVersion: '3.0.0',
    exportedAt: new Date().toISOString(),
    totalEntries: history.length,
    entries: history,
  }
  downloadJSON(data, `nika-history-export-${Date.now()}.json`)
}

/**
 * PDF export placeholder — logs intent and shows user message.
 * Will be wired to a PDF generation library in Sprint 4.
 */
export function exportToPDF(_result: PredictResponse, _sessionId: string): void {
  console.info('[NikaAI] PDF export is planned for Sprint 4 (jsPDF integration).')
  // TODO: Sprint 4 — integrate jsPDF + html2canvas
}
