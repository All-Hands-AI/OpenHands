import toast, { Toast } from "react-hot-toast";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface ErrorToastProps {
  id: Toast["id"];
  error: string;
}

export function ErrorToast({ id, error }: ErrorToastProps) {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-between w-full h-full">
      <span>{error}</span>
      <button
        type="button"
        onClick={() => toast.dismiss(id)}
        className="bg-neutral-500 px-1 rounded-sm h-full"
      >
        {t(I18nKey.ERROR_TOAST$CLOSE_BUTTON_LABEL)}
      </button>
    </div>
  );
}
