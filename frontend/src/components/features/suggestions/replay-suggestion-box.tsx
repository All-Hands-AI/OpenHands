import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SuggestionBox } from "./suggestion-box";

interface ReplaySuggestionBoxProps {
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export function ReplaySuggestionBox({ onChange }: ReplaySuggestionBoxProps) {
  const { t } = useTranslation();
  return (
    <SuggestionBox
      title={t(I18nKey.LANDING$REPLAY)}
      content={
        <label
          htmlFor="import-trajectory"
          className="w-full flex justify-center"
        >
          <span className="border-2 border-dashed border-neutral-600 rounded-sm px-2 py-1 cursor-pointer">
            {t(I18nKey.LANDING$UPLOAD_TRAJECTORY)}
          </span>
          <input
            hidden
            type="file"
            accept="application/json"
            id="import-trajectory"
            multiple={false}
            onChange={onChange}
          />
        </label>
      }
    />
  );
}
