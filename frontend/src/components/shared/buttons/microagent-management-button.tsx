import { useTranslation } from "react-i18next";
import { useLocation } from "react-router";
import { I18nKey } from "#/i18n/declaration";
import { Union } from "#/assets/union";
import { TooltipButton } from "./tooltip-button";

interface MicroagentManagementButtonProps {
  disabled?: boolean;
}

export function MicroagentManagementButton({
  disabled = false,
}: MicroagentManagementButtonProps) {
  const { t } = useTranslation();

  const { pathname } = useLocation();

  const microagentManagement = t(I18nKey.MICROAGENT_MANAGEMENT$TITLE);

  return (
    <TooltipButton
      tooltip={microagentManagement}
      ariaLabel={microagentManagement}
      navLinkTo="/microagent-management"
      testId="microagent-management-button"
      disabled={disabled}
    >
      <Union
        width={24}
        height={21}
        active={pathname === "/microagent-management"}
      />
    </TooltipButton>
  );
}
