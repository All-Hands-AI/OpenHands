import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface MicroagentManagementAddMicroagentButtonProps {
  onClick: () => void;
}

export function MicroagentManagementAddMicroagentButton({
  onClick,
}: MicroagentManagementAddMicroagentButtonProps) {
  const { t } = useTranslation();

  return (
    <button
      type="button"
      className="text-sm font-normal text-[#8480FF] cursor-pointer outline-none border-none"
      onClick={onClick}
    >
      {t(I18nKey.COMMON$ADD_MICROAGENT)}
    </button>
  );
}
