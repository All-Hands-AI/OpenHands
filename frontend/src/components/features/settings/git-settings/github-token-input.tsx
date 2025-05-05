import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "../settings-input";
import { GitHubTokenHelpAnchor } from "./github-token-help-anchor";
import { KeyStatusIcon } from "../key-status-icon";

interface GitHubTokenInputProps {
  onChange: (value: string) => void;
  onGitHubHostChange: (value: string) => void;
  isGitHubTokenSet: boolean;
  name: string;
  githubHostSet: string | null | undefined;
  isSaas: boolean;
}

export function GitHubTokenInput({
  onChange,
  onGitHubHostChange,
  isGitHubTokenSet,
  name,
  githubHostSet,
  isSaas,
}: GitHubTokenInputProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-6">
      {!isSaas && (
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
      )}

      <SettingsInput
        onChange={onGitHubHostChange || (() => {})}
        label="GitHub Host"
        type="text"
        className="w-[680px]"
        placeholder="github.com"
        defaultValue={githubHostSet || undefined}
      />

      {!isSaas && <GitHubTokenHelpAnchor />}
    </div>
  );
}
