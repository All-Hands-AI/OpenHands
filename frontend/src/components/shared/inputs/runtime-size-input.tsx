import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { useAppMode } from "#/hooks/use-app-mode";
import { AppMode } from "#/types/app-mode";

interface RuntimeSizeInputProps {
  isDisabled?: boolean;
  defaultValue?: string;
}

export function RuntimeSizeInput({
  isDisabled,
  defaultValue = "1x",
}: RuntimeSizeInputProps) {
  const { t } = useTranslation();
  const { appMode } = useAppMode();

  if (appMode !== AppMode.SAAS) {
    return null;
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium" htmlFor="runtime-size">
        {t(I18nKey.SETTINGS_FORM$RUNTIME_SIZE_LABEL)}
      </label>
      <select
        id="runtime-size"
        name="runtime-size"
        defaultValue={defaultValue}
        disabled={isDisabled}
        className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500"
      >
        <option value="1x">1x (2 cores, 8GB RAM)</option>
        <option value="2x">2x (4 cores, 16GB RAM)</option>
      </select>
    </div>
  );
}
