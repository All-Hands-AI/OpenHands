/** @type {import('tailwindcss').Config} */
import { heroui } from "@heroui/react";
import typography from '@tailwindcss/typography';
export default {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@heroui/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    animation: {
      enter: "toastIn 400ms cubic-bezier(0.21, 1.02, 0.73, 1)",
      leave: "toastOut 100ms ease-in forwards"
    },
    keyframes: {
      toastIn: {
        "0%": {
          opacity: "0",
          transform: "translateY(-100%) scale(0.8)"
        },
        "80%": {
          opacity: "1",
          transform: "translateY(0) scale(1.02)"
        },
        "100%": {
          opacity: "1",
          transform: "translateY(0) scale(1)"
        }
      },
      toastOut: {
        "0%": {
          opacity: "1",
          transform: "translateY(0) scale(1)"
        },
        "100%": {
          opacity: "0",
          transform: "translateY(-100%) scale(0.9)"
        }
      },
      colors: {
        'root-primary': '#171717',
        'root-secondary': '#262626',
        'hyperlink': '#007AFF',
        'danger': '#EF3744',
        'success': '#4CAF50',
      },
    },
  },
  darkMode: "class",
  plugins: [
    heroui({
      defaultTheme: "dark",
      layout: {
        radius: {
          small: "5px",
          large: "20px",
        },
      },
      themes: {
        dark: {
          colors: {
            primary: "#4465DB",
          },
        }
      }
    }),
    typography,
  ],
};
