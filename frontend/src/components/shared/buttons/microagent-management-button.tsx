import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { UnifiedButton } from "#/ui/unified-button/unified-button";
import RobotIcon from "#/icons/robot.svg?react";

interface MicroagentManagementButtonProps {
  disabled?: boolean;
}

export function MicroagentManagementButton({
  disabled = false,
}: MicroagentManagementButtonProps) {
  const { t } = useTranslation();

  const microagentManagement = t(I18nKey.MICROAGENT_MANAGEMENT$TITLE);

  return (
    <UnifiedButton
      as="NavLink"
      to="/microagent-management"
      withTooltip
      tooltipContent={microagentManagement}
      ariaLabel={microagentManagement}
      testId="microagent-management-button"
      disabled={disabled}
      tooltipProps={{
        placement: "right",
      }}
      className="bg-transparent hover:bg-transparent"
    >
      <RobotIcon width={28} height={28} />
    </UnifiedButton>
  );
}
