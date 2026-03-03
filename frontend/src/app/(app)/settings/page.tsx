'use client'

/**
 * settings/page.tsx
 *
 * Three sections:
 *   1. Profile — avatar upload + who-you're-becoming bio
 *   2. Invite   — share sheet with AI-generated message
 *   3. About   — app info
 *   4. Session  — sign out
 *
 * Data flow:
 *   - On mount: fetches /api/profile for avatar, bio, streak, days active
 *   - Avatar upload: POST /api/profile/avatar (multipart, NOT JSON)
 *   - Bio: POST /api/profile/bio/generate (calls OpenAI, ~2s)
 *   - Share message: POST /api/profile/share-message (calls OpenAI, ~2s)
 */

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/lib/api'
import { useRouter } from 'next/navigation'

interface ProfileData {
  avatar_url: string | null
  bio: string | null
  days_active: number
  current_streak: number
  goal_area: string | null
  display_name: string | null
  email: string
}

export default function SettingsPage() {
  const { user, clearAuth, refreshUser } = useAuthStore()
  const router = useRouter()

  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [profileLoading, setProfileLoading] = useState(true)

  const [avatarUploading, setAvatarUploading] = useState(false)
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [bio, setBio] = useState<string | null>(null)

  const [shareLoading, setShareLoading] = useState(false)
  const [shareMessage, setShareMessage] = useState<string | null>(null)
  const [shareUrl, setShareUrl] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [showSharePanel, setShowSharePanel] = useState(false)

  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)

  useEffect(() => {
    api.profile.get()
      .then(data => {
        setProfile(data)
        setBio(data.bio)
        setAvatarPreview(data.avatar_url)
      })
      .catch(() => {})
      .finally(() => setProfileLoading(false))
  }, [])

  async function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const localUrl = URL.createObjectURL(file)
    setAvatarPreview(localUrl)
    setAvatarUploading(true)
    try {
      const { avatar_url } = await api.profile.uploadAvatar(file)
      setAvatarPreview(avatar_url)
      await refreshUser()
    } catch {
      setAvatarPreview(profile?.avatar_url ?? null)
    } finally {
      setAvatarUploading(false)
    }
  }

  async function handleInvite() {
    setShowSharePanel(true)
    if (shareMessage) return
    setShareLoading(true)
    try {
      const data = await api.profile.generateShareMessage()
      setShareMessage(data.message)
      setShareUrl(data.share_url)
    } catch {
      setShareMessage("I'm using OneGoal Pro to commit to one goal — no excuses. Join me.")
      setShareUrl('https://onegoalpro.vercel.app')
    } finally {
      setShareLoading(false)
    }
  }

  async function handleNativeShare() {
    const text = `${shareMessage}\n\n${shareUrl}`
    if (navigator.share) {
      try { await navigator.share({ text }) } catch {}
    } else {
      handleCopy()
    }
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(`${shareMessage}\n\n${shareUrl}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function handleLogout() {
    clearAuth()
    router.replace('/login')
  }

  const displayName = user?.display_name || profile?.display_name || ''
  const email = user?.email || profile?.email || ''
  const initials = (displayName || email).split(' ').map((w: string) => w[0]).slice(0, 2).join('').toUpperCase() || 'U'

  return (
    <div className="p-6 md:p-8 max-w-2xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <p className="text-[#5C524A] text-sm mb-1">Manage your account</p>
        <h1 className="font-display text-3xl text-[#F5F1ED]">Settings</h1>
      </motion.div>

      <div className="space-y-4">

        {/* ── Profile ── */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="bg-[#111009] border border-white/5 rounded-2xl p-6">
          <p className="text-[#5C524A] text-xs uppercase tracking-widest font-mono mb-5">Profile</p>

          <div className="flex items-center gap-4 mb-6">
            {/* Avatar — click to upload. Hidden input triggered via ref. */}
            <div className="relative w-16 h-16 rounded-2xl cursor-pointer group shrink-0" onClick={() => fileInputRef.current?.click()}>
              {avatarPreview ? (
                <img src={avatarPreview} alt="Avatar" className="w-full h-full rounded-2xl object-cover" />
              ) : (
                <div className="w-full h-full rounded-2xl bg-[#F59E0B]/20 border border-[#F59E0B]/20 flex items-center justify-center">
                  <span className="text-[#F59E0B] text-lg font-semibold">{initials}</span>
                </div>
              )}
              <div className="absolute inset-0 rounded-2xl bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                {avatarUploading ? <Spinner /> : <CameraIcon />}
              </div>
            </div>
            <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={handleAvatarChange} />

            <div>
              <p className="text-[#E8E2DC] text-base font-medium">{displayName || 'No name set'}</p>
              <p className="text-[#5C524A] text-sm">{email}</p>
              <p className="text-[#3D3630] text-xs mt-0.5">Click photo to change</p>
            </div>
          </div>

          {/* Bio */}
          <div className="border-t border-white/5 pt-5">
            <p className="text-[#5C524A] text-xs uppercase tracking-widest font-mono mb-3">Who you're becoming</p>
            {bio
              ? <p className="text-[#C4BBB5] text-sm leading-relaxed italic">{bio}</p>
              : <p className="text-[#3D3630] text-sm">{profileLoading ? 'Writing your identity statement…' : 'Complete a goal to unlock your identity statement.'}</p>
            }
          </div>

          {/* Stats */}
          {!profileLoading && profile && (
            <div className="grid grid-cols-2 gap-3 mt-5 border-t border-white/5 pt-5">
              <div className="bg-[#0A0908] rounded-xl p-3">
                <p className="text-[#3D3630] text-xs font-mono mb-1">Days active</p>
                <p className="text-[#C4BBB5] text-xl font-display">{profile.days_active}</p>
              </div>
              <div className="bg-[#0A0908] rounded-xl p-3">
                <p className="text-[#3D3630] text-xs font-mono mb-1">Current streak</p>
                <p className="text-[#F59E0B] text-xl font-display">{profile.current_streak}d</p>
              </div>
            </div>
          )}

          {/* Account details */}
          <div className="mt-5 border-t border-white/5 pt-3 space-y-0">
            <div className="flex items-center justify-between py-3 border-b border-white/5">
              <p className="text-[#5C524A] text-sm font-mono">Email</p>
              <p className="text-[#C4BBB5] text-sm">{email}</p>
            </div>
            <div className="flex items-center justify-between py-3">
              <p className="text-[#5C524A] text-sm font-mono">Status</p>
              <span className="px-2.5 py-1 bg-[#4ADE80]/10 border border-[#4ADE80]/20 rounded-lg text-[#4ADE80] text-xs font-mono">Active</span>
            </div>
          </div>
        </motion.div>

        {/* ── Invite ── */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-[#111009] border border-white/5 rounded-2xl p-6">
          <p className="text-[#5C524A] text-xs uppercase tracking-widest font-mono mb-2">Invite</p>
          <p className="text-[#5C524A] text-sm mb-5">Share your transformation. Invite someone who needs this.</p>

          <button onClick={handleInvite} className="flex items-center gap-2 px-4 py-2.5 bg-[#F59E0B]/10 border border-[#F59E0B]/20 rounded-xl text-[#F59E0B] text-sm hover:bg-[#F59E0B]/20 transition-all">
            <ShareIcon />
            Invite a friend
          </button>

          <AnimatePresence>
            {showSharePanel && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.25 }} className="overflow-hidden">
                <div className="mt-5 border-t border-white/5 pt-5 space-y-4">
                  <div className="bg-[#0A0908] rounded-xl p-4">
                    {shareLoading
                      ? <div className="flex items-center gap-2 text-[#5C524A] text-sm"><Spinner small />Writing your message...</div>
                      : <p className="text-[#C4BBB5] text-sm leading-relaxed">{shareMessage}</p>
                    }
                  </div>
                  {shareUrl && <p className="text-[#3D3630] text-xs font-mono px-1">{shareUrl}</p>}
                  {!shareLoading && (
                    <div className="flex gap-3 items-center">
                      <button onClick={handleNativeShare} className="flex items-center gap-2 px-4 py-2.5 bg-[#F59E0B] text-[#0A0908] text-sm font-medium rounded-xl hover:bg-[#F59E0B]/90 transition-all">
                        <ShareIcon dark />Share
                      </button>
                      <button onClick={handleCopy} className="flex items-center gap-2 px-4 py-2.5 bg-white/5 border border-white/10 text-[#C4BBB5] text-sm rounded-xl hover:bg-white/10 transition-all">
                        {copied ? <CheckIcon /> : <CopyIcon />}
                        {copied ? 'Copied!' : 'Copy'}
                      </button>
                      <button onClick={() => setShowSharePanel(false)} className="ml-auto text-[#3D3630] hover:text-[#5C524A] text-sm transition-colors">Close</button>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* ── About ── */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="bg-[#111009] border border-white/5 rounded-2xl p-6">
          <p className="text-[#5C524A] text-xs uppercase tracking-widest font-mono mb-5">About</p>
          <div className="space-y-0">
            <div className="flex items-center justify-between py-3 border-b border-white/5">
              <p className="text-[#5C524A] text-sm font-mono">Product</p>
              <p className="text-[#C4BBB5] text-sm">OneGoal Pro</p>
            </div>
            <div className="flex items-center justify-between py-3 border-b border-white/5">
              <p className="text-[#5C524A] text-sm font-mono">Version</p>
              <p className="text-[#3D3630] text-sm font-mono">0.1.0 — MVP</p>
            </div>
            <div className="flex items-center justify-between py-3">
              <p className="text-[#5C524A] text-sm font-mono">Philosophy</p>
              <p className="text-[#C4BBB5] text-sm italic">One goal. Full commitment.</p>
            </div>
          </div>
        </motion.div>

        {/* ── Session ── */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-[#111009] border border-white/5 rounded-2xl p-6">
          <p className="text-[#5C524A] text-xs uppercase tracking-widest font-mono mb-5">Session</p>
          {!showLogoutConfirm ? (
            <button onClick={() => setShowLogoutConfirm(true)} className="flex items-center gap-2 text-[#5C524A] hover:text-red-400 transition-colors text-sm">
              <SignOutIcon />Sign out
            </button>
          ) : (
            <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
              <p className="text-[#C4BBB5] text-sm">You'll be signed out and returned to the login page.</p>
              <div className="flex gap-3">
                <button onClick={handleLogout} className="px-4 py-2 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-xl hover:bg-red-500/20 transition-all">Yes, sign out</button>
                <button onClick={() => setShowLogoutConfirm(false)} className="px-4 py-2 text-[#5C524A] text-sm hover:text-[#C4BBB5] transition-colors">Cancel</button>
              </div>
            </motion.div>
          )}
        </motion.div>

      </div>
    </div>
  )
}

function Spinner({ small }: { small?: boolean }) {
  return <div className={`${small ? 'w-3 h-3' : 'w-4 h-4'} border border-current border-t-transparent rounded-full animate-spin opacity-60`} />
}
function CameraIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
}
function ShareIcon({ dark }: { dark?: boolean }) {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={dark ? '#0A0908' : 'currentColor'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
}
function CopyIcon() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
}
function CheckIcon() {
  return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4ADE80" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
}
function SignOutIcon() {
  return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
}

// Display Current Plan:
// Fetch from GET /api/billing/subscription
const [subscription, setSubscription] = useState(null);

useEffect(() => {
  fetch('/api/billing/subscription')
    .then(r => r.json())
    .then(setSubscription);
}, []);

// Render
<div className="subscription-card">
  <h3>Current Plan: {subscription?.plan}</h3>
  <p>Status: {subscription?.status}</p>
  <p>Renews: {new Date(subscription?.current_period_end).toLocaleDateString()}</p>
  
  {subscription?.status === 'active' && (
    <button onClick={cancelSubscription}>Cancel Subscription</button>
  )}
  
  {subscription?.status === 'canceling' && (
    <button onClick={reactivateSubscription}>Reactivate</button>
  )}
  
  <button onClick={() => window.location.href = '/api/billing/portal'}>
    Manage Billing
  </button>
</div>

// Cancel/Reactivate Functions:
const cancelSubscription = async () => {
  if (!confirm('Cancel at end of billing period?')) return;
  
  const res = await fetch('/api/billing/cancel-subscription', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (res.ok) {
    alert('Subscription will cancel at period end');
    // Refresh subscription data
  }
};