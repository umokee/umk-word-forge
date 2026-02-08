import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0a0a0a',
          card: '#141414',
          secondary: '#1e1e1e',
          tertiary: '#2a2a2a',
        },
        border: {
          DEFAULT: '#2a2a2a',
          hover: '#3a3a3a',
        },
        text: {
          primary: '#e0e0e0',
          secondary: '#888888',
          tertiary: '#666666',
        },
        accent: {
          DEFAULT: '#00ff88',
          hover: '#00cc6a',
          dim: '#00aa55',
          muted: 'rgba(0, 255, 136, 0.1)',
        },
        success: '#00ff88',
        error: '#ff4444',
        warning: '#ffaa00',
        danger: '#ff4444',
      },
      fontFamily: {
        sans: ['SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Roboto Mono', 'monospace'],
        mono: ['SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Roboto Mono', 'monospace'],
      },
      borderRadius: {
        none: '0',
        sm: '0',
        DEFAULT: '0',
        md: '0',
        lg: '0',
        xl: '0',
        '2xl': '0',
        '3xl': '0',
        full: '0',
      },
      animation: {
        'fade-in': 'fadeIn 150ms ease-out',
        'slide-up': 'slideUp 200ms ease-out',
        'shake': 'shake 300ms ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shake: {
          '0%, 100%': { transform: 'translateX(0)' },
          '25%': { transform: 'translateX(-4px)' },
          '75%': { transform: 'translateX(4px)' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
