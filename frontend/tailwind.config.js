/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        // Display: Playfair Display — editorial, authoritative
        display: ['var(--font-display)', 'Georgia', 'serif'],
        // Body: DM Sans — clean, readable, warm
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        // Mono: for scores and numbers
        mono: ['var(--font-mono)', 'monospace'],
      },
      colors: {
        // Core palette — deep night / warm ink
        ink: {
          950: '#0A0908',
          900: '#141210',
          800: '#1E1B18',
          700: '#2A2520',
          600: '#3D3630',
          500: '#5C524A',
          400: '#7A6E65',
          300: '#A09690',
          200: '#C4BBB5',
          100: '#E8E2DC',
          50:  '#F5F1ED',
        },
        // Accent — warm amber / gold (extended for landing)
        gold: {
          950: '#1a150f',
          900: '#5c421b',
          800: '#70501e',
          700: '#8a6420',
          600: '#a67a24',
          500: '#c99a2e',
          400: '#dcb04d',
          300: '#e8c97a',
          200: '#f2e0b0',
          100: '#f9f0d8',
          50:  '#fdf9f0',
        },
        // Signal colors
        rise:  '#4ADE80',
        hold:  '#94A3B8',
        fall:  '#F87171',
        // Semantic
        success: '#22C55E',
        warning: '#EAB308',
        danger:  '#EF4444',
        // Landing-specific aliases
        void: {
          DEFAULT: '#0A0908',
          light: '#0d0b08',
          dark: '#050403',
          center: '#1a150f',
        },
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '88': '22rem',
        '100': '25rem',
        '112': '28rem',
        '128': '32rem',
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },
      boxShadow: {
        'warm-sm': '0 1px 3px rgba(10,9,8,0.3), 0 1px 2px rgba(10,9,8,0.2)',
        'warm':    '0 4px 16px rgba(10,9,8,0.25), 0 2px 6px rgba(10,9,8,0.15)',
        'warm-lg': '0 12px 40px rgba(10,9,8,0.35), 0 4px 16px rgba(10,9,8,0.2)',
        'warm-xl': '0 24px 64px rgba(10,9,8,0.45), 0 8px 24px rgba(10,9,8,0.25)',
        'glow-gold': '0 0 24px rgba(245,158,11,0.3), 0 0 8px rgba(245,158,11,0.15)',
        'inner-warm': 'inset 0 2px 8px rgba(10,9,8,0.2)',
        // Landing-specific glow
        'gold-lg': '0 0 40px rgba(201, 154, 46, 0.25), 0 0 80px rgba(201, 154, 46, 0.1)',
      },
      animation: {
        'fade-up':     'fadeUp 0.5s ease-out both',
        'fade-in':     'fadeIn 0.4s ease-out both',
        'slide-right': 'slideRight 0.4s ease-out both',
        'pulse-slow':  'pulse 3s ease-in-out infinite',
        'shimmer':     'shimmer 2s linear infinite',
        'breathe':     'breathe 4s ease-in-out infinite',
        // Landing-specific
        'breathe-landing': 'breatheLanding 4s ease-in-out infinite',
        'fade-in-landing': 'fadeInLanding 1.5s ease-out forwards',
        'bounce-subtle':   'bounceSubtle 2s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideRight: {
          '0%':   { opacity: '0', transform: 'translateX(-12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        breathe: {
          '0%, 100%': { opacity: '0.7', transform: 'scale(1)' },
          '50%':      { opacity: '1',   transform: 'scale(1.02)' },
        },
        // Landing-specific keyframes
        breatheLanding: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.8' },
          '50%': { transform: 'scale(1.05)', opacity: '1' },
        },
        fadeInLanding: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
      },
      backgroundImage: {
        'grain': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg '%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E\")",
        'gradient-warm': 'linear-gradient(135deg, #0A0908 0%, #1E1B18 50%, #141210 100%)',
        'gradient-gold': 'linear-gradient(135deg, #B45309 0%, #F59E0B 50%, #D97706 100%)',
        // Landing-specific gradients
        'gradient-void': 'radial-gradient(ellipse at center, #1a150f 0%, #0a0908 50%, #050403 100%)',
        'gradient-gold-shine': 'linear-gradient(135deg, #e8c97a 0%, #c99a2e 50%, #8a6420 100%)',
      },
    },
  },
  plugins: [],
}