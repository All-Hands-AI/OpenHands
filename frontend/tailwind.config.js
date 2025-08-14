/** @type {import('tailwindcss').Config} */
import { heroui } from "@heroui/react";
import typography from "@tailwindcss/typography";
export default {
  theme: {
    extend: {
      colors: {
        primary: "#C9B974", // brand gold
        logo: "#CFB755",
        accent: "#00E5FF", // neon cyan accent
        glow: "#7DE69B", // soft green glow used in chat
        base: "#0D0F11",
        "base-secondary": "#24272E",
        danger: "#E76A5E",
        success: "#A5E75E",
        basic: "#9099AC",
        tertiary: "#454545",
        "tertiary-light": "#B7BDC2",
        content: "#ECEDEE",
        "content-2": "#F9FBFE",
      },
      boxShadow: {
        "glow-gold": "0 0 8px #CFB755, 0 0 24px #CFB75566",
        "glow-accent": "0 0 10px #00E5FF, 0 0 28px #00E5FF55",
        "inner-soft": "inset 0 1px 2px rgba(255,255,255,0.06), inset 0 -1px 2px rgba(0,0,0,0.3)",
      },
      dropShadow: {
        neon: ["0 0 6px #00E5FF88", "0 0 14px #00E5FF44"],
        gold: ["0 0 6px #CFB75588", "0 0 14px #CFB75544"],
      },
      ringColor: {
        glow: "#00E5FF",
        gold: "#CFB755",
      },
    },
  },
  darkMode: "class",
  plugins: [typography],
};
