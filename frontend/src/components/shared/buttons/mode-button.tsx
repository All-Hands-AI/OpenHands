import LightModeIcon from "#/icons/light-mode.svg?react";
import DarkModeIcon from "#/icons/dark-mode.svg?react";
import { TooltipButton } from "./tooltip-button";
import { useTheme } from "#/components/layout/theme-provider";
import { cn } from "#/utils/utils";

export function ModeButton() {
  const { theme, setTheme } = useTheme();

  return (
    <TooltipButton
      tooltip="Mode"
      ariaLabel="Mode"
      className="p-2 rounded-lg text-neutral-800 hover:bg-neutral-1000 hover:text-neutral-100 transition-colors"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
    >
      {theme === "light" ? <LightModeIcon /> : <DarkModeIcon />}
    </TooltipButton>
  );
}
