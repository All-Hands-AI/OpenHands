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
      // ... existing extensions ...
      backgroundColor: {
        'user-message': {
          light: '#e6f7ff', // Light blue for user messages in light mode
          dark: '#1a3a4a'   // Dark blue for user messages in dark mode
        },
        'assistant-message': {
          light: '#f0f5ea', // Light green for assistant messages in light mode
          dark: '#1e3a2e'   // Dark green for assistant messages in dark mode
        },
      },
      textColor: {
        'user-message': {
          light: '#003366', // Dark blue text for user messages in light mode
          dark: '#b3d9ff'   // Light blue text for user messages in dark mode
        },
        'assistant-message': {
          light: '#2e5c1f', // Dark green text for assistant messages in light mode
          dark: '#c1e1c1'   // Light green text for assistant messages in dark mode
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
            background: "#f0f4f8", // Changed from "#FFFFFF" to a light blue-gray
            foreground: "#333c4d", // Kept the same
            primary: {
              DEFAULT: "#66cc8a",
              foreground: "#223D30",
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
            // Adjusting the custom colors
            "bg-dark": "#e2e8f0", // Changed from "#FFFFFF" to a lighter gray
            "bg-light": "#f0f4f8", // Changed to match the new background color
            "bg-input": "#ffffff", // Kept white for input fields
            "bg-workspace": "#e2e8f0", // Changed to a lighter gray
            border: "#a0aec0", // Darker border color for more contrast
            "border-editor-sidebar": "#a0aec0", // Matching the border color
            "text-editor-base": "#4a5568", // Slightly darker for better readability
            "text-editor-active": "#1a202c", // Slightly darker for better contrast
            "bg-editor-sidebar": "#e2e8f0", // Changed to match bg-dark
            "bg-editor-active": "#d1dce8", // Slightly darker than bg-editor-sidebar
            "border-editor-sidebar": "#a0aec0", // Darker border for more contrast
            "bg-neutral-muted": "rgba(51, 60, 77, 0.05)", // Reduced opacity
            'user-message-bg': '#e6f7ff',
            'user-message-text': '#003366',
            'assistant-message-bg': '#f0f5ea',
            'assistant-message-text': '#2e5c1f',
          },
        },
        dark: {
          colors: {
            background: "#202020", // Matches base-100
            foreground: "#ECEDEE", // Kept as is for contrast
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
            "bg-dark": "#202020", // Matches base-100
            "bg-light": "#23282E", // Matches neutral
            "bg-input": "#23282E", // Matches neutral
            "bg-workspace": "#202020", // Matches base-100
            border: "#7C909A", // Matches secondary
            "text-editor-base": "#ECEDEE", // Kept as is for readability
            "text-editor-active": "#FFFFFF",
            "bg-editor-sidebar": "#23282E", // Matches neutral
            "bg-editor-active": "#1C4E80", // Matches primary
            "border-editor-sidebar": "#7C909A", // Matches secondary
            "bg-neutral-muted": "rgba(35, 40, 46, 0.6)", // Based on neutral
            'user-message-bg': '#1C4E80', // Matches primary
            'user-message-text': '#ECEDEE', // Kept as is for readability
            'assistant-message-bg': '#23282E', // Matches neutral
            'assistant-message-text': '#ECEDEE', // Kept as is for readability
            info: "#0091D5",
            success: "#6BB187",
            warning: "#DBAE59",
            error: "#AC3E31",
          },
        },
      },
    }),
    require('@tailwindcss/typography'),
  ],
};
