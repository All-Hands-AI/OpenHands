import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { TooltipButton } from "./tooltip-button";
import UnionIcon from "#/icons/union.svg?react";

interface MicroagentManagementButtonProps {
  disabled?: boolean;
}

export function MicroagentManagementButton({
  disabled = false,
}: MicroagentManagementButtonProps) {
  const { t } = useTranslation();

  const microagentManagement = t(I18nKey.MICROAGENT_MANAGEMENT$TITLE);

  return (
    <TooltipButton
      tooltip={microagentManagement}
      ariaLabel={microagentManagement}
      navLinkTo="/microagent-management"
      testId="microagent-management-button"
      disabled={disabled}
    >
      <UnionIcon />
    </TooltipButton>
  );
}
