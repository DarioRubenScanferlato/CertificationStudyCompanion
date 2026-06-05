/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        databricks: {
          50: "#f0f7ff",
          100: "#e0efff",
          500: "#0066cc",
          600: "#0052a3",
          900: "#001a4d",
        },
      },
      spacing: {
        safe: "env(safe-area-inset-left)",
      },
    },
  },
  plugins: [],
}
