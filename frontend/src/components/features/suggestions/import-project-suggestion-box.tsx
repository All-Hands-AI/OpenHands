import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SuggestionBox } from "./suggestion-box";

interface ImportProjectSuggestionBoxProps {
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export function ImportProjectSuggestionBox({
  onChange,
}: ImportProjectSuggestionBoxProps) {
  const { t } = useTranslation();
  return (
    <SuggestionBox
      title={t(I18nKey.LANDING$IMPORT_PROJECT)}
      content={
        <label htmlFor="import-project" className="w-full flex justify-center">
          <span className="border-2 border-dashed border-neutral-600 rounded px-2 py-1 cursor-pointer">
            {t(I18nKey.LANDING$UPLOAD_ZIP)}
          </span>
          <input
            hidden
            type="file"
            accept="application/zip"
            id="import-project"
            multiple={false}
            onChange={onChange}
          />
        </label>
      }
    />
  );
}
