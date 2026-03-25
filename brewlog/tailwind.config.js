/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        coffee: {
          50: '#FEF9F3',
          100: '#FCF5EC',
          200: '#F5EDE3',
          300: '#E8DDD1',
          400: '#D4CCC0',
          700: '#8C7B6B',
          900: '#6B4226',
          950: '#4A2E18',
        }
      },
      fontFamily: {
        heading: ['var(--font-heading)', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
