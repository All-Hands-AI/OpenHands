/** @type {import('tailwindcss').Config} */
import { heroui } from "@heroui/react";
import typography from '@tailwindcss/typography';
export default {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@heroui/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
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
