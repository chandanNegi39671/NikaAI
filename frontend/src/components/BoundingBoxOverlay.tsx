/**
 * src/components/BoundingBoxOverlay.tsx
 * ──────────────────────────────────────
 * Overlays bounding boxes on an inspected component image or live video feed.
 * Dynamically maps coordinates from raw YOLO image coordinates to current render dimensions.
 */

import { motion } from 'framer-motion'
import type { Detection } from '../types'

interface BoundingBoxOverlayProps {
  detections: Detection[]
  sourceWidth: number // Original image/video width
  sourceHeight: number // Original image/video height
  containerWidth: number // Rendered container width
  containerHeight: number // Rendered container height
}

// Defect classification color palette
const CLASS_COLORS: Record<string, { border: string; bg: string; text: string }> = {
  surface_crack: {
    border: 'border-red-500',
    bg: 'bg-red-500/20',
    text: 'bg-red-600 text-white',
  },
  crack: {
    border: 'border-red-500',
    bg: 'bg-red-500/20',
    text: 'bg-red-600 text-white',
  },
  scratch: {
    border: 'border-amber-500',
    bg: 'bg-amber-500/20',
    text: 'bg-amber-600 text-black font-semibold',
  },
  pit: {
    border: 'border-blue-500',
    bg: 'bg-blue-500/20',
    text: 'bg-blue-600 text-white',
  },
  dent: {
    border: 'border-purple-500',
    bg: 'bg-purple-500/20',
    text: 'bg-purple-600 text-white',
  },
  defect: {
    border: 'border-rose-500',
    bg: 'bg-rose-500/20',
    text: 'bg-rose-600 text-white',
  },
}

const DEFAULT_COLOR = {
  border: 'border-primary',
  bg: 'bg-primary/20',
  text: 'bg-primary text-on-primary-container',
}

export default function BoundingBoxOverlay({
  detections,
  sourceWidth,
  sourceHeight,
  containerWidth,
  containerHeight,
}: BoundingBoxOverlayProps) {
  if (sourceWidth === 0 || sourceHeight === 0 || containerWidth === 0 || containerHeight === 0) {
    return null
  }

  // Determine aspect ratio scaling to replicate 'object-contain' fit
  const sourceRatio = sourceWidth / sourceHeight
  const containerRatio = containerWidth / containerHeight

  let renderWidth = containerWidth
  let renderHeight = containerHeight
  let xOffset = 0
  let yOffset = 0

  if (sourceRatio > containerRatio) {
    // Width constrained (letterbox on top/bottom)
    renderHeight = containerWidth / sourceRatio
    yOffset = (containerHeight - renderHeight) / 2
  } else {
    // Height constrained (pillarbox on sides)
    renderWidth = containerHeight * sourceRatio
    xOffset = (containerWidth - renderWidth) / 2
  }

  const scaleX = renderWidth / sourceWidth
  const scaleY = renderHeight / sourceHeight

  return (
    <div
      className="absolute pointer-events-none"
      style={{
        left: xOffset,
        top: yOffset,
        width: renderWidth,
        height: renderHeight,
      }}
    >
      {detections.map((det, index) => {
        const { x1, y1, x2, y2 } = det.bounding_box
        const left = x1 * scaleX
        const top = y1 * scaleY
        const width = (x2 - x1) * scaleX
        const height = (y2 - y1) * scaleY

        const styleConfig = CLASS_COLORS[det.class.toLowerCase()] || DEFAULT_COLOR

        return (
          <motion.div
            key={`${det.class}-${index}`}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{
              type: 'spring',
              damping: 15,
              stiffness: 150,
              delay: index * 0.05,
            }}
            className={`absolute border-2 rounded-lg flex flex-col justify-start items-start ${styleConfig.border} ${styleConfig.bg}`}
            style={{
              left,
              top,
              width,
              height,
              boxShadow: '0 0 12px rgba(0,0,0,0.4)',
            }}
          >
            {/* Label */}
            <div
              className={`px-2 py-0.5 font-display-mono text-[9px] uppercase tracking-wider rounded-br rounded-tl-sm ${styleConfig.text}`}
            >
              {det.class.replace(/_/g, ' ')} {(det.confidence * 100).toFixed(0)}%
            </div>

            {/* Premium Corner Indicators */}
            <div className={`w-3 h-3 border-b-2 border-l-2 absolute bottom-0 left-0 ${styleConfig.border}`} />
            <div className={`w-3 h-3 border-b-2 border-r-2 absolute bottom-0 right-0 ${styleConfig.border}`} />
            <div className={`w-3 h-3 border-t-2 border-l-2 absolute top-0 left-0 ${styleConfig.border}`} />
            <div className={`w-3 h-3 border-t-2 border-r-2 absolute top-0 right-0 ${styleConfig.border}`} />
          </motion.div>
        )
      })}
    </div>
  )
}
