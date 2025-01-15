import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SetBadge } from "#/components/features/set-status/set-badge";
import { UnsetButton } from "#/components/features/set-status/unset-button";

interface GitHubTokenInputProps {
  isSet: boolean;
  onUnset: () => void;
}

export function GitHubTokenInput({ isSet, onUnset }: GitHubTokenInputProps) {
  const { t } = useTranslation();

  return (
    <label
      data-testid="github-token"
      htmlFor="ghToken"
      className="flex flex-col gap-2"
    >
      <div className="flex items-center gap-1">
        <SetBadge isSet={isSet} />
        <span className="text-[11px] leading-4 tracking-[0.5px] font-[500] text-[#A3A3A3]">
          {t(I18nKey.GITHUB$TOKEN_LABEL)}
          <span className="text-[#A3A3A3]">
            {" "}
            {t(I18nKey.CUSTOM_INPUT$OPTIONAL_LABEL)}
          </span>
        </span>
        {isSet && (
          <UnsetButton testId="unset-github-token-button" onUnset={onUnset} />
        )}
      </div>
      {!isSet && (
        <input
          data-testid="github-token-input"
          id="ghToken"
          name="ghToken"
          type="password"
          placeholder="Enter your GitHub token here"
          className="bg-[#27272A] text-xs py-[10px] px-3 rounded"
        />
      )}
    </label>
  );
}
