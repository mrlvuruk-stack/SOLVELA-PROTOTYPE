/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        sovela: {
          navy: "#0F172A",
          card: "#1E293B",
          border: "#334155",
          teal: "#0EA5E9",
          green: "#10B981",
          amber: "#F59E0B",
          rose: "#F43F5E",
          "text-primary": "#F8FAFC",
          "text-muted": "#94A3B8"
        }
      }
    },
  },
  plugins: [],
};
