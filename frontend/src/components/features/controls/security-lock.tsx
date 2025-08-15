import { IoLockClosed } from "react-icons/io5";
import { Tooltip } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function SecurityLock() {
  const { t } = useTranslation();

  return (
    <Tooltip
      content={t(I18nKey.SETTINGS$CONFIRMATION_MODE_LOCK_TOOLTIP)}
      placement="top"
    >
      <div
        className="cursor-help hover:opacity-80 transition-all"
        style={{ marginRight: "8px" }}
      >
        <IoLockClosed size={20} />
      </div>
    </Tooltip>
  );
}
