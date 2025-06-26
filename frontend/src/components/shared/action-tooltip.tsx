import { Tooltip } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import ConfirmIcon from "#/assets/confirm";
import RejectIcon from "#/assets/reject";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { ActionSecurityRisk } from "#/state/security-analyzer-slice";

interface ActionTooltipProps {
  type: "confirm" | "reject";
  onClick: () => void;
}

export function ActionTooltip({ type, onClick }: ActionTooltipProps) {
  const { t } = useTranslation();
  const { logs } = useSelector((state: RootState) => state.securityAnalyzer);

  // Get the most recent log with awaiting_confirmation state
  const pendingLog = logs.find(
    (log) => log.confirmation_state === "awaiting_confirmation",
  );

  // Get risk level text based on the security risk
  const getRiskText = (risk: ActionSecurityRisk) => {
    switch (risk) {
      case ActionSecurityRisk.LOW:
        return t(I18nKey.SECURITY_ANALYZER$LOW_RISK);
      case ActionSecurityRisk.MEDIUM:
        return t(I18nKey.SECURITY_ANALYZER$MEDIUM_RISK);
      case ActionSecurityRisk.HIGH:
        return t(I18nKey.SECURITY_ANALYZER$HIGH_RISK);
      case ActionSecurityRisk.UNKNOWN:
      default:
        return t(I18nKey.SECURITY_ANALYZER$UNKNOWN_RISK);
    }
  };

  // Base content for the tooltip
  let content =
    type === "confirm"
      ? t(I18nKey.CHAT_INTERFACE$USER_CONFIRMED)
      : t(I18nKey.CHAT_INTERFACE$USER_REJECTED);

  // Add risk information to the confirm button tooltip
  if (type === "confirm" && pendingLog) {
    const riskText = getRiskText(pendingLog.security_risk);
    content = `${content} (${riskText})`;
  }

  return (
    <Tooltip content={content} closeDelay={100}>
      <button
        data-testid={`action-${type}-button`}
        type="button"
        aria-label={
          type === "confirm"
            ? t(I18nKey.ACTION$CONFIRM)
            : t(I18nKey.ACTION$REJECT)
        }
        className="bg-tertiary rounded-full p-1 hover:bg-base-secondary"
        onClick={onClick}
      >
        {type === "confirm" ? <ConfirmIcon /> : <RejectIcon />}
      </button>
    </Tooltip>
  );
}
