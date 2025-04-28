import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "../settings-input";
import { GitLabTokenHelpAnchor } from "./gitlab-token-help-anchor";
import { KeyStatusIcon } from "../key-status-icon";

interface GitLabTokenInputProps {
  onChange: (value: string) => void;
  onBaseDomainChange?: (value: string) => void;
  isGitLabTokenSet: boolean;
  name: string;
  baseDomainSet?: string | null;
  isSaas: boolean;
}

export function GitLabTokenInput({
  onChange,
  onBaseDomainChange,
  isGitLabTokenSet,
  name,
  baseDomainSet,
  isSaas,
}: GitLabTokenInputProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-6">
      {!isSaas && (
        <SettingsInput
          testId={name}
          name={name}
          onChange={onChange}
          label={t(I18nKey.GITLAB$TOKEN_LABEL)}
          type="password"
          className="w-[680px]"
          placeholder={isGitLabTokenSet ? "<hidden>" : ""}
          startContent={
            isGitLabTokenSet && (
              <KeyStatusIcon
                testId="gl-set-token-indicator"
                isSet={isGitLabTokenSet}
              />
            )
          }
        />
      )}

      <SettingsInput
        onChange={onBaseDomainChange || (() => {})}
        label={t(I18nKey.GITLAB$BASE_DOMAIN_LABEL)}
        type="text"
        className="w-[680px]"
        placeholder={"gitlab.com"}
        defaultValue={baseDomainSet ? baseDomainSet : undefined}
      />

      {!isSaas && <GitLabTokenHelpAnchor />}
    </div>
  );
}
