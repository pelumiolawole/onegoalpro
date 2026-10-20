'use client'

import Link from 'next/link'
import { APP_UNAVAILABLE_MESSAGE } from '@/lib/platform'

// Shown in place of purchase pages inside the Android app. No plans, prices or website.
export default function AppUnavailable() {
  return (
    <div className="min-h-screen bg-[#0A0908] flex items-center justify-center px-6">
      <div className="max-w-sm text-center">
        <p className="text-[#F5F1ED] text-base mb-6">{APP_UNAVAILABLE_MESSAGE}</p>
        <Link
          href="/dashboard"
          className="inline-block px-5 py-2.5 rounded-xl border border-white/10 text-[#C4BBB5] text-sm hover:border-white/25 transition-colors"
        >
          Back to dashboard
        </Link>
      </div>
    </div>
  )
}
