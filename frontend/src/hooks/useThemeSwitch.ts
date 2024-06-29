import { useState, useEffect } from "react";
import { useThemeSwitcher } from "react-css-theme-switcher";
import {
  Theme,
  isValidTheme,
  getDefaultTheme,
  THEMES,
} from "#/utils/themeUtils";

export const useThemeSwitch = (initialTheme?: Theme) => {
  const { switcher, currentTheme, status } = useThemeSwitcher();
  const [theme, setTheme] = useState<Theme>(() => {
    const savedTheme = localStorage.getItem("theme") as Theme;
    return isValidTheme(savedTheme)
      ? savedTheme
      : initialTheme || getDefaultTheme();
  });

  useEffect(() => {
    localStorage.setItem("theme", theme);
    switcher({ theme });
  }, [theme, switcher]);

  const setValidTheme = (newTheme: string) => {
    if (isValidTheme(newTheme)) {
      setTheme(newTheme);
    } else {
      setTheme(getDefaultTheme());
    }
  };

  return {
    theme,
    setTheme: setValidTheme,
    status,
    currentTheme,
    availableThemes: THEMES,
  };
};
