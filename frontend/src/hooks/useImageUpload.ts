/**
 * src/hooks/useImageUpload.ts
 * ───────────────────────────
 * Manages validation, preview generation, compression, and state of image uploads.
 */

import { useState, useCallback } from 'react'
import { validateImage, compressImage, fileToDataUrl } from '../lib/imageUtils'
import type { UploadedImage, UploadStatus } from '../types'

export function useImageUpload() {
  const [uploaded, setUploaded] = useState<UploadedImage | null>(null)

  const processFile = useCallback(async (file: File) => {
    const validation = validateImage(file)
    if (!validation.valid) {
      setUploaded({
        file,
        previewUrl: '',
        compressedBlob: null,
        sizeBytes: file.size,
        compressedSizeBytes: null,
        status: 'error',
        error: validation.error,
      })
      return
    }

    setUploaded({
      file,
      previewUrl: '',
      compressedBlob: null,
      sizeBytes: file.size,
      compressedSizeBytes: null,
      status: 'validating',
      error: null,
    })

    try {
      // 1. Generate preview Data URL
      const previewUrl = await fileToDataUrl(file)

      // Update state to compressing
      setUploaded((prev) =>
        prev
          ? {
              ...prev,
              previewUrl,
              status: 'compressing',
            }
          : null
      )

      // 2. Compress image client-side to speed up upload
      const compressedBlob = await compressImage(file)

      setUploaded((prev) =>
        prev
          ? {
              ...prev,
              compressedBlob,
              compressedSizeBytes: compressedBlob.size,
              status: 'ready',
            }
          : null
      )
    } catch (err: any) {
      setUploaded((prev) =>
        prev
          ? {
              ...prev,
              status: 'error',
              error: err.message || 'Error processing image.',
            }
          : null
      )
    }
  }, [])

  const removeImage = useCallback(() => {
    setUploaded(null)
  }, [])

  return {
    uploaded,
    processFile,
    removeImage,
    setUploaded,
  }
}
