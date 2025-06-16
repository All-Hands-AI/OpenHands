import React from "react";
import { useTranslation } from "react-i18next";
import { Spinner } from "@heroui/react";
import { MicroagentStatus } from "#/types/microagent-status";
import { SuccessIndicator } from "../success-indicator";

interface MicroagentStatusIndicatorProps {
  status: MicroagentStatus;
}

export function MicroagentStatusIndicator({
  status,
}: MicroagentStatusIndicatorProps) {
  const { t } = useTranslation();

  const getStatusText = () => {
    switch (status) {
      case MicroagentStatus.CREATING:
        return t("MICROAGENT$STATUS_CREATING");
      case MicroagentStatus.RUNNING:
        return t("MICROAGENT$STATUS_RUNNING");
      case MicroagentStatus.COMPLETED:
        return t("MICROAGENT$STATUS_COMPLETED");
      case MicroagentStatus.ERROR:
        return t("MICROAGENT$STATUS_ERROR");
      default:
        return "";
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case MicroagentStatus.CREATING:
      case MicroagentStatus.RUNNING:
        return <Spinner size="sm" />;
      case MicroagentStatus.COMPLETED:
        return <SuccessIndicator status="success" />;
      case MicroagentStatus.ERROR:
        return <SuccessIndicator status="error" />;
      default:
        return null;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case MicroagentStatus.CREATING:
      case MicroagentStatus.RUNNING:
        return "text-blue-600";
      case MicroagentStatus.COMPLETED:
        return "text-green-600";
      case MicroagentStatus.ERROR:
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  return (
    <div className="flex items-center gap-2 mt-2 p-2 bg-gray-50 rounded-md text-sm">
      {getStatusIcon()}
      <span className={`font-medium ${getStatusColor()}`}>
        {getStatusText()}
      </span>
    </div>
  );
}
