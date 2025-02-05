import { Tooltip } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import ConfirmIcon from "#/assets/confirm";
import RejectIcon from "#/assets/reject";
import { I18nKey } from "#/i18n/declaration";

interface ActionTooltipProps {
  type: "confirm" | "reject";
  onClick: () => void;
}

export function ActionTooltip({ type, onClick }: ActionTooltipProps) {
  const { t } = useTranslation();

  const content =
    type === "confirm"
      ? t(I18nKey.CHAT_INTERFACE$USER_CONFIRMED)
      : t(I18nKey.CHAT_INTERFACE$USER_REJECTED);

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
        className="bg-neutral-700 rounded-full p-1 hover:bg-neutral-800"
        onClick={onClick}
      >
        {type === "confirm" ? <ConfirmIcon /> : <RejectIcon />}
      </button>
    </Tooltip>
  );
}
