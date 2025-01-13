import { Tooltip } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import ConfirmIcon from "#/assets/confirm";
import RejectIcon from "#/assets/reject";
import { I18nKey } from "#/i18n/declaration";

import type { OverlayPlacement } from "@nextui-org/aria-utils";

interface ActionTooltipProps {
  type?: "confirm" | "reject";
  onClick?: () => void;
  content?: string;
  side?: OverlayPlacement;
  children?: React.ReactNode;
}

export function ActionTooltip({ type, onClick, content, side = "bottom", children }: ActionTooltipProps) {
  const { t } = useTranslation();

  const tooltipContent = type
    ? type === "confirm"
      ? t(I18nKey.CHAT_INTERFACE$USER_CONFIRMED)
      : t(I18nKey.CHAT_INTERFACE$USER_REJECTED)
    : content;

  return (
    <Tooltip content={tooltipContent} closeDelay={100} placement={side}>
      {type ? (
        <button
          data-testid={`action-${type}-button`}
          type="button"
          aria-label={type === "confirm" ? "Confirm action" : "Reject action"}
          className="bg-neutral-700 rounded-full p-1 hover:bg-neutral-800"
          onClick={onClick}
        >
          {type === "confirm" ? <ConfirmIcon /> : <RejectIcon />}
        </button>
      ) : (
        children
      )}
    </Tooltip>
  );
}
