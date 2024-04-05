/** @type {import('tailwindcss').Config} */
const { nextui } = require("@nextui-org/react");
export default {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@nextui-org/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "bg-dark": "var(--bg-dark)",
        "bg-light": "var(--bg-light)",
        "bg-input": "var(--bg-input)",
        "bg-workspace": "var(--bg-workspace)",
        border: "var(--border)",
      },
    },
  },
  darkMode: "class",
  plugins: [
    nextui({
      defaultTheme: "dark",
    }),
  ],
};
