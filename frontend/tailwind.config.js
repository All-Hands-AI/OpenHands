/** @type {import('tailwindcss').Config} */
const { nextui } = require("@nextui-org/react");

export default {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@nextui-org/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      backgroundColor: {
        'user-message': {
          light: '#e6f7ff',
          dark: '#1a3a4a'
        },
        'assistant-message': {
          light: '#f0f5ea',
          dark: '#1e3a2e'
        },
      },
      textColor: {
        'user-message': {
          light: '#003366',
          dark: '#b3d9ff'
        },
        'assistant-message': {
          light: '#2e5c1f',
          dark: '#c1e1c1'
        },
      },
    },
  },
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
            background: "#f0f4f8",
            foreground: "#333c4d",
            primary: {
              DEFAULT: "#3b82f6",
              foreground: "#ffffff",
            },
            secondary: {
              DEFAULT: "#377cfb",
              foreground: "#FFFFFF",
            },
            accent: {
              DEFAULT: "#f68067",
              foreground: "#000000",
            },
            neutral: {
              DEFAULT: "#333c4d",
              foreground: "#f9fafb",
            },
            "bg-dark": "#e2e8f0",
            "bg-light": "#f0f4f8",
            "bg-input": "#ffffff",
            "bg-workspace": "#e2e8f0",
            border: "#cbd5e1",
            "border-editor-sidebar": "#cbd5e1",
            "text-editor-base": "#4a5568",
            "text-editor-active": "#1a202c",
            "bg-editor-sidebar": "#f1f5f9",
            "bg-editor-active": "#e2e8f0",
            "bg-neutral-muted": "rgba(51, 60, 77, 0.05)",
            'user-message-bg': '#e6f7ff',
            'user-message-text': '#003366',
            'assistant-message-bg': '#f0f5ea',
            'assistant-message-text': '#2e5c1f',
            "color-scheme": "light",
            "primary": "#3b82f6",
            "primary-dark": "#2980b9",
            "secondary": "#377cfb",
            "accent": "#f68067",
            "neutral": "#333c4d",
            "base-100": "#f0f4f8",
            "info": "#3498db",
            "success": "#2ecc71",
            "warning": "#f39c12",
            "error": "#e74c3c",
            "error-dark": "#c0392b",
          },
        },
        dark: {
          colors: {
            background: "#1a1a1a",
            foreground: "#ECEDEE",
            primary: {
              DEFAULT: "#1C4E80",
              foreground: "#FFFFFF",
            },
            secondary: {
              DEFAULT: "#7C909A",
              foreground: "#FFFFFF",
            },
            accent: {
              DEFAULT: "#EA6947",
              foreground: "#FFFFFF",
            },
            neutral: "#23282E",
            "bg-dark": "#1a1a1a",
            "bg-light": "#2a2a2a",
            "bg-input": "#2a2a2a",
            "bg-workspace": "#1a1a1a",
            border: "#4a4a4a",
            "text-editor-base": "#ECEDEE",
            "text-editor-active": "#FFFFFF",
            "bg-editor-sidebar": "#2a2a2a",
            "bg-editor-active": "#3b82f6",
            "border-editor-sidebar": "#4a4a4a",
            "bg-neutral-muted": "rgba(42, 42, 42, 0.6)",
            'user-message-bg': '#1C4E80',
            'user-message-text': '#ECEDEE',
            'assistant-message-bg': '#2a2a2a',
            'assistant-message-text': '#ECEDEE',
            "color-scheme": "dark",
            "primary": "#1C4E80",
            "primary-dark": "#2980b9",
            "secondary": "#7C909A",
            "accent": "#EA6947",
            "neutral": "#23282E",
            "base-100": "#202020",
            "info": "#0091D5",
            "success": "#6BB187",
            "warning": "#DBAE59",
            "error": "#AC3E31",
            "error-dark": "#c0392b",
          },
        },
      },
    }),
    require('@tailwindcss/typography'),
  ],
  theme: {
    extend: {
      borderRadius: {
        'box': '0.25rem',
        'btn': '0.125rem',
        'badge': '0.125rem',
      },
    },
  },
};
