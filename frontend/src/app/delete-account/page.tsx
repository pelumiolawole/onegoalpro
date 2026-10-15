import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Delete your account | OneGoal Pro',
  description: 'How to request deletion of your OneGoal Pro account and data.',
}

export default function DeleteAccountPage() {
  return (
    <div className="min-h-screen bg-[#0A0908] text-[#C4BBB5]">

      {/* Nav */}
      <nav className="border-b border-white/5 px-6 py-4 flex items-center justify-between max-w-4xl mx-auto">
        <a href="/" className="font-display text-[#F5F1ED] text-lg">OneGoal Pro</a>
        <a href="/" className="text-[#5C524A] text-sm hover:text-[#C4BBB5] transition-colors">← Back</a>
      </nav>

      <div className="max-w-3xl mx-auto px-6 py-16 pb-24">

        {/* Header */}
        <div className="mb-12">
          <p className="text-[#F59E0B] text-xs uppercase tracking-widest font-mono mb-4">Your data</p>
          <h1 className="font-display text-4xl text-[#F5F1ED] mb-4">Delete your OneGoal Pro account</h1>
          <p className="text-[#7A6E65]">OneGoal Pro is provided by One Goal Pro Ltd.</p>
        </div>

        <div className="space-y-10 text-[15px] leading-relaxed">

          <section>
            <h2 className="text-[#E8E2DC] font-medium text-lg mb-3">How to request deletion</h2>
            <div className="space-y-4 text-[#7A6E65]">
              <div className="border-l border-white/10 pl-4">
                <p className="text-[#C4BBB5] font-medium mb-1">In the app or on the website</p>
                <p>
                  Sign in, open Settings, and choose &quot;Delete account&quot; at the bottom of the page. Type
                  DELETE to confirm. Any paid subscription is cancelled straight away and you are signed out.
                </p>
              </div>
              <div className="border-l border-white/10 pl-4">
                <p className="text-[#C4BBB5] font-medium mb-1">By email</p>
                <p>
                  If you can&apos;t sign in, email{' '}
                  <a href="mailto:support@onegoalpro.app?subject=Delete%20my%20account" className="text-[#F59E0B] hover:underline">support@onegoalpro.app</a>{' '}
                  from the email address registered to your account, with the subject line &quot;Delete my
                  account&quot;. You don&apos;t need to install the app. We will delete your account and confirm
                  by email within 30 days of your request.
                </p>
              </div>
              <p>Either way, your data is permanently deleted within 30 days, and deletion cannot be undone.</p>
            </div>
          </section>

          <section>
            <h2 className="text-[#E8E2DC] font-medium text-lg mb-3">What we delete</h2>
            <div className="space-y-2 text-[#7A6E65]">
              <p>Your account and the personal data linked to it:</p>
              <p>— Account details: your name, email address, sign-in method (including a linked Google account) and profile photo</p>
              <p>— Your Discovery Interview answers, goal, identity traits and daily tasks</p>
              <p>— Your reflections, task history and progress scores</p>
              <p>— Your conversations with the AI coach</p>
              <p>— Push notification subscriptions</p>
              <p>— Analytics records linked to your account</p>
              <p className="pt-2">
                If you have a paid subscription, we cancel it so you are not charged again.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-[#E8E2DC] font-medium text-lg mb-3">What we keep, and for how long</h2>
            <div className="space-y-4 text-[#7A6E65]">
              <div className="border-l border-white/10 pl-4">
                <p className="text-[#C4BBB5] font-medium mb-1">Payment records</p>
                <p>
                  If you paid for a subscription, records of those payments are kept by Stripe, our payment
                  processor, for as long as UK tax law requires us to keep them. This is generally 6 years.
                </p>
              </div>
              <div className="border-l border-white/10 pl-4">
                <p className="text-[#C4BBB5] font-medium mb-1">Backups</p>
                <p>
                  Copies of deleted data can remain in our database provider&apos;s backups until those backups
                  expire on their normal schedule.
                </p>
              </div>
            </div>
          </section>

          <section className="border-t border-white/5 pt-8">
            <p className="text-[#5C524A] text-sm">
              For more on how we handle your data, read our <a href="/privacy" className="text-[#F59E0B] hover:underline">privacy policy</a>.
            </p>
          </section>

        </div>
      </div>
    </div>
  )
}
