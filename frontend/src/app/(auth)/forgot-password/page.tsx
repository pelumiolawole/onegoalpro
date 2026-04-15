'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import OneGoalLogo from '@/components/OneGoalLogo'
import { api } from '@/lib/api'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await api.auth.forgotPassword(email)
      setSubmitted(true)
    } catch (err: any) {
      setError(err.detail || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-[#FFFFFF] flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-sm text-center"
        >
          <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="font-display text-2xl text-[#1A1A1A] mb-4">Check your email</h1>
          <p className="text-[#7A7974] mb-8">
            If an account exists with <span className="text-[#1A1A1A]">{email}</span>, 
            you will receive a password reset link shortly.
          </p>
          <Link 
            href="/login" 
            className="text-[#009e97] hover:text-[#33c4be] transition-colors"
          >
            Back to login
          </Link>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#FFFFFF] flex">
      {/* Left side - same pattern as login */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#e6f8f7] via-[#FFFFFF] to-[#FFFFFF]" />
        <div className="relative z-10 flex flex-col justify-center p-16 w-full">
          <OneGoalLogo size={30} textSize="text-2xl" />
          <blockquote className="mt-12 font-display text-2xl text-[#28271F] italic">
            "Small steps, consistently taken, lead to extraordinary results."
          </blockquote>
        </div>
      </div>

      {/* Right side - form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-sm"
        >
          <div className="lg:hidden mb-10">
            <OneGoalLogo size={30} textSize="text-2xl" />
          </div>

          <h1 className="font-display text-3xl text-[#1A1A1A] mb-2">
            Reset password
          </h1>
          <p className="text-[#9E9D9B] mb-8">
            Enter your email and we'll send you a reset link.
          </p>

          {error && (
            <div className="mb-6 px-4 py-3 rounded-xl bg-red-950/40 border border-red-900/30 text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[#7A7974] text-sm mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="input-base"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary w-full mt-6 h-12 text-base"
            >
              {loading ? 'Sending...' : 'Send reset link'}
            </button>
          </form>

          <p className="mt-6 text-center text-[#C8C7C5] text-sm">
            Remember your password?{' '}
            <Link href="/login" className="text-[#009e97] hover:text-[#33c4be]">
              Sign in
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  )
}