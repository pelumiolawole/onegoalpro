'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getConsent, setConsent, OPEN_COOKIE_SETTINGS_EVENT } from '@/lib/posthog'

export default function CookieBanner() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (getConsent() === null) setVisible(true)

    const open = () => setVisible(true)
    window.addEventListener(OPEN_COOKIE_SETTINGS_EVENT, open)
    return () => window.removeEventListener(OPEN_COOKIE_SETTINGS_EVENT, open)
  }, [])

  function choose(consent: 'accepted' | 'declined') {
    setConsent(consent)
    setVisible(false)
  }

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 16 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="fixed bottom-20 md:bottom-6 left-4 right-4 md:left-auto md:right-6 md:max-w-sm z-50"
          role="dialog"
          aria-label="Analytics preferences"
        >
          <div
            className="rounded-2xl border border-white/8 bg-[#1A1714] px-5 py-4"
            style={{ boxShadow: '0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)' }}
          >
            <p className="text-[#E8E2DC] text-sm font-medium mb-1">Your privacy</p>
            <p className="text-[#5C524A] text-xs leading-relaxed mb-4">
              We use your browser&apos;s storage to keep you signed in. With your permission, we also use
              analytics (PostHog) to understand how the app is used. You can change your mind at any time.{' '}
              <a
                href="/privacy"
                className="text-[#7A6E65] underline underline-offset-2 hover:text-[#A09690] transition-colors"
              >
                Privacy policy
              </a>
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => choose('accepted')}
                className="flex-1 h-9 rounded-xl bg-[#F59E0B] text-[#0A0908] text-sm font-medium hover:bg-[#FCD34D] transition-colors"
              >
                Accept analytics
              </button>
              <button
                onClick={() => choose('declined')}
                className="flex-1 h-9 rounded-xl border border-white/8 text-[#7A6E65] text-sm hover:text-[#A09690] hover:border-white/15 transition-all"
              >
                Decline
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
