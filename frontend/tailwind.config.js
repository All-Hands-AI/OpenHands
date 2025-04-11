/** @type {import('tailwindcss').Config} */
import { heroui } from "@heroui/react"
import typography from "@tailwindcss/typography"
export default {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@heroui/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        inter: ["Inter", "sans-serif"],
      },
      colors: {
        // primary: "#FF6100", // nice yellow
        // logo: "#E4775D", // color for logos and icons
        primary: "#0070ff", // nice yellow
        logo: "#0070ff88", // color for logos and icons
        base: "#13141D", // dark background also used for tooltips
        "base-secondary": "#1A1C28", // lighter background
        danger: "#E76A5E",
        success: "#A5E75E",
        tertiary: "#454545", // gray, used for inputs
        "tertiary-light": "#B7BDC2", // lighter gray, used for borders and placeholder text
        content: "#ECEDEE", // light gray, used mostly for text
        "content-2": "#F9FBFE",
        gray: {
          100: "#1E1E1F",
          200: "#232521",
          300: "#0F0F0F",
          400: "#19191A",
          500: "#171717",
        },
        neutral: {
          1: "#292929",
          2: "#979995",
        },
        "sea-stone": {
          900: "#181A17",
        },
        neutral: {
          100: "#0F0F0F",
          200: "#141414",
          300: "#1F1F1F",
          400: "#292929",
          500: "#3D3D3D",
          600: "#525252",
          700: "#666",
          800: "#A3A3A3",
          900: "#B8B8B8",
          1000: "#E6E6E6",
          1100: "#F5F5F5",
          1200: "#FFF",
        },
      },
    },
  },
  darkMode: "class",
  plugins: [
    heroui({
      defaultTheme: "light",
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
            logo: "#E4775D",
          },
        },
      },
    }),
    typography,
  ],
}
