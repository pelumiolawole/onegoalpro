import { useEffect, useState } from 'react'

// Detects the Android app (a Trusted Web Activity) so purchase paths can be hidden there:
// Google Play's payments policy does not allow buying a digital subscription inside a Play
// app through anything except Play Billing.
//
// The flag lives in sessionStorage, not localStorage. A TWA shares Chrome's storage, so a
// localStorage flag would also hide purchase paths in ordinary Chrome tabs on the same phone.
// sessionStorage belongs to the app's own tab, and every launch from the app icon opens
// /dashboard?source=android, which sets the flag again.

const PLATFORM_KEY = 'ogp_platform'
const ANDROID_REFERRER = 'android-app://app.onegoalpro'

export function detectAndroidApp(): void {
  if (typeof window === 'undefined') return
  try {
    const url = new URL(window.location.href)
    const fromParam = url.searchParams.get('source') === 'android'
    const fromReferrer = document.referrer.startsWith(ANDROID_REFERRER)

    if (fromParam || fromReferrer) {
      sessionStorage.setItem(PLATFORM_KEY, 'android')
    }
    if (fromParam) {
      url.searchParams.delete('source')
      window.history.replaceState(null, '', url.pathname + url.search + url.hash)
    }
  } catch {
    // Storage or URL unavailable: treat as the website
  }
}

export function isAndroidApp(): boolean {
  if (typeof window === 'undefined') return false
  try {
    return sessionStorage.getItem(PLATFORM_KEY) === 'android'
  } catch {
    return false
  }
}

// null until the first client render has checked. Render purchase UI only when this is
// strictly false, so the Android app never flashes an upgrade button before hiding it.
export function useIsAndroidApp(): boolean | null {
  const [android, setAndroid] = useState<boolean | null>(null)
  useEffect(() => {
    detectAndroidApp()
    setAndroid(isAndroidApp())
  }, [])
  return android
}

export const APP_LIMIT_MESSAGE = "You've reached today's coach message limit. It resets tomorrow."
export const APP_UNAVAILABLE_MESSAGE = "This isn't available in the app."
