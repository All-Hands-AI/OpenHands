import { IoLockClosed } from "react-icons/io5";
import { Tooltip } from "@heroui/react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";
import { I18nKey } from "#/i18n/declaration";

export function SecurityLock() {
  const { t } = useTranslation();

  return (
    <Tooltip
      content={
        <div className="max-w-xs p-2">
          {t(I18nKey.SETTINGS$CONFIRMATION_MODE_LOCK_TOOLTIP)}
        </div>
      }
      placement="top"
    >
      <Link
        to="/settings"
        className="cursor-pointer hover:opacity-80 transition-all"
        style={{ marginRight: "8px" }}
        aria-label={t(I18nKey.SETTINGS$TITLE)}
      >
        <IoLockClosed size={20} />
      </Link>
    </Tooltip>
  );
}
