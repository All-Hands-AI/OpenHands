import { useLocation } from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { UnifiedButton } from "#/ui/unified-button/unified-button";
import PlusIcon from "#/icons/u-plus.svg?react";

interface NewProjectButtonProps {
  disabled?: boolean;
}

export function NewProjectButton({ disabled = false }: NewProjectButtonProps) {
  const { pathname } = useLocation();

  const { t } = useTranslation();

  const startNewProject = t(I18nKey.CONVERSATION$START_NEW);

  return (
    <UnifiedButton
      as="NavLink"
      to="/"
      withTooltip
      tooltipContent={startNewProject}
      ariaLabel={startNewProject}
      testId="new-project-button"
      disabled={disabled}
      tooltipProps={{
        placement: "right",
      }}
      className="bg-transparent hover:bg-transparent"
    >
      <PlusIcon
        width={24}
        height={24}
        color={pathname === "/" ? "#ffffff" : "#B1B9D3"}
      />
    </UnifiedButton>
  );
}
