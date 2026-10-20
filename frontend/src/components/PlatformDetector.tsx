'use client'

import { useEffect } from 'react'
import { detectAndroidApp } from '@/lib/platform'

export default function PlatformDetector() {
  useEffect(() => {
    detectAndroidApp()
  }, [])
  return null
}
