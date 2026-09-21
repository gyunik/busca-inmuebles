/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ml: {
          yellow: '#FFE600',
          blue: '#3483FA',
          navy: '#2D3277',
          dark: '#333333',
          gray: '#666666',
          lightgray: '#EBEBEB',
          bg: '#EDEDED'
        }
      }
    },
  },
  plugins: [],
}
