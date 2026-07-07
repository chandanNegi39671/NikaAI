/**
 * src/store/cameraStore.ts
 * ─────────────────────────
 * Zustand store for webcam/camera state.
 * The actual MediaStream lifecycle is managed by the useCamera hook;
 * this store holds the derived state that components read.
 */

import { create } from 'zustand'
import type { CameraState, CameraStatus, CameraDevice } from '../types'

interface CameraStore extends CameraState {
  setStatus: (status: CameraStatus) => void
  setDevices: (devices: CameraDevice[]) => void
  setActiveDevice: (deviceId: string | null) => void
  setStream: (stream: MediaStream | null) => void
  setCameraError: (error: string | null) => void
  reset: () => void
}

const initial: CameraState = {
  status: 'idle',
  devices: [],
  activeDeviceId: null,
  stream: null,
  error: null,
}

export const useCameraStore = create<CameraStore>((set) => ({
  ...initial,

  setStatus: (status) => set({ status }),
  setDevices: (devices) => set({ devices }),
  setActiveDevice: (activeDeviceId) => set({ activeDeviceId }),
  setStream: (stream) => set({ stream }),
  setCameraError: (error) => set({ error }),
  reset: () => set(initial),
}))
