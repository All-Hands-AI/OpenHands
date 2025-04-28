import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "../settings-input";
import { GitHubTokenHelpAnchor } from "./github-token-help-anchor";
import { KeyStatusIcon } from "../key-status-icon";

interface GitHubTokenInputProps {
  onChange: (value: string) => void;
  onBaseDomainChange?: (value: string) => void;
  isGitHubTokenSet: boolean;
  name: string;
  baseDomainName?: string;
}

export function GitHubTokenInput({
  onChange,
  onBaseDomainChange,
  isGitHubTokenSet,
  name,
  baseDomainName,
}: GitHubTokenInputProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-6">
      <SettingsInput
        testId={name}
        name={name}
        onChange={onChange}
        label={t(I18nKey.GITHUB$TOKEN_LABEL)}
        type="password"
        className="w-[680px]"
        placeholder={isGitHubTokenSet ? "<hidden>" : ""}
        startContent={
          isGitHubTokenSet && (
            <KeyStatusIcon
              testId="gh-set-token-indicator"
              isSet={isGitHubTokenSet}
            />
          )
        }
      />

      {baseDomainName && (
        <SettingsInput
          testId={baseDomainName}
          name={baseDomainName}
          onChange={onBaseDomainChange || (() => {})}
          label={t(I18nKey.GITHUB$BASE_DOMAIN_LABEL)}
          type="text"
          className="w-[680px]"
          placeholder="github.com"
        />
      )}

      <GitHubTokenHelpAnchor />
    </div>
  );
}
