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
        primary: "#FF6100", // nice yellow
        logo: "#E4775D", // color for logos and icons
        base: "#13141D", // dark background also used for tooltips
        "base-secondary": "#1A1C28", // lighter background
        danger: "#E76A5E",
        success: "#A5E75E",
        tertiary: "#454545", // gray, used for inputs
        "tertiary-light": "#B7BDC2", // lighter gray, used for borders and placeholder text
        content: "#ECEDEE", // light gray, used mostly for text
        "content-2": "#F9FBFE",
        "gray-100": "#1E1E1F",
        "gray-200": "#232521",
        "gray-300": "#0F0F0F",
        "gray-400": "#19191A",
        "gray-500": "#171717",
        "sea-stone": {
          900: "#181A17",
        },
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
            logo: "#E4775D",
          },
        },
      },
    }),
    typography,
  ],
};
