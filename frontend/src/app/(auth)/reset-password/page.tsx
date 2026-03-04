'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import OneGoalLogo from '@/components/OneGoalLogo'
import { api } from '@/lib/api'

function ResetPasswordForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!token) {
      setError('Invalid reset link. Please request a new password reset.')
    }
  }, [token])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setLoading(true)

    try {
      await api.auth.resetPassword(token!, password)
      setSuccess(true)
      setTimeout(() => router.push('/login'), 3000)
    } catch (err: any) {
      setError(err.detail || 'Failed to reset password. The link may have expired.')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="text-center">
        <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="font-display text-2xl text-[#F5F1ED] mb-4">Password reset!</h1>
        <p className="text-[#A09690] mb-4">
          Your password has been updated successfully.
        </p>
        <p className="text-[#7A6E65] text-sm">
          Redirecting to login...
        </p>
      </div>
    )
  }

  return (
    <>
      <h1 className="font-display text-3xl text-[#F5F1ED] mb-2">
        Create new password
      </h1>
      <p className="text-[#7A6E65] mb-8">
        Enter a new password for your account.
      </p>

      {error && (
        <div className="mb-6 px-4 py-3 rounded-xl bg-red-950/40 border border-red-900/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-[#A09690] text-sm mb-1.5">New password</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            minLength={8}
            className="input-base"
          />
          <p className="mt-1 text-[#5C524A] text-xs">At least 8 characters</p>
        </div>

        <div>
          <label className="block text-[#A09690] text-sm mb-1.5">Confirm password</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            placeholder="••••••••"
            required
            className="input-base"
          />
        </div>

        <button
          type="submit"
          disabled={loading || !token}
          className="btn btn-primary w-full mt-6 h-12 text-base"
        >
          {loading ? 'Updating...' : 'Reset password'}
        </button>
      </form>
    </>
  )
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen bg-[#0A0908] flex">
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#1a1208] via-[#0A0908] to-[#0A0908]" />
        <div className="relative z-10 flex flex-col justify-center p-16 w-full">
          <OneGoalLogo size={30} textSize="text-2xl" />
          <blockquote className="mt-12 font-display text-2xl text-[#E8E2DC] italic">
            "Your future self is built one decision at a time."
          </blockquote>
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-sm"
        >
          <div className="lg:hidden mb-10">
            <OneGoalLogo size={30} textSize="text-2xl" />
          </div>
          
          <Suspense fallback={
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-2 border-[#F59E0B] border-t-transparent rounded-full mx-auto" />
            </div>
          }>
            <ResetPasswordForm />
          </Suspense>
        </motion.div>
      </div>
    </div>
  )
}