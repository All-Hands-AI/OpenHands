import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import PlusIcon from "#/icons/plus.svg?react";
import { TooltipButton } from "./tooltip-button";

export function NewProjectButton() {
  const { t } = useTranslation();
  const startNewProject = t(I18nKey.CONVERSATION$START_NEW);
  return (
    <TooltipButton
      tooltip={startNewProject}
      ariaLabel={startNewProject}
      navLinkTo="/"
      testId="new-project-button"
    >
      <PlusIcon width={28} height={28} />
    </TooltipButton>
  );
}
