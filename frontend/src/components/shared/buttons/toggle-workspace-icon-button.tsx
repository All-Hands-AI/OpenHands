import { IoIosArrowForward, IoIosArrowBack } from "react-icons/io";
import { useTranslation } from "react-i18next";
import { IconButton } from "./icon-button";
import { I18nKey } from "#/i18n/declaration";

interface ToggleWorkspaceIconButtonProps {
  onClick: () => void;
  isHidden: boolean;
}

export function ToggleWorkspaceIconButton({
  onClick,
  isHidden,
}: ToggleWorkspaceIconButtonProps) {
  const { t } = useTranslation();

  return (
    <IconButton
      icon={
        isHidden ? (
          <IoIosArrowForward
            size={20}
            className="text-neutral-400 hover:text-neutral-100 transition"
          />
        ) : (
          <IoIosArrowBack
            size={20}
            className="text-neutral-400 hover:text-neutral-100 transition"
          />
        )
      }
      testId="toggle"
      ariaLabel={
        isHidden ? t(I18nKey.WORKSPACE$OPEN) : t(I18nKey.WORKSPACE$CLOSE)
      }
      onClick={onClick}
    />
  );
}
