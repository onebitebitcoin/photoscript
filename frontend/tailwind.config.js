/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 다크 테마 커스텀 색상
        dark: {
          bg: '#0f0f1a',
          card: '#1a1a2e',
          border: '#2a2a4a',
          hover: '#252540',
        },
        primary: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
        },
        accent: {
          blue: '#60a5fa',
          green: '#34d399',
          yellow: '#fbbf24',
        }
      },
    },
  },
  plugins: [],
}
