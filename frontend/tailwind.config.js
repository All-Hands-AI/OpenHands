/** @type {import('tailwindcss').Config} */
import { heroui } from "@heroui/react";
import typography from "@tailwindcss/typography";
export default {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@heroui/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "var(--green)", // nice yellow
        base: "var(--navy)", // dark background (neutral-900)
        "base-secondary": "var(--navy-dark)", // lighter background (neutral-800); also used for tooltips
        danger: "var(--red)",
        success: "var(--green)",
        tertiary: "var(--navy)", // gray, used for inputs
        "tertiary-light": "red", // lighter gray, used for borders and placeholder text

        "neutral-1100": "var(--navy-extra-extra-dark)",
        "neutral-1000": "var(--navy-extra-dark)",
        "neutral-900": "var(--navy-dark)",
        "neutral-800": "var(--navy-darker)",
        "neutral-700": "var(--navy)", 
        "neutral-600": "var(--navy-a-bit-lighter)",
        "neutral-500": "var(--navy-lighter)",
        "neutral-400": "var(--navy-light)",
        "neutral-300": "var(--navy-extra-light)",

        "red-500": "var(--red)"
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
            primary: "red",
          },
        },
      },
    }),
    typography,
  ],
};
