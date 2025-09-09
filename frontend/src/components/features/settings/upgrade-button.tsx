import { useTranslation } from "react-i18next";

interface UpgradeButtonProps {
  onClick?: () => void;
  className?: string;
}

export function UpgradeButton({ onClick, className = "" }: UpgradeButtonProps) {
  const { t } = useTranslation();

  return (
    <button
      type="button"
      onClick={onClick}
      className={`bg-neutral-500 box-border content-stretch flex h-4 items-center justify-center mix-blend-multiply overflow-clip p-[8px] relative rounded-[100px] shrink-0 w-16 cursor-pointer hover:opacity-80 ${className}`}
    >
      <div className="box-border content-stretch flex gap-2.5 items-center justify-center min-h-6 px-1 py-0 relative shrink-0">
        <div className="flex flex-col font-medium justify-center leading-[0] not-italic overflow-ellipsis overflow-hidden relative shrink-0 text-[9px] text-nowrap text-white">
          <p className="leading-[20px] overflow-ellipsis overflow-hidden whitespace-pre">
            {t("SETTINGS$UPGRADE_BUTTON")}
          </p>
        </div>
      </div>
    </button>
  );
}
