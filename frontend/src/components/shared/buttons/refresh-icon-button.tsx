import { IoIosRefresh } from "react-icons/io";
import { useTranslation } from "react-i18next";
import { IconButton } from "./icon-button";
import { I18nKey } from "#/i18n/declaration";

interface RefreshIconButtonProps {
  onClick: () => void;
}

export function RefreshIconButton({ onClick }: RefreshIconButtonProps) {
  const { t } = useTranslation();

  return (
    <IconButton
      icon={
        <IoIosRefresh
          size={16}
          className="text-neutral-400 hover:text-neutral-100 transition"
        />
      }
      testId="refresh"
      ariaLabel={t("BUTTON$REFRESH" as I18nKey)}
      onClick={onClick}
    />
  );
}
