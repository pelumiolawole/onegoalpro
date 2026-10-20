'use client'

import type { ReactNode } from 'react'
import { useIsAndroidApp } from '@/lib/platform'
import AppUnavailable from '@/components/AppUnavailable'

// Wraps purchase pages: renders them on the website, and a neutral message inside the
// Android app (Google Play payments policy). Renders nothing until the platform is known.
export default function WebOnly({ children }: { children: ReactNode }) {
  const isAndroidApp = useIsAndroidApp()
  if (isAndroidApp === null) return null
  if (isAndroidApp) return <AppUnavailable />
  return <>{children}</>
}
