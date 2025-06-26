import { FaClock } from "react-icons/fa";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { Tooltip } from "@heroui/react";
import CheckCircle from "#/icons/check-circle-solid.svg?react";
import XCircle from "#/icons/x-circle-solid.svg?react";
import { ObservationResultStatus } from "./event-content-helpers/get-observation-result";
import { RootState } from "#/store";
import { ActionSecurityRisk } from "#/state/security-analyzer-slice";
import { I18nKey } from "#/i18n/declaration";

interface SuccessIndicatorProps {
  status: ObservationResultStatus;
  eventId?: number; // Optional event ID to match with security logs
}

export function SuccessIndicator({ status, eventId }: SuccessIndicatorProps) {
  const { t } = useTranslation();
  const { logs } = useSelector((state: RootState) => state.securityAnalyzer);

  // Find the security log for this event if eventId is provided
  const securityLog = eventId
    ? logs.find((log) => log.id === eventId)
    : undefined;

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

  // Determine tooltip content based on status and security risk
  const getTooltipContent = () => {
    if (status === "success" && securityLog) {
      return getRiskText(securityLog.security_risk);
    }
    if (status === "success") {
      return t(I18nKey.ACTION$SUCCESS);
    }
    if (status === "error") {
      return t(I18nKey.ACTION$ERROR);
    }
    return t(I18nKey.ACTION$TIMEOUT);
  };

  return (
    <span className="flex-shrink-0">
      {status === "success" && (
        <Tooltip content={getTooltipContent()} closeDelay={100}>
          <CheckCircle
            data-testid="status-icon"
            className="h-4 w-4 ml-2 inline fill-success"
          />
        </Tooltip>
      )}

      {status === "error" && (
        <Tooltip content={getTooltipContent()} closeDelay={100}>
          <XCircle
            data-testid="status-icon"
            className="h-4 w-4 ml-2 inline fill-danger"
          />
        </Tooltip>
      )}

      {status === "timeout" && (
        <Tooltip content={getTooltipContent()} closeDelay={100}>
          <FaClock
            data-testid="status-icon"
            className="h-4 w-4 ml-2 inline fill-yellow-500"
          />
        </Tooltip>
      )}
    </span>
  );
}
