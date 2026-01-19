import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        beige: {
          DEFAULT: '#F5F0E6',
          light: '#FAF7F2',
          dark: '#EBE6DC',
          border: '#D4CFC4',
        },
        ink: {
          DEFAULT: '#1A1A1A',
          light: '#2C2C2C',
          muted: '#666666',
        },
      },
      fontFamily: {
        serif: ['Georgia', 'Times New Roman', 'serif'],
        mono: ['IBM Plex Mono', 'Courier New', 'monospace'],
      },
      animation: {
        'progress-bar': 'progress 1.5s ease-in-out infinite',
      },
      keyframes: {
        progress: {
          '0%': { transform: 'translateX(-100%)', width: '40%' },
          '50%': { transform: 'translateX(50%)', width: '60%' },
          '100%': { transform: 'translateX(250%)', width: '40%' },
        },
      },
    },
  },
  plugins: [],
}
export default config
