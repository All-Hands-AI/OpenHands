/** @type {import('tailwindcss').Config} */
import { heroui } from "@heroui/react";
import typography from "@tailwindcss/typography";
export default {
  theme: {
    extend: {
      colors: {
        primary: "#C9B974", // nice yellow
        logo: "#CFB755", // color for logos and icons
        base: "#0D0F11", // dark background also used for tooltips
        "base-secondary": "#24272E", // lighter background
        danger: "#E76A5E",
        success: "#A5E75E",
        basic: "#9099AC", // light gray
        tertiary: "#454545", // gray, used for inputs
        "tertiary-light": "#B7BDC2", // lighter gray, used for borders and placeholder text
        content: "#ECEDEE", // light gray, used mostly for text
        "content-2": "#F9FBFE",
      },
    },
  },
  darkMode: "class",
  plugins: [typography],
};
