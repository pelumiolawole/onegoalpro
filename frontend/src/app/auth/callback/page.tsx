'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/lib/api'

export default function AuthCallbackPage() {
  const router = useRouter()
  const setAuth = useAuthStore(s => s.setAuth)
  const [error, setError] = useState('')

  useEffect(() => {
    async function handleCallback() {
      try {
        // Supabase puts the session in the URL hash after OAuth
        // Parse it out
        const hash = window.location.hash.substring(1)
        const params = new URLSearchParams(hash)
        const accessToken = params.get('access_token')
        const providerToken = params.get('provider_token')

        if (!accessToken) {
          // Try query params (some providers use these)
          const searchParams = new URLSearchParams(window.location.search)
          const code = searchParams.get('code')
          if (!code) {
            setError('No authentication token received. Please try again.')
            return
          }
        }

        // Exchange the Supabase token with our backend
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone

        const data = await api.auth.oauthCallback({
          supabase_token: accessToken || '',
          timezone,
        })

        setAuth(data)

        // Route based on onboarding step
        const step = data.user.onboarding_step
        if (step === 0 || step === 1) router.replace('/interview')
        else if (step === 2) router.replace('/goal-setup')
        else if (step === 3) router.replace('/preview')
        else if (step === 4) router.replace('/activate')
        else router.replace('/dashboard')

      } catch (err: any) {
        console.error('OAuth callback error:', err)
        setError(err.detail || 'Authentication failed. Please try again.')
      }
    }

    handleCallback()
  }, [])

  if (error) {
    return (
      <div className="min-h-screen bg-[#0A0908] flex items-center justify-center p-8">
        <div className="text-center max-w-sm">
          <p className="text-[#F87171] mb-4">{error}</p>
          <button
            onClick={() => window.location.href = '/login'}
            className="text-[#F59E0B] hover:text-[#FCD34D] text-sm"
          >
            Back to login
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0A0908] flex items-center justify-center">
      <div className="text-center">
        <div className="w-10 h-10 border-2 border-[#F59E0B] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-[#7A6E65] text-sm">Completing sign in...</p>
      </div>
    </div>
  )
}