'use client'

import { useState, Suspense } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Loader2, Sparkles, Shield, Check, ArrowLeft } from 'lucide-react'
import { api } from '@/lib/api'
import { trackEvent } from '@/lib/posthog'

const plans = {
  forge: {
    name: 'The Forge',
    price: { monthly: 4.99, annual: 47.88 },
    annualMonthly: '3.99',
    annualNote: 'Billed as $47.88/year',
    tagline: 'For people who are serious.',
    cta: 'Go deeper',
    features: [
      'Coach PO with full memory — unlimited',
      'Weekly review every Monday',
      'Full transformation score breakdown',
      'Reflection insights',
      'Goal history and archive',
    ],
    color: 'text-[#009e97]',
    border: 'border-[#009e97]/20',
    activeBorder: 'border-[#009e97]',
    bg: 'bg-[#009e97]/8',
    saveBadge: 'Save 20%',
    icon: Sparkles,
  },
  identity: {
    name: 'The Identity',
    price: { monthly: 10.99, annual: 107.88 },
    annualMonthly: '8.99',
    annualNote: 'Billed as $107.88/year',
    tagline: 'For people committed to becoming.',
    cta: 'Commit fully',
    features: [
      'Everything in The Forge',
      'Re-interview when your goal evolves',
      'Behavioural pattern summary',
      'Priority task generation',
      'Early feature access',
      'Priority support',
    ],
    color: 'text-[#009e97]',
    border: 'border-[#009e97]/20',
    activeBorder: 'border-[#009e97]',
    bg: 'bg-[#009e97]/8',
    saveBadge: 'Save 18%',
    icon: Shield,
  },
}

function UpgradeContent() {
  const router = useRouter()
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly')
  const [loadingPlan, setLoadingPlan] = useState<'forge' | 'identity' | null>(null)
  const [error, setError] = useState('')

  const handleCheckout = async (plan: 'forge' | 'identity') => {
    setLoadingPlan(plan)
    setError('')
    trackEvent('upgrade_initiated', { plan, billing_cycle: billingCycle })
    try {
      const response = await api.billing.createCheckout({
        plan,
        billing_cycle: billingCycle,
      })
      window.location.href = response.url
    } catch (err: any) {
      setError(err.detail || 'Failed to start checkout. Try again.')
      setLoadingPlan(null)
    }
  }

  return (
    <div className="min-h-screen bg-[#FFFFFF]">
      <div className="max-w-3xl mx-auto px-6 py-12">

        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-[#C8C7C5] hover:text-[#5C5B57] mb-10 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Settings
        </button>

        <div className="mb-10">
          <h1 className="font-display text-3xl text-[#1A1A1A] mb-2">Upgrade your plan</h1>
          <p className="text-[#9E9D9B]">Choose the level of commitment that matches where you are.</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-950/40 border border-red-900/30 rounded-xl text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Billing toggle */}
        <div className="flex items-center gap-1 p-1 bg-[#F8F8F7] border border-black/5 rounded-xl w-fit mb-8">
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
              billingCycle === 'monthly'
                ? 'bg-[#009e97] text-[#FFFFFF]'
                : 'text-[#C8C7C5] hover:text-[#5C5B57]'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingCycle('annual')}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
              billingCycle === 'annual'
                ? 'bg-[#009e97] text-[#FFFFFF]'
                : 'text-[#C8C7C5] hover:text-[#5C5B57]'
            }`}
          >
            Annual
            <span className={`text-xs px-1.5 py-0.5 rounded-full ${
              billingCycle === 'annual'
                ? 'bg-[#FFFFFF]/20 text-[#FFFFFF]'
                : 'bg-[#009e97]/15 text-[#009e97]'
            }`}>
              Save up to 20%
            </span>
          </button>
        </div>

        {/* Plan cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(Object.entries(plans) as [keyof typeof plans, typeof plans.forge][]).map(([key, plan]) => {
            const Icon = plan.icon
            const isLoading = loadingPlan === key
            const price = billingCycle === 'annual' ? plan.annualMonthly : plan.price.monthly

            return (
              <motion.div
                key={key}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: key === 'forge' ? 0 : 0.08 }}
                className="bg-[#F8F8F7] border border-black/5 rounded-2xl p-6 flex flex-col"
              >
                <div className="flex items-start justify-between mb-5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-[#009e97]/10 flex items-center justify-center">
                      <Icon className="w-5 h-5 text-[#009e97]" />
                    </div>
                    <div>
                      <h2 className="text-[#1A1A1A] font-display text-lg">{plan.name}</h2>
                      <p className="text-[#C8C7C5] text-xs">{plan.tagline}</p>
                    </div>
                  </div>
                  {billingCycle === 'annual' && (
                    <span className="text-xs px-2 py-0.5 bg-[#009e97]/15 text-[#009e97] rounded-full shrink-0">
                      {plan.saveBadge}
                    </span>
                  )}
                </div>

                {/* Price */}
                <div className="mb-6">
                  <div className="flex items-end gap-1">
                    <span className="text-3xl font-display text-[#1A1A1A]">${price}</span>
                    <span className="text-[#C8C7C5] text-sm mb-1">/mo</span>
                  </div>
                  {billingCycle === 'annual' && (
                    <p className="text-[#C8C7C5] text-xs mt-1">{plan.annualNote}</p>
                  )}
                </div>

                {/* Features */}
                <div className="space-y-2.5 mb-8 flex-1">
                  {plan.features.map((feature, i) => (
                    <div key={i} className="flex items-start gap-2.5">
                      <div className="w-4 h-4 rounded-full bg-green-950/40 flex items-center justify-center shrink-0 mt-0.5">
                        <Check className="w-2.5 h-2.5 text-green-400" />
                      </div>
                      <span className="text-[#7A7974] text-sm leading-snug">{feature}</span>
                    </div>
                  ))}
                </div>

                {/* CTA */}
                <button
                  onClick={() => handleCheckout(key)}
                  disabled={loadingPlan !== null}
                  className="w-full py-3 bg-[#009e97] text-[#FFFFFF] font-medium rounded-xl hover:bg-[#33c4be] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Redirecting...
                    </>
                  ) : (
                    plan.cta
                  )}
                </button>
              </motion.div>
            )
          })}
        </div>

        <p className="text-center text-[#C8C7C5] text-xs mt-6">
          14-day money-back guarantee. No questions asked.
        </p>
      </div>
    </div>
  )
}

function UpgradeLoading() {
  return (
    <div className="min-h-screen bg-[#FFFFFF] flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-[#009e97] animate-spin" />
    </div>
  )
}

export default function UpgradePage() {
  return (
    <Suspense fallback={<UpgradeLoading />}>
      <UpgradeContent />
    </Suspense>
  )
}