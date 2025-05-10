import mermaid from "mermaid";

/**
 * Initialize mermaid with default configuration.
 * This should be called once when the application loads.
 */
export function initializeMermaid() {
  mermaid.initialize({
    startOnLoad: false,
    theme: "default",
    securityLevel: "loose", // Adjust based on security requirements
    fontFamily: "monospace",
    flowchart: {
      htmlLabels: true,
      curve: "linear"
    },
    themeVariables: {
      // Theme variables can be customized here to match the application theme
      primaryColor: "#326BF6",
      primaryTextColor: "#fff",
      primaryBorderColor: "#1F4CDF",
      lineColor: "#666",
      secondaryColor: "#F5F5F5",
      tertiaryColor: "#fff"
    }
  });
}

/**
 * Initialize mermaid with dark theme configuration.
 * This can be called when the application switches to dark mode.
 */
export function initializeMermaidDarkTheme() {
  mermaid.initialize({
    startOnLoad: false,
    theme: "dark",
    securityLevel: "loose",
    fontFamily: "monospace",
    flowchart: {
      htmlLabels: true,
      curve: "linear"
    },
    themeVariables: {
      // Dark theme variables
      primaryColor: "#326BF6",
      primaryTextColor: "#fff",
      primaryBorderColor: "#1F4CDF",
      lineColor: "#aaa",
      secondaryColor: "#2a3038",
      tertiaryColor: "#1e1e1e",
      // Additional dark theme colors
      background: "#1e1e1e",
      mainBkg: "#2a3038",
      nodeBorder: "#444",
      clusterBkg: "#2a3038",
      clusterBorder: "#444",
      titleColor: "#fff",
      edgeLabelBackground: "#2a3038"
    }
  });
}