import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { SettingsInput } from "../settings-input";
import { GitLabTokenHelpAnchor } from "./gitlab-token-help-anchor";

interface GitLabTokenInputProps {
  onChange: (value: string) => void;
  isGitLabTokenSet: boolean;
  name: string;
}

export function GitLabTokenInput({
  onChange,
  isGitLabTokenSet,
  name,
}: GitLabTokenInputProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-6">
      <SettingsInput
        testId={name}
        name={name}
        onChange={onChange}
        label={t(I18nKey.GITLAB$TOKEN_LABEL)}
        type="password"
        className="w-[680px]"
        placeholder={isGitLabTokenSet ? "<hidden>" : ""}
      />

      <GitLabTokenHelpAnchor />
    </div>
  );
}
