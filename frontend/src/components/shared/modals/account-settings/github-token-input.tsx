import { useTranslation } from "react-i18next";
import { FaCheckCircle } from "react-icons/fa";
import { I18nKey } from "#/i18n/declaration";

interface GitHubTokenInputProps {
  githubTokenIsSet: boolean;
}

export function GitHubTokenInput({ githubTokenIsSet }: GitHubTokenInputProps) {
  const { t } = useTranslation();

  return (
    <label htmlFor="ghToken" className="flex flex-col gap-2">
      <span className="text-[11px] leading-4 tracking-[0.5px] font-[500] text-[#A3A3A3] flex items-center gap-1">
        {githubTokenIsSet && (
          <FaCheckCircle
            data-testid="github-token-set-checkmark"
            size={12}
            className="text-[#00D1B2]"
          />
        )}
        {t(I18nKey.GITHUB$TOKEN_LABEL)}
        <span className="text-[#A3A3A3]">
          {" "}
          {t(I18nKey.CUSTOM_INPUT$OPTIONAL_LABEL)}
        </span>
      </span>
      {!githubTokenIsSet && (
        <input
          data-testid="github-token-input"
          id="ghToken"
          name="ghToken"
          type="password"
          className="bg-[#27272A] text-xs py-[10px] px-3 rounded"
        />
      )}
    </label>
  );
}
