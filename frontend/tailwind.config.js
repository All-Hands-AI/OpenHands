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
        primary: "#C9B974", // nice yellow
        logo: "#CFB755", // color for logos and icons
        // Theme-aware colors using CSS custom properties
        base: "var(--color-base)",
        "base-secondary": "var(--color-base-secondary)",
        "base-tertiary": "var(--color-base-tertiary)",
        "base-primary": "var(--color-base-primary)",
        danger: "#E76A5E",
        success: "#A5E75E",
        basic: "#9099AC", // light gray
        tertiary: "var(--color-tertiary)",
        "tertiary-light": "var(--color-tertiary-light)",
        "tertiary-alt": "var(--color-tertiary-light)",
        content: "var(--color-content)",
        "content-secondary": "var(--color-content-secondary)",
        "content-2": "var(--color-content-2)",
        border: "var(--color-border)",
        "border-hover": "var(--color-border-hover)",
        input: "var(--color-input)",
        // Neutral colors for theme-aware usage
        "neutral-600": "var(--color-neutral-600)",
        "neutral-700": "var(--color-neutral-700)",
        "neutral-800": "var(--color-neutral-800)",
        // Gray colors for theme-aware usage
        "gray-100": "var(--color-gray-100)",
        "gray-200": "var(--color-gray-200)",
        "gray-300": "var(--color-gray-300)",
        "gray-400": "var(--color-gray-400)",
        "gray-500": "var(--color-gray-500)",
        "gray-600": "var(--color-gray-600)",
        "gray-700": "var(--color-gray-700)",
        "gray-800": "var(--color-gray-800)",
        "gray-900": "var(--color-gray-900)",
        // White and black
        white: "var(--color-white)",
        black: "var(--color-black)",
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
            logo: "#CFB755",
          },
        },
        light: {
          colors: {
            primary: "#C9B974",
            logo: "#000000", // Black logo for light theme
          },
        },
      },
    }),
    typography,
  ],
};
