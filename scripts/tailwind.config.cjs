/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./src/**/*.{js,jsx,ts,tsx}", "./static/js/**/*.js"],
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        'primary-600': 'var(--color-primary-600)',
        accent: 'var(--color-accent)',
        success: 'var(--color-success)',
        warning: 'var(--color-warning)',
        danger: 'var(--color-danger)',
        neutral: {
          100: 'var(--neutral-100)',
          300: 'var(--neutral-300)',
          600: 'var(--neutral-600)',
          700: 'var(--neutral-700)',
          800: 'var(--neutral-800)',
          900: 'var(--neutral-900)'
        }
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        display: ['var(--font-display)']
      },
      borderRadius: {
        lg: 'var(--radius-lg)'
      }
    }
  },
  plugins: []
}
