/** @type {import('tailwindcss').Config} */
import { nextui } from "@nextui-org/react";
import typography from '@tailwindcss/typography';
export default {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@nextui-org/theme/dist/**/*.{js,ts,jsx,tsx}",
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
    nextui({
      defaultTheme: "dark",
      layout: {
        radius: {
          small: "5px",
          large: "20px",
        },
      },
      themes: {
        light: {
          colors: {
            primary: "#4465DB",
            background: "#FFFFFF",
            foreground: "#11181C",
          },
        },
        dark: {
          colors: {
            primary: "#4465DB",
            background: "#171717",
            foreground: "#ECEDEE",
          },
        }
      }
    }),
    typography,
  ],
};
