'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuthStore } from '@/stores/auth'
import OneGoalLogo from '@/components/OneGoalLogo'

const STEPS = [
  { label: 'Discovery',  path: '/onboarding/interview' },
  { label: 'Your Goal',  path: '/onboarding/goal' },
  { label: 'Strategy',   path: '/onboarding/preview' },
  { label: 'Activate',   path: '/onboarding/activate' },
]

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, isAuthenticated } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!isAuthenticated) router.replace('/login')
    if (user?.onboarding_step === 5) router.replace('/dashboard')
  }, [isAuthenticated, user])

  const currentStep = Math.max(0, (user?.onboarding_step ?? 1) - 1)

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-6 border-b border-black/5">
        <OneGoalLogo size={26} textSize="text-lg" />

        {/* Step indicators */}
        <div className="hidden sm:flex items-center gap-2">
          {STEPS.map((step, i) => (
            <div key={step.label} className="flex items-center gap-2">
              <div className="flex items-center gap-1.5">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono transition-all duration-300 ${
                    i < currentStep
                      ? 'bg-[#009e97] text-[#FFFFFF]'
                      : i === currentStep
                      ? 'bg-[#009e97]/20 text-[#009e97] border border-[#009e97]/40'
                      : 'bg-[#F0EFED] text-[#C8C7C5] border border-black/5'
                  }`}
                >
                  {i < currentStep ? '✓' : i + 1}
                </div>
                <span
                  className={`text-xs transition-colors ${
                    i <= currentStep ? 'text-[#7A7974]' : 'text-[#C8C7C5]'
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className={`w-8 h-px ${i < currentStep ? 'bg-[#009e97]/40' : 'bg-white/5'}`} />
              )}
            </div>
          ))}
        </div>

        {/* Mobile: step X of Y */}
        <span className="sm:hidden text-[#C8C7C5] text-sm">
          Step {currentStep + 1} of {STEPS.length}
        </span>
      </header>

      {/* Content */}
      <main className="flex-1 flex items-center justify-center p-6">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-2xl"
        >
          {children}
        </motion.div>
      </main>
    </div>
  )
}
