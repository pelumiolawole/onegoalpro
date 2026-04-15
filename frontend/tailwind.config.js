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
        // Core palette — light-mode slate
        slate: {
          950: '#FFFFFF',
          900: '#F8F8F7',
          800: '#F0EFED',
          700: '#E5E4E2',
          600: '#C8C7C5',
          500: '#9E9D9B',
          400: '#7A7974',
          300: '#5C5B57',
          200: '#3D3C39',
          100: '#28271F',
          50:  '#1A1A1A',
        },
        // Accent — teal
        teal: {
          950: '#003d3a',
          900: '#005450',
          800: '#006b66',
          700: '#00827c',
          600: '#009e97',
          500: '#00b5ad',
          400: '#33c4be',
          300: '#66d4cf',
          200: '#99e3e0',
          100: '#ccf1ef',
          50:  '#e6f8f7',
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
          DEFAULT: '#FFFFFF',
          light: '#F8F8F7',
          dark: '#F0EFED',
          center: '#e6f8f7',
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
        'warm-sm': '0 1px 2px rgba(0,0,0,0.05)',
        'warm':    '0 2px 4px rgba(0,0,0,0.08)',
        'warm-lg': '0 4px 12px rgba(0,0,0,0.1)',
        'warm-xl': '0 8px 24px rgba(0,0,0,0.12)',
        'glow-teal': '0 0 15px rgba(0,158,151,0.3), 0 0 30px rgba(0,158,151,0.15)',
        'inner-warm': 'inset 0 2px 8px rgba(0,0,0,0.06)',
        // Landing-specific glow
        'teal-lg': '0 4px 15px rgba(0,158,151,0.25), 0 1px 3px rgba(0,158,151,0.1)',
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
        'gradient-warm': 'linear-gradient(135deg, #FFFFFF 0%, #F0EFED 50%, #F8F8F7 100%)',
        'gradient-teal': 'linear-gradient(135deg, #006b66 0%, #009e97 50%, #00827c 100%)',
        // Landing-specific gradients
        'gradient-void': 'radial-gradient(ellipse at center, #e6f8f7 0%, #FFFFFF 50%, #F0EFED 100%)',
        'gradient-teal-shine': 'linear-gradient(135deg, #66d4cf 0%, #00b5ad 50%, #006b66 100%)',
      },
    },
  },
  plugins: [],
}