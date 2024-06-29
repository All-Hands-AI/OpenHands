// Theme-related utils
export const THEMES = ["light", "dark"] as const;
export type Theme = (typeof THEMES)[number];

export const isValidTheme = (theme: string): theme is Theme =>
  THEMES.includes(theme as Theme);

export const getDefaultTheme = (): Theme => "dark";

export const getThemeMap = (publicUrl: string) => ({
  dark: `${publicUrl}/dark-theme.css`,
  light: `${publicUrl}/light-theme.css`,
});
