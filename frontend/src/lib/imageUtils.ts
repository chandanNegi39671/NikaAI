/**
 * src/lib/imageUtils.ts
 * ──────────────────────
 * Client-side image utilities:
 *  - Format validation (PNG, JPEG, JPG, WEBP)
 *  - File size validation (max 10 MB)
 *  - Canvas-based compression to JPEG blob
 *  - Frame capture from HTMLVideoElement
 */

// ── Constants ─────────────────────────────────────────────────────────────────

export const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'] as const
export const MAX_FILE_SIZE_MB = 10
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
export const DEFAULT_COMPRESS_QUALITY = 0.82
export const DEFAULT_MAX_DIMENSION = 1280

// ── Validation ─────────────────────────────────────────────────────────────────

export function isValidImageType(file: File): boolean {
  return (ALLOWED_TYPES as readonly string[]).includes(file.type)
}

export function isValidFileSize(file: File): boolean {
  return file.size <= MAX_FILE_SIZE_BYTES
}

export interface ValidationResult {
  valid: boolean
  error: string | null
}

export function validateImage(file: File): ValidationResult {
  if (!isValidImageType(file)) {
    return {
      valid: false,
      error: `Unsupported format. Use PNG, JPEG, JPG, or WEBP.`,
    }
  }
  if (!isValidFileSize(file)) {
    return {
      valid: false,
      error: `File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is ${MAX_FILE_SIZE_MB} MB.`,
    }
  }
  return { valid: true, error: null }
}

// ── Canvas Compression ─────────────────────────────────────────────────────────

/**
 * Compress an image File or Blob to a JPEG Blob using Canvas API.
 * Resizes down if either dimension exceeds maxDimension.
 */
export async function compressImage(
  source: File | Blob,
  quality = DEFAULT_COMPRESS_QUALITY,
  maxDimension = DEFAULT_MAX_DIMENSION,
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(source)

    img.onload = () => {
      URL.revokeObjectURL(url)

      let { width, height } = img
      if (width > maxDimension || height > maxDimension) {
        if (width > height) {
          height = Math.round((height / width) * maxDimension)
          width = maxDimension
        } else {
          width = Math.round((width / height) * maxDimension)
          height = maxDimension
        }
      }

      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('Could not create canvas context'))
        return
      }

      ctx.drawImage(img, 0, 0, width, height)
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('Canvas compression produced null blob'))
            return
          }
          resolve(blob)
        },
        'image/jpeg',
        quality,
      )
    }

    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Failed to load image for compression'))
    }

    img.src = url
  })
}

// ── Frame Capture ──────────────────────────────────────────────────────────────

/**
 * Capture the current frame from a video element as a JPEG Blob.
 * Used by the real-time inference pipeline.
 */
export function captureFrame(
  video: HTMLVideoElement,
  quality = 0.75,
  maxDimension = 640,
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    if (video.readyState < 2) {
      reject(new Error('Video not ready'))
      return
    }

    let w = video.videoWidth
    let h = video.videoHeight

    if (w === 0 || h === 0) {
      reject(new Error('Video dimensions are zero'))
      return
    }

    if (w > maxDimension || h > maxDimension) {
      if (w > h) {
        h = Math.round((h / w) * maxDimension)
        w = maxDimension
      } else {
        w = Math.round((w / h) * maxDimension)
        h = maxDimension
      }
    }

    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      reject(new Error('Canvas context unavailable'))
      return
    }

    ctx.drawImage(video, 0, 0, w, h)
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          reject(new Error('Frame capture produced null blob'))
          return
        }
        resolve(blob)
      },
      'image/jpeg',
      quality,
    )
  })
}

// ── File to DataURL ────────────────────────────────────────────────────────────

export function fileToDataUrl(file: File | Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string)
    reader.onerror = () => reject(new Error('FileReader failed'))
    reader.readAsDataURL(file)
  })
}
