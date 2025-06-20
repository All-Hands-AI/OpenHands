import React from "react";
import { useTheme } from "#/context/theme-context";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";

interface ThemeToggleProps {
  testId?: string;
  name?: string;
}

export function ThemeToggle({ testId = "theme-toggle", name = "theme-toggle" }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <SettingsSwitch
      testId={testId}
      name={name}
      defaultIsToggled={theme === "light"}
      onToggle={toggleTheme}
    >
      {theme === "dark" ? "Light Theme" : "Dark Theme"}
    </SettingsSwitch>
  );
}
