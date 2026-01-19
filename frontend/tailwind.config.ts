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
    },
  },
  plugins: [],
}
export default config
