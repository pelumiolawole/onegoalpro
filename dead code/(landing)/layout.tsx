import type { Metadata, Viewport } from 'next'
import { Playfair_Display, DM_Sans, DM_Mono } from 'next/font/google'

const playfair = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
})

const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-sans',
  axes: ['opsz'],
  display: 'swap',
})

const dmMono = DM_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  weight: ['400', '500'],
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'One Goal. One Identity. | OneGoal Pro',
  description: 'Most apps track what you do. OneGoal works on who you are. It starts with a real interview, builds a goal around your actual life, and gives you one task every day that moves you toward the person you\'re trying to become.',
  keywords: ['goal setting', 'personal development', 'AI coaching', 'habit building', 'identity-based goals'],
  openGraph: {
    title: 'One Goal. One Identity.',
    description: 'Stop managing tasks. Start becoming.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'One Goal. One Identity.',
    description: 'Stop managing tasks. Start becoming.',
  },
}

export const viewport: Viewport = {
  themeColor: '#0A0908',
}

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="en"
      className={`${playfair.variable} ${dmSans.variable} ${dmMono.variable}`}
    >
      <body className="antialiased overflow-x-hidden">{children}</body>
    </html>
  )
}