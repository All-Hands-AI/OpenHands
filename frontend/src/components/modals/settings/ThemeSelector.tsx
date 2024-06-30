import React from "react";
import { Radio, RadioGroup } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import { Theme, THEMES } from "#/utils/themeUtils";

interface ThemeSelectorProps {
  theme: Theme;
  onThemeChange: (theme: Theme) => void;
  disabled: boolean;
}

function ThemeSelector({
  theme,
  onThemeChange,
  disabled = false,
}: ThemeSelectorProps) {
  const { t } = useTranslation();

  return (
    <div className="mb-4">
      <RadioGroup
        value={theme}
        onValueChange={(value) => onThemeChange(value as Theme)}
        isDisabled={disabled}
        className="text-foreground dark:text-foreground-dark"
      >
        {THEMES.map((themeOption) => (
          <Radio
            key={themeOption}
            value={themeOption}
            className="text-foreground dark:text-foreground-dark"
          >
            {t(`CONFIGURATION$THEME_${themeOption.toUpperCase()}`)}
          </Radio>
        ))}
      </RadioGroup>
    </div>
  );
}

export default ThemeSelector;
