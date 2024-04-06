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
        "text-editor-base": "var(--text-editor-base)",
        "text-editor-active": "var(--text-editor-active)",
        "bg-editor-active": "var(--bg-editor-active)",
        "bg-editor-sidebar": "var(--bg-editor-sidebar)",
        "border-editor-sidebar": "var(--border-editor-sidebar)",
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
