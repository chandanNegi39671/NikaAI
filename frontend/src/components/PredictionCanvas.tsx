/**
 * src/components/PredictionCanvas.tsx
 * ────────────────────────────────────
 * Holds image/video asset and measures container size to apply BoundingBoxOverlay.
 */

import { useRef, useState, useEffect } from 'react'
import BoundingBoxOverlay from './BoundingBoxOverlay'
import type { Detection } from '../types'

interface PredictionCanvasProps {
  src: string | null
  videoRef?: React.RefObject<any>
  detections: Detection[]
  sourceWidth: number
  sourceHeight: number
  className?: string
  alt?: string
}

export default function PredictionCanvas({
  src,
  videoRef,
  detections,
  sourceWidth,
  sourceHeight,
  className = '',
  alt = 'Inspection Target',
}: PredictionCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const updateSize = () => {
      setDimensions({
        width: el.clientWidth,
        height: el.clientHeight,
      })
    }

    // Measure initially
    updateSize()

    // Listen to resize
    const observer = new ResizeObserver(updateSize)
    observer.observe(el)

    return () => {
      observer.disconnect()
    }
  }, [])

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-full overflow-hidden flex items-center justify-center bg-black/40 ${className}`}
    >
      {/* Target Asset */}
      {videoRef ? (
        <video
          ref={videoRef}
          playsInline
          muted
          autoPlay
          className="w-full h-full object-contain"
        />
      ) : src ? (
        <img
          src={src}
          alt={alt}
          className="w-full h-full object-contain"
        />
      ) : (
        <div className="text-on-surface-variant/40 flex flex-col items-center justify-center p-8 text-center">
          <span className="material-symbols-outlined text-[80px] mb-2 opacity-25">
            photo_camera_back
          </span>
          <p className="font-display-mono text-xs uppercase tracking-wider">
            No source input loaded
          </p>
        </div>
      )}

      {/* Overlay Detections */}
      {detections.length > 0 && (
        <BoundingBoxOverlay
          detections={detections}
          sourceWidth={sourceWidth || 640}
          sourceHeight={sourceHeight || 480}
          containerWidth={dimensions.width}
          containerHeight={dimensions.height}
        />
      )}
    </div>
  )
}
