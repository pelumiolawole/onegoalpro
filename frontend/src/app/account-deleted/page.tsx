import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Account deleted | OneGoal Pro',
  robots: { index: false },
}

export default function AccountDeletedPage() {
  return (
    <div className="min-h-screen bg-[#0A0908] text-[#C4BBB5] flex items-center justify-center px-6">
      <div className="max-w-md text-center">
        <h1 className="font-display text-3xl text-[#F5F1ED] mb-4">Your account has been deleted</h1>
        <div className="space-y-3 text-[#7A6E65] text-[15px] leading-relaxed mb-8">
          <p>You&apos;ve been signed out. Any paid subscription has been cancelled, so you won&apos;t be charged again.</p>
          <p>Your data will be permanently deleted within 30 days.</p>
          <p>
            Questions? Email{' '}
            <a href="mailto:support@onegoalpro.app" className="text-[#F59E0B] hover:underline">support@onegoalpro.app</a>.
          </p>
        </div>
        <a href="/" className="text-[#5C524A] text-sm hover:text-[#C4BBB5] transition-colors">Go to the home page</a>
      </div>
    </div>
  )
}
