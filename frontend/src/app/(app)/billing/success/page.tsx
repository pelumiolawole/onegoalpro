'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { api } from '@/lib/api'
import { trackEvent } from '@/lib/posthog'

function SuccessLoading() {
  return (
    <div className="min-h-screen bg-[#FFFFFF] flex items-center justify-center">
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-8 h-8 border-2 border-[#009e97] border-t-transparent rounded-full mx-auto mb-4"
        />
        <p className="text-[#C8C7C5] text-sm">Confirming your subscription...</p>
      </div>
    </div>
  )
}

function SuccessContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const sessionId = searchParams.get('session_id')
  const [subscription, setSubscription] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!sessionId) {
      setError('No session ID found')
      setLoading(false)
      return
    }

    const verifySession = async () => {
      try {
        const response = await api.billing.verifySession({ session_id: sessionId })
        setSubscription(response)
        trackEvent('subscription_activated', { tier: response.plan })
      } catch (err) {
        setError('Could not verify subscription')
      } finally {
        setLoading(false)
      }
    }

    verifySession()
  }, [sessionId])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FFFFFF] flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-8 h-8 border-2 border-[#009e97] border-t-transparent rounded-full mx-auto mb-4"
          />
          <p className="text-[#C8C7C5] text-sm">Confirming your subscription...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#FFFFFF] flex items-center justify-center p-6">
        <div className="max-w-md w-full text-center">
          <div className="w-14 h-14 rounded-full border border-red-500/30 bg-red-500/10 flex items-center justify-center mx-auto mb-6">
            <span className="text-red-400 text-xl">✕</span>
          </div>
          <h1 className="text-xl font-semibold text-[#1A1A1A] mb-3">Something went wrong</h1>
          <p className="text-[#C8C7C5] text-sm mb-8">{error}</p>
          <Link
            href="/settings"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#009e97] text-[#FFFFFF] font-semibold text-sm hover:bg-[#00827c] transition-all"
          >
            Go to settings →
          </Link>
        </div>
      </div>
    )
  }

  const isForge = subscription?.plan === 'forge'
  const planName = isForge ? 'The Forge' : 'The Identity'
  const planDesc = isForge
    ? 'Unlimited AI coaching. Full transformation scores. Weekly reviews.'
    : 'Everything in The Forge plus re-interview anytime and priority support.'

  const features = isForge
    ? ['Unlimited AI coach messages', 'Full transformation scores', 'Weekly evolution reviews', 'Reflection insights', 'Goal history and archive']
    : ['Everything in The Forge', 'Re-interview anytime', 'Behavioral fingerprinting', 'Priority task generation', 'Priority support']

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="max-w-md w-full"
      >
        {/* Success indicator */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="w-16 h-16 rounded-full border border-[#009e97]/30 bg-[#009e97]/10 flex items-center justify-center mx-auto mb-6"
          >
            <span className="text-[#009e97] text-2xl">✓</span>
          </motion.div>

          <h1 className="text-2xl font-semibold text-[#1A1A1A] mb-2">
            Welcome to {planName}
          </h1>
          <p className="text-[#C8C7C5] text-sm leading-relaxed">{planDesc}</p>
        </div>

        {/* Plan card */}
        <div className="border border-[#009e97]/20 bg-[#F8F8F7] rounded-2xl p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <p className="text-xs text-[#C8C7C5] uppercase tracking-widest">Your plan</p>
            <span className="text-xs px-2.5 py-1 rounded-full bg-[#009e97]/10 border border-[#009e97]/20 text-[#009e97] font-medium">
              Active
            </span>
          </div>

          <ul className="space-y-3">
            {features.map((f) => (
              <li key={f} className="flex items-start gap-2.5 text-sm">
                <span className="text-[#009e97] mt-0.5 shrink-0">✓</span>
                <span className="text-[#9E9D9B]">{f}</span>
              </li>
            ))}
          </ul>

          {subscription?.current_period_end && (
            <p className="mt-5 pt-4 border-t border-black/5 text-xs text-[#C8C7C5]">
              Renews {new Date(subscription.current_period_end * 1000).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}
            </p>
          )}
        </div>

        {/* Identity framing */}
        <p className="text-center text-[#C8C7C5] text-xs italic mb-6">
          The version of you that finishes this just made a decision.
        </p>

        {/* CTAs */}
        <div className="flex flex-col gap-3">
          <Link
            href="/dashboard"
            className="w-full py-3.5 rounded-xl bg-[#009e97] text-[#FFFFFF] font-semibold text-sm text-center hover:bg-[#00827c] transition-all hover:scale-[1.01] active:scale-[0.99]"
          >
            Go to dashboard →
          </Link>
          <Link
            href="/settings/subscription"
            className="w-full py-3.5 rounded-xl border border-black/8 text-[#9E9D9B] text-sm text-center hover:border-black/20 hover:text-[#7A7974] transition-all"
          >
            Manage subscription
          </Link>
        </div>
      </motion.div>
    </div>
  )
}

export default function SuccessPage() {
  return (
    <Suspense fallback={<SuccessLoading />}>
      <SuccessContent />
    </Suspense>
  )
}